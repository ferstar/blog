---
title: "Docker 清日志"
date: "2020-09-25T02:27:34+08:00"
tags: ['Docker', 'Linux']
comments: true
---

> 这玩意属于粗暴玩法，要确定日志没用才能搞

`truncate -s 0 /var/lib/docker/containers/*/*-json.log`

出处: https://stackoverflow.com/a/43570083



```
# NOTE: I am not responsible for any expired content.
create@2020-09-25T02:27:34+08:00
update@2021-02-14T16:34:40+08:00
comment@https://github.com/ferstar/blog/issues/25
```
