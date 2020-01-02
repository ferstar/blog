---
title: "Git常用操作"
date: "2020-01-02T10:51:58+08:00"
tags: ['Git']
comments: false
---

> created_date: 2020-01-02T10:51:58+08:00

> update_date: 2020-01-02T10:55:46+08:00

> comment_url: https://github.com/ferstar/blog/issues/10

1. 强行抹掉远程commit log

> 不小心把不该提交的东西提交了, 可以用这招救命, **团队协作慎用**
```shell
git reset --hard <需要回退到的commit tag>
git push --force
```

