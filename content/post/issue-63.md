---
title: "挖坑：利用memray重构项目，提升内存利用效率"
date: "2022-05-25T08:13:58+08:00"
tags: ['Python']
comments: true
---

> 先甩个成果，项目冷启动内存占用减半，速度提升了2~3倍

```shell
yyyy-mm-dd HH:18:28,729 - [INFO] [MainThread] (server:27) starting remarkable
yyyy-mm-dd HH:18:28,729 - [INFO] [MainThread] (base_handler:54) loading web handlers
yyyy-mm-dd HH:18:29,661 - [INFO] [MainThread] (file_utils:41) PyTorch version 1.4.0 available.
yyyy-mm-dd HH:18:31,789 - [INFO] [MainThread] (base_handler:79) /
yyyy-mm-dd HH:18:31,806 - [INFO] [MainThread] (server:89) Server started...
yyyy-mm-dd HH:18:31,806 - [INFO] [MainThread] (server:90) the web server is listening on http://0.0.0.0:8000


yyyy-mm-dd HH:20:06,448 - [INFO] [MainThread] (server:27) starting remarkable
yyyy-mm-dd HH:20:06,448 - [INFO] [MainThread] (base_handler:54) loading web handlers
yyyy-mm-dd HH:20:06,495 - [INFO] [MainThread] (base_handler:64) loading plugins
yyyy-mm-dd HH:20:07,615 - [INFO] [MainThread] (base_handler:79) /
yyyy-mm-dd HH:20:07,631 - [INFO] [MainThread] (server:89) Server started...
yyyy-mm-dd HH:20:07,631 - [INFO] [MainThread] (server:90) the web server is listening on http://0.0.0.0:8000
```



```
# NOTE: I am not responsible for any expired content.
create@2022-05-25T08:13:58+08:00
update@2022-06-05T00:17:12+08:00
comment@https://github.com/ferstar/blog/issues/63
```
