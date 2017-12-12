---
title: "挂代理&apt-fast多线程更新packages"
date: "2015-08-31T23:06:06+08:00"
tags: ['OTHERS']
comments: 
---

因为更新并不是频繁操作，所以只需要临时(**只在当前终端生效**)在终端指定下proxy
```
sudo -i
# 这里当然需要你提前在内网90的机器上配好http fuck gfw代理喽
export http_proxy=http://192.168.1.90:8118/
```
这样就在当前终端临时给root用户指定了内网代理

`apt-get`工具默认是单线程的，还是太慢，可以用另外的一个工具代替`apt-fast`
```
apt-get install axel
axel -o /usr/bin/apt-fast http://www.mattparnell.com/linux/apt-fast/apt-fast.sh
chmod +x /usr/bin/apt-fast
```
使用很简单，直接apt-fast替换apt-get即可

经过上述折腾，在比较生僻的国外源拖packages的速度会大有改善
