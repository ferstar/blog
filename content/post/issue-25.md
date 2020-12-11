---
title: "Docker 清日志"
date: "2020-09-25T02:27:34+08:00"
tags: ['Docker', 'Linux']
comments: false
---

> created_date: 2020-09-25T02:27:34+08:00

> update_date: 2020-12-11T22:19:10+08:00

> comment_url: https://github.com/ferstar/blog/issues/25

> 这玩意属于粗暴玩法，要确定日志没用才能搞

`truncate -s 0 /var/lib/docker/containers/*/*-json.log`

出处: https://stackoverflow.com/a/43570083

