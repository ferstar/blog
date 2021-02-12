---
title: "Python Understanding Dict Copy Shallow or Deep"
date: 2018-12-01T17:31:03+08:00
tags: ['PYTHON']
comments: true
---

- **直接赋值：**其实就是对象的引用（别名）。
- **浅拷贝(copy)：**拷贝父对象，不会拷贝对象的内部的子对象。
- **深拷贝(deepcopy)：** copy 模块的 deepcopy 方法，完全拷贝了父对象及其子对象。

比较二的拿一个嵌套很多层的`dict`直接赋值, 结果悲剧了, 引发了一系列子对象比如`list`内容各种异常, 使用`deepcopy`后正常

![贴图](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/blog/20181201173603.png)

悲剧就出在`L`不停的被修改...

http://www.runoob.com/w3cnote/python-understanding-dict-copy-shallow-or-deep.html