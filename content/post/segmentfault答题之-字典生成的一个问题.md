---
date = "2016-08-19T10:00:00+08:00"
title = "segmentfault答题之-字典生成的一个问题"
tags = ['OTHERS']

---

via <https://segmentfault.com/q/1010000006624056/a-1020000006628560>

一个函数, 作用是按区切割列表
```
def generate_index(n, step=1):
    for i in range(0, n, step):
        yield (i, i + step) if i + step < n else (i, None)
 ```
 简单使用
 `list(generate_index(20, 5))`
 ```
[(0, 5), (5, 10), (10, 15), (15, None)]
``` 