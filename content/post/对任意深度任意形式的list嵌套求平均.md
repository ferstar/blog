---
title: "对任意深度任意形式的list嵌套求平均"
date: "2016-09-07T14:30:00+08:00"
tags: ['PYTHON']
comments: 
---


[水木论坛](http://www.newsmth.net/nForum/#!article/Python/134174)看到的这个问题, 觉得有意思, 就写了下

如`L = [1, [2, [3, 4], 5], 6, [7, 8]]`这个 list
求平均值, 用到了递归

```
def get_avg(L): 
     count=0
     def scantree(L): 
         nonlocal count 
         total = 0
         for x in L: 
             if not isinstance(x, list): 
                 total += x 
                 count += 1
             else: 
                 total += scantree(x) 
         return total 
     return scantree(L) / count 

 L =   [1, [2, [3, 4], 5], 6, [7, 8]]
 print(get_avg(L)) 
```

采用`generator`重写一下上面的代码

```python
import collections


def get_item(iterable):
    for el in iterable:
        if not isinstance(el, str) and isinstance(el, collections.Iterable):
            yield from list_exp(el)
        else:
            yield el
```

测试

```python
L = [1, [2, [3, 4], 5], 6, [7, 8]]
sum, count = 0, 0
for i in get_item(L):
    count += 1
    sum += i
print(sum/count)

# 4.5
```

