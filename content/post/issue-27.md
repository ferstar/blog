---
title: "miniconda的一个坑"
date: "2020-11-28T00:56:32+08:00"
tags: ['Linux', 'Python']
comments: false
---

> created_date: 2020-11-28T00:56:32+08:00

> update_date: 2020-11-28T00:57:46+08:00

> comment_url: https://github.com/ferstar/blog/issues/27

> 这货socket模块没有`SO_REUSEPORT`，着实坑我不少，还是用官方源码编译靠谱，鬼知道类似这种魔改选手又在哪里缺金少两。

有个tornado项目起手式是这样的

```python
app = TornadoApplication()
server = tornado.httpserver.HTTPServer(app)
server.bind(8888, reuse_port=True)
server.start()
tornado.ioloop.IOLoop.current().start()
```

然后赤裸裸报错：
```
the platform doesn't support SO_REUSEPORT
```

找到出错的源码位置

```python
    if reuse_port and not hasattr(socket, "SO_REUSEPORT"):
        raise ValueError("the platform doesn't support SO_REUSEPORT")
```

好吧居然没有`SO_REUSEPORT`属性，我一度以为是自己系统问题，然而并不是，问题出在miniconda的Python包上，换系统内置Python或者官方源码编译的就没有问题。

准备给Conda官方提个issue，发现早有人发现这个问题

https://github.com/conda/conda/issues/9151

一直没人理会的感觉，瞟一眼1.7k+的issues，我还是跟conda拜拜吧，毕竟又不炼丹。

