+++
date = "2015-08-19T21:25:43+08:00"
title = "查询局域网在线ip及对应mac地址的方法"
tags = ['OTHERS']

+++

## windows

这个软件很不错 [maxcanner.rar](http://7xivdp.com1.z0.glb.clouddn.com/2015/08/1360260925.rar)，小巧快速，即开即用，有5档扫描方式，一般选择5或者4，可以得到主机名，如果有的话

## ubuntu

arp-scan

```
# apt-get install arp-scan
# arp-scan --interface=eth0 192.168.1.0/24
```