---
title: "备份Linux系统小计"
date: "2020-12-13T08:08:17+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-12-13T08:08:17+08:00

> update_date: 2020-12-13T08:08:17+08:00

> comment_url: https://github.com/ferstar/blog/issues/32

> 以Ubuntu为例, 参考[BackuoYourSystem](https://help.ubuntu.com/community/BackupYourSystem/TAR)

#### 用到的非系统内置软件
- zstd：新一代无损压缩算法实现，用来压缩备份文件（需安装）
- pv：用以显示命令行工具执行进度（需安装）

#### 备份

> 以zstd压缩方式打包/目录（除/proc /sys /mnt /media /home外），并切分为最大3900MB的分片文件（backup_xxx）

```shell
sudo tar -I zstd -cpf - --exclude=/home --exclude=/proc --exclude=/tmp --exclude=/mnt --exclude=/dev --exclude=/sys --exclude=/run --exclude=/media --exclude=/var/log --exclude=/var/cache/apt/archives --one-file-system / | pv -s $(du -sb . | awk '{print $1}') | split -b 3900m - -d -a 3 backup_
```

#### 恢复

> 进入recovery模式或者liveCD模式，恢复备份
```shell
cat backup_* | pv - | sudo tar -I zstd -xpf - -C /media/path_to_rec
# 补足缺失的目录
mkdir /proc /sys /mnt /media 
```

#### 修复引导

```shell
sudo -s
for f in dev dev/pts proc ; do mount --bind /$f /media/whatever/$f ; done
chroot /media/whatever
dpkg-reconfigure grub-pc
```

