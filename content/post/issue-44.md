---
title: "Use literal_eval instead of eval"
date: "2021-10-25T01:49:59+08:00"
tags: ['Python', 'Snippet']
comments: true
---

- code
```python
import ast
import operator


def safe_eval(expr):
    """Use `ast.literal_eval` instead of `eval`
    via: https://stackoverflow.com/a/20748308
    """

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.BinOp):
            return valid_ops[type(node.op)](_eval(node.left), _eval(node.right))
        raise TypeError('Unsupported type {}'.format(node))

    return _eval(ast.parse(expr, mode='eval').body)
```
- test
```shell
safe_eval('1 + 2 / 3')
Out[3]: 1.6666666666666665
safe_eval('(1 + 2) / 3')
Out[4]: 1.0
```



```
# NOTE: I am not responsible for any expired content.
create@2021-10-25T01:49:59+08:00
update@2021-10-25T01:49:59+08:00
comment@https://github.com/ferstar/blog/issues/44
```
