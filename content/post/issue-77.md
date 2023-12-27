---
title: "Migrate from Tornado to FastAPI"
date: "2023-06-09T12:32:25+08:00"
tags: ['Python', 'Tornado', 'FastAPI']
comments: true
---

心水 FastAPI 的 ASGI、依赖注入、类型注解和自动在线文档很久，但迫于项目历史依赖（立项的时候 FastAPI 还没出来），迟迟没有迁移的动力。直到某次又翻到过期的接口文档，实在不想继续过文档和代码分割的日子了，于是决定开整。

迫于旧接口太多，一下迁移明显不现实，想了两个过渡方案：

1. Nginx 分流，旧接口继续使用 Tornado 驱动，新接口走 FastAPI
2. 完全抛弃 Tornado 驱动，利用 WSGI 将旧接口分流、转换成 Tornado 兼容的响应

方案一实施起来最简单，但有个问题是 Session 共享不好解决，另外增加了额外的运维部署复杂度，于是pass；

走方案二的话，就需要写一个中间件来将旧接口分流、转换给原 Tornado 的实现，代码如下：

经典的 Tornado hello world

```python
import asyncio
import tornado


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def make_app():
    return tornado.web.Application([
        (r"/api/v1/", MainHandler),
    ])


async def main():
    app = make_app()
    app.listen(8888)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
```

本来是打算手撸 ASGI -> WSGI 的，刚好刷推看到  Django 的 a2wsgi，能省不少手撕 WSGI 协议的活，于是果断抄之，最终成品如下：

