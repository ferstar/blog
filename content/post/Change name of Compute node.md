---
title: "Change name of Compute node"
date: "2016-06-17T05:26:00+08:00"
tags: ['OTHERS']
comments: true
---


look at the following commands:

rocks set host name
rocks set host rank
rocks set host rack
rocks set host interface name

e.g. to change the name of compute-0-0 to compute-10-13
```
# rocks set host name compute-0-0 compute-10-13
# rocks set host rank compute-10-13 13
# rocks set host rack compute-10-13 10
# rocks set host interface name compute-10-13 eth0 compute-10-13
# rocks sync config
# rocks sync host network compute-10-13
# rocks run host compute-10-13 "shutdown -r now"
rocks run host "service rocks-grub off"
rocks run host "service rocks-grub stop"
rocks run host "shutdown -r now"
# 重启所有计算节点
```