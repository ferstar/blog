---
title: "Mkhash Cannot Execute Binary File"
date: 2018-12-20T10:25:00+08:00
tags: ['OPENWRT']
comments: false
---

编译openwrt固件时碰到这么个问题, 记录下解决方案:

```shell
cd scripts
gcc mkhash.c -o mkhash
mv mkhash ../staging_dir/host/bin/mkhash
```

原因就是
```shell
$ ./scripts/feeds update -a
$ ./scripts/feeds install -a
```
这两命令执行完`mkhash`这个程序居然没有自动编译好, 原因就不深究了, 毕竟只是用用而已