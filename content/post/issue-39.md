---
title: "Fix "TypeError: __call__() takes 2 positional arguments but 3 were given""
date: "2021-03-23T01:54:07+08:00"
tags: ['Linux', 'Python']
comments: true
---

用`gunicorn`启动一个`tornado`服务时报了个错:

```shell
[ERROR] [MainThread] (http1connection:67) Uncaught exception
Traceback (most recent call last):
  File "/Users/ferstar/.pyenv/versions/scriber/lib/python3.6/site-packages/tornado/http1connection.py", line 273, in _read_message
    delegate.finish()
  File "/Users/ferstar/.pyenv/versions/scriber/lib/python3.6/site-packages/tornado/httpserver.py", line 280, in finish
    self.request_callback(self.request)
  File "/Users/ferstar/.pyenv/versions/scriber/lib/python3.6/site-packages/tornado/wsgi.py", line 114, in __call__
    WSGIContainer.environ(request), start_response
TypeError: __call__() takes 2 positional arguments but 3 were given
```

调试发现是[这行代码](https://github.com/benoitc/gunicorn/blob/master/gunicorn/workers/gtornado.py#L113)的问题:

```python
        # Assume the app is a WSGI callable if its not an
        # instance of tornado.web.Application or is an
        # instance of tornado.wsgi.WSGIApplication
        app = self.wsgi
        if tornado.version_info[0] < 6:
            if not isinstance(app, tornado.web.Application) or \
            isinstance(app, tornado.wsgi.WSGIApplication):
                app = WSGIContainer(app)
        elif not isinstance(app, WSGIContainer):
            app = WSGIContainer(app)
```

我用的 tornado 版本是`6.1`, 可以看到, `web.Application`被`WSGIContainer`包了一层, 实际上`tornado`自`6.0`以后的版本中有意在剥离`WSGI`的支持, 所以比较苟的一个解决方法是退回到`6.0`之前的版本, 比如`5.1.1`, 即可正常; 然而作为一个有追求的攻城狮, 怎么能够因为一个小小的兼容问题就退版本号呢, 我选择硬肛, 既然`gunicorn`自己的`tornado worker`不能用, 那就照抄另写一个:

```python
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.
# filename: gtornado.py

import copy
import gettext
import logging.config
import os
import sys

from gunicorn.workers.base import Worker
import tornado
import tornado.httpserver
import tornado.web
from tornado.ioloop import IOLoop, PeriodicCallback

class TornadoWorker(Worker):
    def handle_exit(self, sig, frame):
        if self.alive:
            super().handle_exit(sig, frame)

    def handle_request(self):
        self.nr += 1
        if self.alive and self.nr >= self.max_requests:
            self.log.info("Autorestarting worker after current request.")
            self.alive = False

    def watchdog(self):
        if self.alive:
            self.notify()

        if self.ppid != os.getppid():
            self.log.info("Parent changed, shutting down: %s", self)
            self.alive = False

    def heartbeat(self):
        if not self.alive:
            if self.server_alive:
                if hasattr(self, 'server'):
                    try:
                        self.server.stop()
                    except Exception:  # pylint: disable=broad-except
                        pass
                self.server_alive = False
            else:
                for callback in self.callbacks:
                    callback.stop()
                self.ioloop.stop()

    def init_process(self):
        # IOLoop cannot survive a fork or be shared across processes
        # in any way. When multiple processes are being used, each process
        # should create its own IOLoop. We should clear current IOLoop
        # if exists before os.fork.
        IOLoop.clear_current()
        super().init_process()

    def run(self):
        self.ioloop = IOLoop.current()
        self.alive = True
        self.server_alive = False

        self.callbacks = []
        self.callbacks.append(PeriodicCallback(self.watchdog, 1000))
        self.callbacks.append(PeriodicCallback(self.heartbeat, 1000))
        for callback in self.callbacks:
            callback.start()

        # Assume the app is a WSGI callable if its not an
        # instance of tornado.web.Application or is an
        # instance of tornado.wsgi.WSGIApplication
        app = self.wsgi

        # Monkey-patching HTTPConnection.finish to count the
        # number of requests being handled by Tornado. This
        # will help gunicorn shutdown the worker if max_requests
        # is exceeded.
        httpserver = sys.modules["tornado.httpserver"]
        if hasattr(httpserver, 'HTTPConnection'):
            old_connection_finish = httpserver.HTTPConnection.finish

            def finish(other):
                self.handle_request()
                old_connection_finish(other)

            httpserver.HTTPConnection.finish = finish
            sys.modules["tornado.httpserver"] = httpserver

            server_class = tornado.httpserver.HTTPServer
        else:

            class _HTTPServer(tornado.httpserver.HTTPServer):
                def on_close(instance, server_conn):  # pylint: disable=no-self-argument
                    self.handle_request()
                    super(_HTTPServer, instance).on_close(server_conn)

            server_class = _HTTPServer

        app_params = {
            "max_buffer_size": 200 * 1024 * 1024,  # 200MB
            "decompress_request": True,
        }
        if self.cfg.is_ssl:
            _ssl_opt = copy.deepcopy(self.cfg.ssl_options)
            # tornado refuses initialization if ssl_options contains following
            # options
            del _ssl_opt["do_handshake_on_connect"]
            del _ssl_opt["suppress_ragged_eofs"]
            app_params["ssl_options"] = _ssl_opt
        server = server_class(app, **app_params)

        self.server = server
        self.server_alive = True

        for socket in self.sockets:
            socket.setblocking(0)
            server.add_socket(socket)

        server.no_keep_alive = self.cfg.keepalive <= 0
        server.start(num_processes=1)

        self.ioloop.start()
```

主要就是直接丢掉`WSGIContainer`, 使用`tornado.web.Application`, 然后运行:

```shell
gunicorn -k gtornado.TornadoWorker main:app -b 0.0.0.0:8080 --graceful-timeout 120 --timeout 600
```

发送个`HUP`信号看看反应, 嗯, 顺利重载

```shell
[INFO] Starting gunicorn 20.1.0
[INFO] Listening at: http://0.0.0.0:8080 (51702)
[INFO] Using worker: gtornado.TornadoWorker
[INFO] Booting worker with pid: 51756
[INFO] Handling signal: hup  # 收到信号
[INFO] Hang up: Master
[INFO] Booting worker with pid: 52640  # 顺利重载
[INFO] Worker exiting (pid: 51756)
```

附上测试代码:
```python
# filename: main.py
import asyncio
from tornado.web import Application, RequestHandler


class MainHandler(RequestHandler):
    def get(self):
        self.write("Hello, world")


class LongPollHandler(RequestHandler):
    async def get(self):
        lines = ['line 1\n', 'line 2\n']

        for line in lines:
            self.write(line)
            await self.flush()
            await asyncio.sleep(0.5)
        await self.finish()


app = Application([
    (r"/", MainHandler),
    (r"/longpoll", LongPollHandler)
])
```



```
# NOTE: I am not responsible for any expired content.
create@2021-03-23T01:54:07+08:00
update@2021-03-23T01:54:07+08:00
comment@https://github.com/ferstar/blog/issues/39
```
