---
title: "Fsck Error on Boot Dev Sda7 Unexpected Inconsistency Run Fsck Manually"
date: 2018-02-26T08:53:37+08:00
tags: ['LINUX', 'UBUNTU']
comments: true
---

台式机一直双系统跑 Windows10 和 Ubuntu 16.04，昨天单位意外断电，悲剧的事情发生了，Ubuntu 无法启动，failsafe 启动看 log 显示 `/dev/sda7：UNEXPECTED INCONSISTENCY;RUN fsck MANUALLY`，顺手 Google 一番，找到解决办法，记录下：

via <https://askubuntu.com/questions/697190/fsck-error-on-boot-dev-sda6-unexpected-inconsistency-run-fsck-manually>

基本上就是在`initramfs`命令行敲如下命令即可搞定

`fsck -sy /dev/sda2`

