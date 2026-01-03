---
title: "Tornado热重载机制下使用lru_cache一个隐藏的坑点"
slug: "tornado-lru-cache-reload-bug"
date: "2021-11-09T11:02:12+08:00"
tags: ['Python', 'Tornado']
comments: true
---

> 经常用`lru_cache`来加速一些重复耗时的`func`, 今天栽了个坑: `func`的缓存在服务热重载后并没有被释放掉, 导致重跑这个方法的时候总是返回旧的数据, 放代码解释:

```python
@lru_cache()
def parse_file(path):
    pass
```

`parse_file`接收一个文件路径, 对给定文件做了若干处理, 正常情况是没有问题的, 但是如果文件内容发生了变化, 本例实际上是因为要重跑某些process, 连带着这个文件内容是有更新的, 但是`path`不变, 在热重载的时候, 全局缓存并没有清掉, 导致每次调用方法返回的还是旧缓存数据

关于 Tornado 的热重载, 我在这里有过介绍: [init_process](/post/issue-39)

问题搞清楚, 解决起来就很简单, 重载的时候清一波就完事

- 定义一个清缓存的方法

```python
def clear_caches():
    # All objects cleared
    for obj in (i for i in gc.get_objects() if isinstance(i, functools._lru_cache_wrapper)):
        obj.cache_clear()
    gc.collect()
```

- 热重载前清掉缓存

```python
class TornadoWorker(Worker):
    ......
    def init_process(self):
        # IOLoop cannot survive a fork or be shared across processes
        # in any way. When multiple processes are being used, each process
        # should create its own IOLoop. We should clear current IOLoop
        # if exists before os.fork.
        IOLoop.clear_current()
        clear_caches()
        # You can do something like release db conn/clean fp or else.
        super().init_process()
```

然后, 整个世界清净了~



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2021-11-09T11:02:12+08:00
Updated at: 2025-01-12T20:07:23+08:00
Origin issue: https://github.com/ferstar/blog/issues/48
```
