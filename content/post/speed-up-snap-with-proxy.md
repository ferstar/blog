---
title: "给snap加代理"
date: 2019-12-23T14:38:05+08:00
tags: ['LINUX']
comments: true
---

Ubuntu 自 16.04 开始自带的 snap 用起来真是舒服, 不过直连网络太差, 需要代理
需要在`/etc/environment`中指定需要使用的proxy
```shell
http_proxy="socks5://192.168.0.25:7891"
https_proxy="socks5://192.168.0.25:7891"
```
然后重启一下 snap service
`sudo systemctl restart snapd.service`

## 删除snap历史packages

```shell
#!/bin/bash
# Removes old revisions of snaps
# CLOSE ALL SNAPS BEFORE RUNNING THIS
set -eu

LANG=C snap list --all | awk '/disabled/{print $1, $3}' |
    while read snapname revision; do
        snap remove "$snapname" --revision="$revision"
    done

```
