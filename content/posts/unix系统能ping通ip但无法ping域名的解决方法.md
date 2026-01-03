---
title: "unix系统能ping通ip但无法ping域名的解决方法"
slug: "unix-ping-ip-ping"
date: "2015-09-18T09:22:00+08:00"
tags: ['OTHERS']
comments: true
---


>from [http://www.cnblogs.com/laipDIDI/articles/2213787.html](http://www.cnblogs.com/laipdidi/articles/2213787.html)
```shell
sudo vi /etc/nsswitch.conf
'''
- hosts: files dns
- networks: files
@@
+ hosts: files dns wins
+ networks: files
'''
sudo systemctl restart network.service    #重启rhel网络
```
