---
title: "uefi 方式安装 Biolinux 时遇到的一个坑"
slug: "fix-uefi-biolinux-grub-install-error"
date: "2016-05-26T10:35:27+08:00"
tags: ['OTHERS']
comments: true
---


作为混迹 Linux 颇久的老司机一枚, 安装系统这种事情本不该是啥问题, 然而快安装完的时候出了个吐血的错误提示: 

> the grub-efi-amd64-signed package failed to install into /target/. Without the GRUB bootloader the system will not load

真是囧到无极限啊, 直接连我 Windows 10 启动项也给干翻了. Google 发现这个问题在 12.04 时代是个 BUG, 但是我明明装的是 14.04.1(Biolinux 其实就是在 14.04 的基础上套了一堆生物信息学专用的软件包而已), 一定是哪里姿势不对, 一定是的

于是仔细检查了一遍安装过程: 

1. BIOS 关闭 Security Boot

2. 找一个 4G 多的U盘, 格式化为 FAT32 格式, 然后把 ISO 文件解压全复制进去

3. 开机启动选择从U盘启动

4. 选择 Try 但不 install

5. `sudo umount -l /cdrom`

6. 一路 NEXT

7. EFI 分区使用 Windows 的就行, 网上说什么这个区放驱动啥的全是扯淡, 就几个引导文件, 不占地方, 给 100MB 够意思了, 不能再多

8. 本来想图快, 所以全程断网安装(各种update包网速差的话等待时间很让人崩溃)

> 就是这个过程出了问题, ISO 里面带的 grub-efi* 相关的 package 不全, 需要联网下载, 我安装过程没有联网, 所以悲剧...

简直神坑啊, 坑我好久, 又是检查 ISO md5 又是查分区格式的, 不由得联想到曾经给某妹子远程解决电脑无法联网的问题, 折腾半天那头传来弱弱的一声: "不好意思, 电信发欠费提醒, 我们家网没费了..."

卒~
