---
title: "Tornado专题"
date: "2020-01-03T13:10:40+08:00"
tags: ['Python', 'TODO']
comments: false
---

> created_date: 2020-01-03T13:10:40+08:00

> update_date: 2020-01-07T10:46:00+08:00

> comment_url: https://github.com/ferstar/blog/issues/14

##### 1. 断点续传

> 待填坑

https://github.com/kzahel/tornado_gen/blob/master/tornado/web.py#L1509

##### 2. CSRF

> [维基传送门](https://en.wikipedia.org/wiki/Cross-site_request_forgery)，这里只说说咋防

其实tornado已经有对应的[实现](https://github.com/tornadoweb/tornado/blob/master/tornado/web.py#L1489)，
大概就是每次请求多带一个预先分发的token，然后用用浏览器cookie里的token跟这个做比对

但实际实施过程中总有些接口比如`/login`，都没登录自然拿不到派发的`_xsrf`，所以这个接口不能开`csrf`验证，再比如我们各个微服务间的通讯一般是用基于token的认证方式，这种方式是免疫`csrf`的，自然也不需要验证，基于可能的自定义需求，我们需要重写这个方法`check_xsrf_cookie`

```python
# 你肯定得有个类似`BaseHandler`的类
class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        """此处省略若干自定义初始化过程"""
        pass

    def check_xsrf_cookie(self):
        if not get_config('xsrf开关', False):
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

接下来告诉你的前端同学，任何`POST`，`DELETE`，`PUT`请求都带上`_xsrf`参数或者`X-Xsrftoken`请求头或者`X-Csrftoken`请求头，不要问为什么，问就甩[源码](https://github.com/tornadoweb/tornado/blob/master/tornado/web.py#L1513)