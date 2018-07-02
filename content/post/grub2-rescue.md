---
title: "修复升级BIOS导致grub意外丢失的问题"
date: 2018-07-02T17:43:32+08:00
tags: ['LINUX']
comments: true
---

给老本子（x220）升 BIOS 后不知为何直接 Grub 给搞挂了，怎一个蛋疼了得。所幸折腾一通安全找回，记录下过程：

```shell
# 先看看/分区对不对
grub> echo $root
hd1, gpt2
# 没毛病，是第二块盘的第二个分区

# 看看磁盘分区状况
# 双硬盘，hd0装的Windows10，hd1装的ubuntu 16.04
grub> ls
(hd0) (hd0, gpt7) ... (hd1, gpt2) (hd1, gpt1)

# 看看grub路径
grub> echo $prefix

# 居然是空的，这样肯定没法加载normal模块
# 所以下一步就是设定这个 prefix 路径
grub> set prefix=(hd1,gpt2)/@/boot/grub
# tab 补全这里是可以用的，很方便

# 设定完以后加载 normal 模块
grub> insmod normal
# 没报错，加载成功，接下来就启动 grub 菜单
grub> normal
```

先进 Ubuntu，打开 terminal 重新安装一下 grub

```shell
sudo grub-install /dev/sdb1
```

重启即恢复正常。