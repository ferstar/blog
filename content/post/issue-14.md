---
title: "Tornado专题"
date: "2020-01-03T13:10:40+08:00"
tags: ['Python', 'TODO']
comments: false
---

> created_date: 2020-01-03T13:10:40+08:00

> update_date: 2020-02-03T11:33:07+08:00

> comment_url: https://github.com/ferstar/blog/issues/14

##### 1. 断点续传/分片下载

> 抄这里的实现，主要应用场景就是某个接口要提供导出某某静态文件啊什么的，直接把文件绝对路径传给`export`方法即可。

> https://github.com/kzahel/tornado_gen/blob/master/tornado/web.py#L1414

```python
# 你肯定得有个类似`BaseHandler`的类
class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        """此处省略若干自定义初始化过程"""
        pass
    def export(self, abs_path, file_name=None, content_type=None):
        def set_content_length(this, path, req_range):
            size = os.path.getsize(path)
            if req_range:
                start, end = req_range
                if (start is not None and start >= size) or end == 0:
                    # As per RFC 2616 14.35.1, a range is not satisfiable only: if
                    # the first requested byte is equal to or greater than the
                    # content, or when a suffix with length 0 is specified
                    this.set_status(416)  # Range Not Satisfiable
                    this.set_header("Content-Type", "text/plain")
                    this.set_header("Content-Range", "bytes */%s" % (size,))
                    return start, end
                if start is not None and start < 0:
                    start += size
                if end is not None and end > size:
                    # Clients sometimes blindly use a large range to limit their
                    # download size; cap the endpoint at the actual file size.
                    end = size
                # Note: only return HTTP 206 if less than the entire range has been
                # requested. Not only is this semantically correct, but Chrome
                # refuses to play audio if it gets an HTTP 206 in response to
                # ``Range: bytes=0-``.
                if size != (end or size) - (start or 0):
                    this.set_status(206)  # Partial Content
                    # pylint: disable=protected-access
                    this.set_header("Content-Range", httputil._get_content_range(start, end, size))
            else:
                start = end = None

            if start is not None and end is not None:
                length = end - start
            elif end is not None:
                length = end
            elif start is not None:
                length = size - start
            else:
                length = size
            this.set_header("Content-Length", length)
            return start, end

        def get_content_type(path):
            mime_type, encoding = mimetypes.guess_type(path)
            # per RFC 6713, use the appropriate type for a gzip compressed file
            if encoding == "gzip":
                return "application/gzip"
            # As of 2015-07-21 there is no bzip2 encoding defined at
            # http://www.iana.org/assignments/media-types/media-types.xhtml
            # So for that (and any other encoding), use octet-stream.
            elif encoding is not None:
                return "application/octet-stream"
            elif mime_type is not None:
                return mime_type
            # if mime_type not detected, use application/octet-stream
            else:
                return "application/octet-stream"

        def get_content(abspath, start=None, end=None):
            with open(abspath, "rb") as file:
                if start is not None:
                    file.seek(start)
                if end is not None:
                    remaining = end - (start or 0)
                else:
                    remaining = None
                while True:
                    chunk_size = 64 * 1024
                    if remaining is not None and remaining < chunk_size:
                        chunk_size = remaining
                    chunk = file.read(chunk_size)
                    if chunk:
                        if remaining is not None:
                            remaining -= len(chunk)
                        yield chunk
                    else:
                        if remaining is not None:
                            assert remaining == 0
                        return

        if isinstance(abs_path, bytes):
            self.set_header('Content-Type', f'application/{content_type}')
            if file_name:
                file_name = urllib.parse.quote(file_name)
                self.set_header('Content-Disposition', f'attachment; filename={file_name}')
            self.finish(abs_path)

        if not os.path.exists(abs_path):
            raise CustomError(_("File not found"))
        if not file_name:
            file_name = os.path.basename(abs_path)
        file_name = urllib.parse.quote(file_name)
        self.set_header('Content-Disposition', f'attachment; filename={file_name}')
        if not content_type:
            content_type = get_content_type(abs_path)
        self.set_header("Content-Type", content_type)

        self.set_header("Accept-Ranges", "bytes")
        self.set_header("Last-Modified", datetime.datetime.utcfromtimestamp(os.path.getmtime(abs_path)))

        request_range = None
        range_header = self.request.headers.get("Range")
        if range_header:
            # As per RFC 2616 14.16, if an invalid Range header is specified,
            # the request will be treated as if the header didn't exist.
            request_range = httputil._parse_request_range(range_header)  # pylint: disable=protected-access
        start, end = set_content_length(self, abs_path, request_range)

        if self.request.method == 'GET':
            content = get_content(abs_path, start, end)
            if isinstance(content, bytes):
                content = [content]
            for chunk in content:
                try:
                    self.write(chunk)
                except iostream.StreamClosedError:
                    return
        else:
            assert self.request.method == "HEAD"
```

##### 2. CSRF

> [维基传送门](https://en.wikipedia.org/wiki/Cross-site_request_forgery)，这里只说说咋防

其实tornado已经有对应的[实现](https://github.com/tornadoweb/tornado/blob/master/tornado/web.py#L1489)，
大概就是每次请求多带一个预先分发的token，然后用浏览器cookie里的token跟这个做比对

但实际实施过程中总有些接口比如`/login`，都没登录自然拿不到派发的`_xsrf`，所以这个接口不能开`csrf`验证，再比如我们各个微服务间的通讯一般是用基于token的认证方式，这种方式是免疫`csrf`的，自然也不需要验证，基于可能的自定义需求，我们需要重写这个方法`check_xsrf_cookie`

```python
# 你肯定得有个类似`BaseHandler`的类
class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        """此处省略若干自定义初始化过程"""
        pass

    def check_xsrf_cookie(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS") or not get_config('xsrf开关', False):
            return None
        for route_ext in get_config('不检查的路由白名单', []):
            if re.search(rf'不检查的路由', self.request.path):
                logging.debug('Skip xsrf check: %s', self.request.path)
                return None
        # 可能有些系统内接口用的是token认证，那么这些接口也是不需要检查xsrf的，所以也要跳过
        url = self.request.full_url()
        query = urllib.parse.urlparse(url).query
        params = urllib.parse.parse_qs(query) if query else {}
        if all([v for k, v in params.items() if k in ('藏在url里的token key1', '藏在url里的token key2')] or [None]):
            logging.debug('Skip xsrf check: %s', self.request.path)
            return None
        try:
            super(BaseHandler, self).check_xsrf_cookie()
        except tornado.web.HTTPError as exp:
            # 返回一个对前端友好的错误消息提示
            return custom_error(self, exp.status_code, str(exp))
        return None
...

# 你的Application类需要塞进去点参数
class Application(tornado.web.Application):

    def __init__(self):
        ...

        settings = {
            'compiled_template_cache': False,
            'template_path': 'templates',
            'serve_traceback': get_config('要不要开调试', True),
            'xsrf_cookies': get_config('要不要开xsrf验证', False),
            'xsrf_cookie_kwargs': dict(httponly=True),  # _xsrf cookie 加个`httponly`的属性，这样脚本就没办法偷你的cookie了
            "cookie_secret": "a_u_ok?",
        }
        tornado.web.Application.__init__(self, handlers, debug=get_config("要不要开调试", True), **settings)
...
```

接下来告诉前端同学，任何`POST`，`DELETE`，`PUT`请求都带上`_xsrf`参数或者`X-Xsrftoken`请求头或者`X-Csrftoken`请求头，不要问为什么，问就甩[源码](https://github.com/tornadoweb/tornado/blob/master/tornado/web.py#L1513)