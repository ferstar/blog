---
title: "不死小强——timeshift+btrfs-grub"
slug: "linux-timeshift-btrfs-grub-guide"
date: "2022-05-01T14:04:25+08:00"
tags: ['Linux']
comments: true
---

> 以下几个组合可以达到这样的一个效果: 系统自动快照, 同时快照会自动添加到开机启动项, 机器从此变身不死小强

- BTRFS 文件系统
- TimeShift
- btrfs-grub

我的挂载信息：

> 可以看到我把 cache log docker 等划分了单独的 subvolume，同时启用了 zstd 压缩等特性

```shell
 ~ cat /etc/fstab
# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
UUID=3EB0-83DA /boot/efi       vfat    umask=0077      0       0
UUID=d28630c8-a642-45e6-baae-b41de3da008e /               btrfs   defaults,ssd,noatime,compress-force=zstd,commit=120,space_cache=v2,subvol=/@ 0       2
UUID=d28630c8-a642-45e6-baae-b41de3da008e /home           btrfs   defaults,ssd,noatime,compress-force=zstd,commit=120,space_cache=v2,subvol=/@home 0       0
UUID=d28630c8-a642-45e6-baae-b41de3da008e /var/lib/docker btrfs   defaults,ssd,noatime,compress-force=zstd,commit=120,space_cache=v2,subvol=/@docker 0       0
UUID=d28630c8-a642-45e6-baae-b41de3da008e /var/cache btrfs   defaults,ssd,noatime,compress-force=zstd,commit=120,space_cache=v2,subvol=/@cache 0       0
UUID=d28630c8-a642-45e6-baae-b41de3da008e /var/log btrfs   defaults,ssd,noatime,compress-force=zstd,commit=120,space_cache=v2,subvol=/@log 0       0
```

Timeshift 这个不必多说，很好用的一个快照管理软件；

btrfs-grub https://github.com/Antynea/grub-btrfs 直接去项目主页看说明比较好



```
# NOTE: I am not responsible for any expired content.
create@2022-05-01T14:04:25+08:00
update@2023-01-25T15:43:30+08:00
comment@https://github.com/ferstar/blog/issues/60
```
