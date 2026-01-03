---
title: "Reload Intel AX201 wireless card on Ubuntu"
slug: "reload-intel-ax201-driver-ubuntu"
date: 2019-12-14T16:47:09+08:00
tags: ['UBUNTU']
comments: true
---

我佛了，不知道进行了某次更新后，WiFi开始狂掉，坑爹的不行，各种骚操作也是没锤子卵用，后来换成连2.4G，好了。。。WiFi6的5G有毒？

---fuck iwlwifi---

前阵子买了美帝联想的年度真香本:小新pro 13 i7版, 装Ubuntu是必须的, 然而这个本子硬件太新, 无线网卡驱动要求系统内核>5.2才能装, 然而实际上就算是装了官网的驱动, 这破网卡也是会间歇性断网, 重连还没发连, dmesg看一堆关于网卡的报错, 没法子, 只能写个批处理重载驱动&重启nm了, 还真好使, 总比重启大法好

```shell
#!/bin/sh

rmmod iwlmvm
rmmod iwlwifi

modprobe iwlwifi
systemctl restart NetworkManager.service

```
玩Linux机器还是不能太新啊~
