---
title: "Tornado专题"
date: "2020-01-03T13:10:40+08:00"
tags: ['Python', 'TODO']
comments: true
---

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

##### ~~3. 自适应修正可能错误的 Content-Type POST 请求头~~

> ~~后端N久没动的一个接口被产品吐槽出bug了，debug发现原来是前端的锅，原本这个接口要求  Content-Type  得是 multipart/form-data，然而前端某次重构后，这个 Content-Type 变成了 application/json，于是在没有经过充分回归测试的情况下，bug出现了，接口没办法正常拿到正确的参数。~~

~~定位到问题后，解决就很简单了，要么前端抖抖小手把这个header写对，要么后端在接收 POST 请求之前把 header 改对。介于我司小厂，测试不足，所以我还是双保险，后端也对这种情况做一个兼容。~~

```python
class BaseHandler(tornado.web.RequestHandler, SessionMixin):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        # 一系列init方法

    def prepare(self):
        """
        Called at the beginning of a request before  `get`/`post`/etc.
        """
        if self.request.method in ('POST', 'PUT'):
            self.adapt_req_headers()

    def adapt_req_headers(self):
        """根据request body自适应修正Content-Type"""
        form_data_prefix = 'multipart/form-data;'
        content_disp = b'Content-Disposition: form-data;'
        www_form_prefix = 'application/x-www-form-urlencoded'

        def parse_body():
            self.request._parse_body()  # pylint: disable=protected-access
            logging.warning('Content-Type does not match the request body, will correct it')

        if self.request.body:
            if (
                not self.request.headers.get('Content-Type', '').startswith(form_data_prefix)
                and content_disp in self.request.body
            ):
                try:
                    boundary = self.request.body.split(b'\r\n')[0][2:].decode() or 'boundary'
                except UnicodeDecodeError as exp:
                    logging.exception(exp)
                else:
                    self.request.headers.update({'Content-Type': f'{form_data_prefix} boundary="{boundary}"'})
                    parse_body()
                return
            if not self.request.headers.get('Content-Type', '').startswith(www_form_prefix) and all(
                [all(i.partition(b'=')) for i in self.request.body.split(b'&') if content_disp not in i]
                or (False,)
            ):
                self.request.headers.update({'Content-Type': www_form_prefix})
                parse_body()
                return
```

##### 4. 跨域资源共享(CORS) 

> 跨域资源共享(CORS) 是一种机制，它使用额外的HTTP 头来告诉浏览器 让运行在一个origin (domain) 上的Web应用被准许访问来自不同源服务器上的指定的资源。 当一个资源从与该资源本身所在的服务器不同的域、协议或端口请求一个资源时，资源会发起一个跨域HTTP 请求。

> tornado 正确处理 CORS 请求的代码如下

```python
    def set_cors_header(self):
        origin = f'{self.request.headers.get("Origin", "").rstrip("/")}'
        trust_hosts = [...]
        if origin not in trust_hosts:
            logging.warning(f'Untrusted source request detected: {origin}')
            return None
        # NOTE: Can't be set "*" because a valid request always sending with cookies
        # which will be blocked by CORS policy
        self.set_header("Access-Control-Allow-Origin", origin)
        # Must be set as "true"(case sensitive) to allow CORS with cookies
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")
        # Must contain all possible request headers from frontend requests
        self.set_header(
            "Access-Control-Allow-Headers",
            "Accept, Accept-Encoding, Accept-Language, Access-Control-Request-Headers, Access-Control-Request-Method, "
            "Cache-Control, Connection, Content-Type, "
            "Host, Origin, Pragma, Referer, Sec-Fetch-Mode, User-Agent, X-Csrftoken",
        )
```

参考: 

https://fullstackbb.com/http/options-method-and-cors-preflight/

https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Access_control_CORS```
# NOTE: I am not responsible for any expired content.
created_date: 2020-01-03T13:10:40+08:00
update_date: 2021-02-13T03:23:42+08:00
comment_url: https://github.com/ferstar/blog/issues/14
