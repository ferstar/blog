---
title: "利用msgspec加速大json文件反序列化速度"
date: "2022-05-25T08:12:46+08:00"
tags: ['Python']
comments: true
---

> 一个库的命运啊，当然要靠自我奋斗，但是也要考虑到项目的实际需求，有舍才有得。

内部项目有一个基础依赖的结果「下文简述为 origin.json.gz」是`json.dump`然后压缩成`gz`文件存储的，下游引用的时候有个头大的问题就是这玩意太大了，动辄百兆级别，一般的`json.load`就很慢，于是就一直在寻找可用的性能更为优秀的方法来替换掉内置`json`处理，至少期望是`load`快一些。

先后尝试过不同的`json`库，包括不限于以下选手：`orjson/ujson/rapidjson/simplejson`，基本的对比效果就是：序列化各种吊打内置库，但反序列化基本上没啥太大的优势，直到有一天老板甩了个分享链接：[Faster, more memory-efficient Python JSON parsing with msgspec (pythonspeed.com)](https://pythonspeed.com/articles/faster-python-json-parsing/)

发现`msgspec`这玩意简直强的离谱：提前定义好`struct`然后按需`streaming`加载的思路性能极佳且内存极度友好。

简单说明一下这个`origin.json.gz`的大致结构：

```js
[
  {
    "A": ...一堆子子孙孙
    "B": ...二堆子子孙孙
    ...
    "Z": {
      "ZA": ...aaa
      "ZB": ...bbb
      ...
      "ZZ": ...zzz
    }
	},
  ...
]
```

某个下游引用的场景是：需要`origin.json.gz`里的某个节点的部分信息来做一些二次处理的事情。以往的操作不管如何先`load`一把，实在浪费资源。如果用`msgspec`来处理，是这样的姿势：

```python
import gzip
from msgspec.json import decode
from msgspec import Struct


path = '...path...of...origin...json...gz...'

class Z(Struct):
    ZZ: List[dict]

class Item(Struct):
    Z: Dict[str, ZZ]

with gzip.open(path, 'rb') as fp:
    # 可以看到我只需要定义自己关心的节点链路即可，其他用不到的数据完全可以忽略不写
    # 这种读取方式必然是内存友好型了
    data = decode(fp.read(), type=List[Item])

for item in data:
    print(item.Z.ZZ)
```

代码量看起来是比以前一把梭哈`json.load`多了一点，但收益巨大：同样的硬件条件，使用`msgspec.decode`快了近一个数量级。

虽然没有去翻源码去看具体实现，但二进制的世界没有魔法，无非就是在玩时间空间的把戏。`msgspec.decode`的快源于两点：

1. 预定义了数据类型，他的核心解析器可以节省大量不必要的类型判断
2. 按需定义，忽略不必要的数据

这就是一个**空间换时间**的玩法，**按需加载**显著降低了需要处理的数据量，自然性能就上来了。

这时候来了个成年人说我都要行不行？很遗憾，不行。在预定义了所有节点的数据结构「去掉**按需加载**的 buff」以后，`msgspec.decode`的速度甚至比内置`json`还慢 20% （基于一坨 400MB 大小的`origin.json`测试所得），`object`显然要比`dict`慢上一拍的。



```
# NOTE: I am not responsible for any expired content.
create@2022-05-25T08:12:46+08:00
update@2022-06-04T23:12:30+08:00
comment@https://github.com/ferstar/blog/issues/62
```
