---
title: "SwapFAQ"
date: "2015-09-10T11:26:52+08:00"
tags: ['OTHERS']
comments: true
---

关于swap的介绍，挺详细，值得一看：
[https://help.ubuntu.com/community/SwapFaq](https://help.ubuntu.com/community/SwapFaq)

其中比较常用的就是调`swappiness`值

- To check the swappiness value
`cat /proc/sys/vm/swappiness`
- To change the swappiness value A temporary change (lost on reboot) with a swappiness value of 10 can be made with
`sudo sysctl vm.swappiness=10`
- To make a change permanent, edit the configuration file with your favorite editor:
`sudo gedit /etc/sysctl.conf`
-  Search for vm.swappiness and change its value as desired. If vm.swappiness does not exist, add it to the end of the file like so:
`vm.swappiness=10`内存如果够大，这里完全可以设为0，或者干脆干掉swap分区
Save the file and reboot.