```python
import asyncio
import contextvars
import functools
import urllib.parse as urllib_parse
from asyncio import Future
from typing import Any, List, Tuple

import tornado
import uvicorn
from a2wsgi.types import Environ, StartResponse
from a2wsgi.wsgi import Body, WSGIResponder, build_environ
from fastapi import FastAPI
from starlette.types import Receive, Scope, Send
from tornado import httputil
from tornado.escape import native_str
from tornado.web import Application


# WSGI has no facilities for flow control, so just return an already-done
# Future when the interface requires it.
def _dummy_future():
    f = Future()
    f.set_result(None)
    return f


class _WSGIRequestContext:
    def __init__(self, remote_ip, protocol):
        self.remote_ip = remote_ip
        self.protocol = protocol

    def __str__(self):
        return self.remote_ip


class _WSGIConnection(httputil.HTTPConnection):
    def __init__(self, method, start_response, context):
        self.method = method
        self.start_response = start_response
        self.context = context
        self._write_buffer = []
        self._finished = False
        self._expected_content_remaining = None
        self._error = None

    def set_close_callback(self, callback):
        # WSGI has no facility for detecting a closed connection mid-request,
        # so we can simply ignore the callback.
        pass

    def write_headers(self, start_line, headers, chunk=None, callback=None):
        if self.method == "HEAD":
            self._expected_content_remaining = 0
        elif "Content-Length" in headers:
            self._expected_content_remaining = int(headers["Content-Length"])
        else:
            self._expected_content_remaining = None
        self.start_response(
            "%d %s" % (start_line.code, start_line.reason),
            [(native_str(k), native_str(v)) for (k, v) in headers.get_all()],
        )
        if chunk is not None:
            self.write(chunk, callback)
        elif callback is not None:
            callback()
        return _dummy_future()

    def write(self, chunk, callback=None):
        if self._expected_content_remaining is not None:
            self._expected_content_remaining -= len(chunk)
            if self._expected_content_remaining < 0:
                self._error = httputil.HTTPOutputError(
                    "Tried to write more data than Content-Length"
                )
                raise self._error
        self._write_buffer.append(chunk)
        if callback is not None:
            callback()
        return _dummy_future()

    def finish(self):
        if (
            self._expected_content_remaining is not None
            and self._expected_content_remaining != 0
        ):
            self._error = httputil.HTTPOutputError(
                f"Tried to write {self._expected_content_remaining} bytes less than Content-Length"
            )
            raise self._error
        self._finished = True


class WSGIAdapter:
    def __init__(self, app):
        self.app = app

    async def __call__(
        self, environ: Environ, start_response: StartResponse
    ) -> List[bytes]:
        method = environ["REQUEST_METHOD"]
        uri = urllib_parse.quote(environ.get("SCRIPT_NAME", ""))
        uri += urllib_parse.quote(environ.get("PATH_INFO", ""))
        if environ.get("QUERY_STRING"):
            uri += "?" + environ["QUERY_STRING"]
        headers = httputil.HTTPHeaders()
        if environ.get("CONTENT_TYPE"):
            headers["Content-Type"] = environ["CONTENT_TYPE"]
        if environ.get("CONTENT_LENGTH"):
            headers["Content-Length"] = environ["CONTENT_LENGTH"]
        for key in environ:
            if key.startswith("HTTP_"):
                headers[key[5:].replace("_", "-")] = environ[key]
        if headers.get("Content-Length"):
            body = await environ["wsgi.input"].aread(int(headers["Content-Length"]))
        else:
            body = b""
        protocol = environ["wsgi.url_scheme"]
        remote_ip = environ.get("REMOTE_ADDR", "")
        if environ.get("HTTP_HOST"):
            host = environ["HTTP_HOST"]
        else:
            host = environ["SERVER_NAME"]
        connection = _WSGIConnection(
            method, start_response, _WSGIRequestContext(remote_ip, protocol)
        )
        request = httputil.HTTPServerRequest(
            method,
            uri,
            "HTTP/1.1",
            headers=headers,
            body=body,
            host=host,
            connection=connection,
        )
        request._parse_body()
        await self.app(request)
        if connection._error:
            raise connection._error
        if not connection._finished:
            raise Exception("request did not finish synchronously")
        return connection._write_buffer


class TornadoMiddleware:
    def __init__(self, app) -> None:
        self.app = WSGIAdapter(app)
        self.executor = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            responder = _WSGIResponder(self.app, self.executor)
            return await responder(scope, receive, send)

        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1000})
            return None


class _Body(Body):
    async def _areceive_more_data(self) -> bytes:
        if not self._has_more:
            return b""
        message = await self.receive()
        self._has_more = message.get("more_body", False)
        return message.get("body", b"")

    async def aread(self, size: int = -1) -> bytes:
        while size == -1 or size > len(self.buffer):
            self.buffer.extend(await self._areceive_more_data())
            if not self._has_more:
                break
        if size == -1:
            result = bytes(self.buffer)
            self.buffer.clear()
        else:
            result = bytes(self.buffer[:size])
            del self.buffer[:size]
        return result


class _WSGIResponder(WSGIResponder):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        body = _Body(self.loop, receive)
        environ = build_environ(scope, body)
        sender = None
        try:
            sender = self.loop.create_task(self.sender(send))
            context = contextvars.copy_context()
            func = functools.partial(context.run, self.awsgi)
            await func(environ, self.start_response)
            self.send_queue.append(None)
            self.send_event.set()
            await asyncio.wait_for(sender, None)
            if self.exc_info is not None:
                raise self.exc_info[0].with_traceback(
                    self.exc_info[1], self.exc_info[2]
                )
        finally:
            if sender and not sender.done():
                sender.cancel()  # pragma: no cover

    def start_response(
        self,
        status: str,
        response_headers: List[Tuple[str, str]],
        exc_info: Any = None,
    ) -> None:
        self.exc_info = exc_info
        if not self.response_started:
            self.response_started = True
            status_code_string, _ = status.split(" ", 1)
            status_code = int(status_code_string)
            headers = [
                (name.strip().encode("latin1").lower(), value.strip().encode("latin1"))
                for name, value in response_headers
            ]
            self.send(
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": headers,
                }
            )

    async def awsgi(self, environ: Environ, start_response: StartResponse) -> None:
        for chunk in await self.app(environ, start_response):
            self.send({"type": "http.response.body", "body": chunk, "more_body": True})

        self.send({"type": "http.response.body", "body": b""})


class HandleDelegate(tornado.web._HandlerDelegate):
    def execute(self):
        if not self.application.settings.get("compiled_template_cache", True):
            with tornado.web.RequestHandler._template_loader_lock:
                for loader in tornado.web.RequestHandler._template_loaders.values():
                    loader.reset()
        if not self.application.settings.get("static_hash_cache", True):
            tornado.web.StaticFileHandler.reset()

        self.handler = self.handler_class(
            self.application, self.request, **self.handler_kwargs
        )
        transforms = [t(self.request) for t in self.application.transforms]

        return self.handler._execute(transforms, *self.path_args, **self.path_kwargs)


class TornadoApplication(Application):
    def get_handler_delegate(
        self,
        request,
        target_class,
        target_kwargs=None,
        path_args=None,
        path_kwargs=None,
    ):
        return HandleDelegate(
            self, request, target_class, target_kwargs, path_args, path_kwargs
        )


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def make_app():
    return TornadoApplication([(r"/api/v1/", MainHandler)])


async def main():
    app = make_app()
    app.listen(8888)
    await asyncio.Event().wait()


app = FastAPI()
app.mount("/api/v1", TornadoMiddleware(make_app()))


@app.get("/api/v2/")
def hello_world():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
```

测一下：

```shell
~ curl http://127.0.0.1:8888/api/v2/
{"message":"Hello, World!"}%
~ curl http://127.0.0.1:8888/api/v1/
Hello, world%
```

可以看出 v1 接口请求被 FastAPI 通过中间件机制传给 TornadoMiddleware，再由 TornadoMiddleware 完成 ASGI 到 WSGI 再到 Tornado 接口代码的转换工作，完美解决了旧 Tornado 接口与新 FastAPI 接口共存的问题，且不影响现有项目部署流程，十分nice。



```
# NOTE: I am not responsible for any expired content.
create@2023-06-09T12:32:25+08:00
update@2023-12-27T11:08:32+08:00
comment@https://github.com/ferstar/blog/issues/77
```
