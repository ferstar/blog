---
title: "Do not use Super in comprehension if you need cython"
slug: "cython-comprehension-super-bug"
date: "2023-01-24T01:24:35+08:00"
tags: ['Python']
comments: true
---

一般项目交付给客户都会把源码打包一下，通常是下面的姿势：

```shell
# py to c
cython -X language_level=3 -X annotation_typing=False --directive always_allow_keywords=true debug.py
# c to so
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing $(python3-config --includes) -o debug.so debug.c
```

你会发现源码能行的一些写法，编译以后执行就会报莫名其妙的错误，比如：`Super in comprehension`

```python
class A:
    def hi(self):
        return range(10)


class B(A):
    @property
    def wow(self):
        return [i for i in super().hi()]


if __name__ == '__main__':
    print(B().wow)
```

这段代码源码运行没有任何问题，执行`B().wow`输出就是`[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`。但是编译后再运行就会报如下的错：

```shell
Python 3.11.6 (main, Nov 14 2023, 09:36:21) [GCC 13.2.1 20230801] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import debug
>>> debug.B().wow
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "debug.py", line 10, in debug.B.wow
    
RuntimeError: super(): no arguments
```

不用担心，这不是你的问题，而是 cython 一个上古的 bug：https://github.com/cython/cython/issues/1828

那团队协作中如何提示组员避免这种写法呢？我们可以借助 `pylint` 来检查&提示：

```python
from astroid import nodes
from pylint import checkers, interfaces
from pylint.checkers import utils


class SupperInCompChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = "super-in-comprehension"

    msgs = {
        "R9527": (
            "You need to abstract super() to a variable",
            "do-not-use-super-in-comprehension",
            "Use super() in comprehension may cause compatibility issues with cython.",
        ),
    }
    options = ()

    priority = -1

    @utils.only_required_for_messages(
        "do-not-use-super-in-comprehension",
    )
    def visit_comprehension(self, node: nodes.Comprehension) -> None:
        self._check_super_in_comprehension(node)

    def _check_super_in_comprehension(self, node: nodes.Comprehension) -> None:
        if " super(" not in node.as_string():
            return

        self.add_message("do-not-use-super-in-comprehension", node=node)


def register(linter):
    linter.register_checker(SupperInCompChecker(linter))
```

至于这个checker怎么用，卖个关子，有心人自己去找：

https://pylint.pycqa.org/en/latest/development_guide/how_tos/custom_checkers.html

最终的效果大概是：

```shell
You need to abstract super() to a variable,
do not use super in comprehension...
```



```
# NOTE: I am not responsible for any expired content.
create@2023-01-24T01:24:35+08:00
update@2023-12-27T09:08:09+08:00
comment@https://github.com/ferstar/blog/issues/72
```
