---
date = "2016-08-31T10:24:00+08:00"
title = "grub引导修复"
tags = ['OTHERS']
---

> 很久很久前写的一个折腾记录, 现在启动都差不多是`GPT+UEFI`的模式了, 以下纯做纪念

安装完 ubuntu 之后，若再安装 windows xp 作业系统到其它的 partition 就会破坏掉原本 MBR 中的 GRUB，导致从此以后只能开机进 XP，没办法再多重开机了。其实那只是 MBR 中的 GRUB 启动区被 windows xp 安装程式给盖掉了，整个完整的 GRUB 并没有消失，拿出 ubuntu 光碟即可救回来。
1. 用 ubuntu 光碟开机后，执行 sudo grub
2. 输入 find /boot/grub/stage1 指令找出当初存放 /boot/grub/stage1 的地方在什么 partition，有时候可能会找不到，如果有印象当初安装时这个 /boot/grub/ 的目录摆在什么地方的话，那也没有关系。
3. 输入 root (hd0,0) 指令，表示当初 /boot/grub/ 的目录摆在 /dev/hda1
4. 输入 setup (hd0) 指令，表示将 GRUB 的启动器重新写到 /dev/hda 磁碟的 MBR 上。
5. 输入 quit 指令可以离开 grub 的设定程式，重新开机后即可看到 GRUB 原来的多重开机选单。
用LIVECD进入系统

打开终端,输入

sudo grub
grub> root (hd0,*)
grub> setup (hd0)

* 为你已经安装ubuntu系统的根所在区

如果您不确定 * ，您可以打开 gpart 分区编辑器软件查看

系统 System -> 系统管理 Administrator -> gpart

记下 /dev/sda*

因为 grub 中 0 表示第一个区， 1 表示第二个区，所以把 * - 1 差就是真正的 *
