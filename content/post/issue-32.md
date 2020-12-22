---
title: "Linux系统备份小计"
date: "2020-12-13T08:08:17+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-12-13T08:08:17+08:00

> update_date: 2020-12-22T04:29:59+08:00

> comment_url: https://github.com/ferstar/blog/issues/32

### BTRFS专用，snapshot

> 这个其实最方便最无感，有个软件很犀利：[timeshift](https://github.com/teejee2008/timeshift)，核心就是利用btrfs文件系统的快照能力，但是成也快照败也快照，只能放在同盘分区下，如果单盘扑街，资料就跪了。

![image](https://user-images.githubusercontent.com/2854276/102006755-83a85780-3d5e-11eb-8c52-22be45b05e78.png)

### 利用tar做备份

> 以Ubuntu为例, 参考[BackuoYourSystem](https://help.ubuntu.com/community/BackupYourSystem/TAR)，适用于任意文件系统备份

#### 用到的非系统内置软件
- zstd：新一代无损压缩算法实现，用来压缩备份文件（需安装）
- pv：用以显示命令行工具执行进度（需安装）

#### 备份

> 以zstd压缩方式打包/目录（除/proc /sys /mnt /media /home外），并切分为最大3900MB的分片文件（backup_xxx）

```shell
sudo tar -I zstd -cpf - --exclude=/home --exclude=/proc --exclude=/tmp --exclude=/mnt --exclude=/dev --exclude=/sys --exclude=/run --exclude=/media --exclude=/var/log --exclude=/var/cache/apt/archives --one-file-system / | pv -s $(du -sb . | awk '{print $1}') | split -b 3900m - -d -a 3 backup_
```

附上备份输出，可以看出pv给的进度其实不准，看看而已

```shell
tar: Removing leading `/' from member names
tar: Removing leading `/' from hard link targets               ] 17% ETA 0:01:05
tar: /root/.cache/keyring-87BMU0/control: socket ignored       ] 19% ETA 0:01:10
tar: /var/snap/canonical-livepatch/95/livepatchd-priv.sock: socket ignored:00:05
tar: /var/snap/canonical-livepatch/95/livepatchd.sock: socket ignored
tar: /var/xdroid/common/data/system/ndebugsocket: socket ignored108% ETA 0:00:00
tar: /var/xdroid/common/runtime/xdroid/sockets/0/qemu_pipe: socket ignored:00:00
tar: /var/xdroid/common/runtime/xdroid/sockets/0/xdroid_bridge: socket ignored
tar: /var/xdroid/common/runtime/xdroid/input/0/event0: socket ignored
tar: /var/xdroid/common/runtime/xdroid/input/0/event1: socket ignored
tar: /var/xdroid/common/runtime/xdroid/input/0/event2: socket ignored
tar: /var/xdroid/common/sockets/xdroid-container.socket: socket ignored
10.1GiB 0:01:49 [94.8MiB/s] [=================================] 116%
```

#### 恢复

> 进入recovery模式或者liveCD模式，恢复备份
```shell
cat backup_* | pv - | sudo tar -I zstd -xpf - -C /media/path_to_rec --numeric-owner
# 补足缺失的目录
mkdir /proc /sys /mnt /media /dev
```

#### 修复引导

```shell
sudo -s
for f in dev dev/pts proc ; do mount --bind /$f /media/whatever/$f ; done
chroot /media/whatever
dpkg-reconfigure grub-pc
```

