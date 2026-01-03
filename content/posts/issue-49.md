---
title: "Make use of invoke klass param to simplify our daily CLI task"
slug: "python-invoke-cli-task-automation"
date: "2021-11-13T12:26:24+08:00"
tags: ['Python', 'Snippet', 'Invoke']
comments: true
---

> invoke version: >= 1.1

### Code
```python
# filename=tasks.py
import asyncio
from inspect import isgeneratorfunction, iscoroutinefunction

from invoke import Task
from invoke.tasks import task


class InvokeWrapper(Task):
    def __call__(self, *args, **kwargs):
        io_loop = asyncio.get_event_loop()
        if isgeneratorfunction(self.body):
            result = io_loop.run_until_complete(
                asyncio.coroutine(self.body)(*args, **kwargs)
            )
        elif iscoroutinefunction(self.body):
            result = io_loop.run_until_complete(self.body(*args, **kwargs))
        else:
            result = self.body(*args, **kwargs)
        self.times_called += 1
        return result


@task(klass=InvokeWrapper)
def foo(ctx):
    """sync task"""
    print("foo")


@task(klass=InvokeWrapper)
async def bar(ctx):
    """async/await style async task"""
    await asyncio.sleep(0.1)
    print("bar")


@task(klass=InvokeWrapper)
def baz(ctx):
    """yield from(< py3.6) style async task"""
    yield from asyncio.sleep(0.1)
    print("baz")

```

### Test
```shell
~ inv -l
Available tasks:

  bar   async/await style async task
  baz   yield from(< py3.6) style async task
  foo   sync task

~ inv bar|foo|baz
bar
baz
foo
```



```
# NOTE: I am not responsible for any expired content.
create@2021-11-13T12:26:24+08:00
update@2021-11-13T12:27:13+08:00
comment@https://github.com/ferstar/blog/issues/49
```
