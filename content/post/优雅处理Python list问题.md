+++
date = "2017-07-19T10:29:00+08:00"
title = "优雅处理Python list问题"
tags = ['PYTHON']

+++

贴一个在[segmentfault](https://segmentfault.com/q/1010000010242056/a-1020000010249040)的回答, 问题是这样的:

有一个`list`, 是有`list`嵌套与`Str`的混合的`list`, 如何能优雅的处理成一个简单的`list`?

```shell
# example:
tmp = ['0-0', ['0-1-0', '0-1-5'], ['0-2-0', '0-2-1', '0-2-2'], ['3-1-0', '3-1-1', '3-1-2', '3-1-3', '3-1-4', '3-1-5'], '4-0', '4-1', '5-0', '5-1']
# to:
des = ['0-0', '0-1-0', '0-1-5', '0-2-0', '0-2-1', '0-2-2', '3-1-0', '3-1-1', '3-1-2', '3-1-3', '3-1-4', '3-1-5', '4-0', '4-1', '5-0', '5-1']
```

有一些要求:

1. 实际问题是很大量的数, 如何**不增加额外list**的情况下处理? (需要内存控制)
2. 维度已知, **二维**
3. 若维度增加, 应该如何处理?

## 别人的实现办法

有人提供了一个`package`可以轻松实现

```python
from compiler.ast import flatten

des = flatten(tmp)
```

## 递归办法

我自己手搓了一个递归也可以搞定, 支持任意维度, 与之前处理过的一个问题类似: [对任意深度任意形式的list嵌套求平均](https://ferstar.org/post/root/dui-ren-yi-shen-du-ren-yi-xing-shi-de-listqian-tao-qiu-ping-jun)

```python
def list_exp(lst):
    _lst = []
    for i in lst:
        if not isinstance(i, list):
            _lst.append(i)
        else:
            _lst += list_exp(i)
    return _lst
```

测试结果

```shell
# 二维
tmp = ['0-0', ['0-1-0', '0-1-5'], ['0-2-0', '0-2-1', '0-2-2'], ['3-1-0', '3-1-1', '3-1-2', '3-1-3', '3-1-4', '3-1-5'], '4-0', '4-1', '5-0', '5-1']
print(lst_ext(tmp))
['0-0', '0-1-0', '0-1-5', '0-2-0', '0-2-1', '0-2-2', '3-1-0', '3-1-1', '3-1-2', '3-1-3', '3-1-4', '3-1-5', '4-0', '4-1', '5-0', '5-1']

# N维
tmp = ['0-0', ['0-1-0', '0-1-5', ['0-1-0', '0-1-5'], ['0-0', ['0-1-0', '0-1-5', ['0-1-0', '0-1-5']]]]]
print(lst_ext(tmp))
['0-0', '0-1-0', '0-1-5', '0-1-0', '0-1-5', '0-0', '0-1-0', '0-1-5', '0-1-0', '0-1-5']
```
## 生成器办法

发现递归还是不可避免的增加了额外的`list`, 而且数据量大了以后, 内存占用似乎也不占优, 所以是时候搬出`generator`大法了.

```python
import collections

# python3
def py3(iterable):
    for el in iterable:
        if not isinstance(el, str) and isinstance(el, collections.Iterable):
            yield from list_exp(el)
        else:
            yield el

# python2
def py2(iterable):
    for el in iterable:
        if not isinstance(el, basestring) and isinstance(el, collections.Iterable):
            for subel in el:
                yield subel
        else:
            yield el
```

果然是一切有`for`的地方都可以上`yield`的节奏~