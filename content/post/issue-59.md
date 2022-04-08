---
title: "一个简单计算PDF页数的方法"
date: "2022-04-08T02:51:14+08:00"
tags: ['Python', 'Snippet']
comments: true
---

```python
import re


def count_pages(path):
    count_pages_p = re.compile(rb"/Type\s*/Page([^s]|$)", re.MULTILINE | re.DOTALL)
    with open(path, 'rb') as fp:
        return len(count_pages_p.findall(fp.read()))
```



```
# NOTE: I am not responsible for any expired content.
create@2022-04-08T02:51:14+08:00
update@2022-04-08T02:51:19+08:00
comment@https://github.com/ferstar/blog/issues/59
```
