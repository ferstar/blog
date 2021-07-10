---
title: "Deal with "RuntimeError: super(): __class__ cell not found" bugs"
date: "2021-07-10T23:11:20+08:00"
tags: ['Python']
comments: true
---

When I use [cython](https://github.com/cython) compile my *.py files to *.so, it looks good and no error occurred. But when I run my project it throw out such error exception: `RuntimeError: super(): __class__ cell not found`(I'm sure I can run the project from the source code without any problems)

...debuging...


After debugging for a few minutes, I found this ancient issue: https://github.com/cython/cython/issues/1127

My goodness, this bug has not been resolved for more than ten years......

Fortunately, I got a simple solution: *roll back the legacy python2 super style*

And here comes the problems:

1. How to roll back the py2 super style in batches? I have so many *.py files...
2. How to warn team members not to use the py3 super style?

...coding...

And here comes the solution:

1. Because I am lazy, I wrote a script to help me do this:

```python
"""Change py3 super style to py2's"""
import re
from pathlib import Path

class_p = re.compile(r'class (?P<class_name>\w+)[\(:]')


def replace(path):
    with open(path, 'r') as read_file:
        reversed_lines = read_file.readlines()[::-1]
    for idx, line in enumerate(reversed_lines[:]):
        if 'super().' in line:
            print(f'{path}:{len(reversed_lines) - idx}')
            cls_str = 'cls' if '__new__' in line else 'self'
            for above_line in reversed_lines[idx:]:
                if '@classmethod' in line:
                    cls_str = 'cls'
                    continue
                match = class_p.search(above_line)
                if match:
                    reversed_lines[idx] = line.replace('super().', f'super({match.group("class_name")}, {cls_str}).')
                    break
    with open(path, 'w') as write_file:
        write_file.writelines(reversed_lines[::-1])


if __name__ == '__main__':
    for file in Path('.').glob('**/*.py'):
        if __file__ != file.as_posix():
            replace(file)
```

2. Like most open source projects, we also use [pylint](http://pylint.pycqa.org/) to check the code style, I copied the template and wrote a custom checker:

```python
"""file: py3_style_checker.py"""
import astroid
from pylint import checkers, interfaces
from pylint.checkers import utils


class PY3StyleSupperChecker(checkers.BaseChecker):

    __implements__ = (interfaces.IAstroidChecker,)

    name = "py3-style-super"

    msgs = {
        "R0711": (
            "Consider using Python 2 style super() within arguments",
            "super-without-arguments",
            "Emitted when calling the super() builtin with the current class "
            "and instance. We need to keep the legacy Python 2 style super to "
            "make the Cython compile correct.",
        ),
    }
    options = ()

    priority = -1

    @utils.check_messages(
        "super-without-arguments",
    )
    def visit_call(self, node):
        self._check_super_without_arguments(node)

    def _check_super_without_arguments(self, node):
        if not isinstance(node.func, astroid.Name) or node.func.name != "super":
            return

        if len(node.args) != 0:
            return

        self.add_message("super-without-arguments", node=node)


def register(linter):
    linter.register_checker(PY3StyleSupperChecker(linter))
```

We need to add the checker's parent directory into current `PYTHONPATH`, and run `pylint` like this:

```shell
$ pylint --load-plugins=py3_style_checker --disable=all --enable=super-without-arguments <path_to_your_py_file>
```

done!

> Ref
> 1. [How to Write a Checker](http://pylint.pycqa.org/en/latest/how_tos/custom_checkers.html)
> 2. [super doesn't work with cpdef methods](https://github.com/cython/cython/issues/1127)



```
# NOTE: I am not responsible for any expired content.
create@2021-07-10T23:11:20+08:00
update@2021-07-10T23:12:19+08:00
comment@https://github.com/ferstar/blog/issues/42
```
