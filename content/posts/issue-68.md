---
title: "更换Manjaro默认坑爹的grub"
slug: "manjaro-replace-default-grub"
date: "2023-01-24T00:57:55+08:00"
tags: ['Linux']
comments: true
---

前阵子换了个新电脑，重装是不可能的，于是拷一份老机的数据到新机，具体过程不表，基本就是 [#32](https://blog.ferstar.org/post/issue-32/) 说的那套。

搞完发现系统么发启动，具体报错忘了，大概就是找不到启动配置的意思，这种一般就是grub的问题，于是进`/boot/efi`瞧一瞧：

```shell
cd /boot/efi/EFI/manjaro
strings grubx64.efi | grep gpt
# 以下为输出
partmap/gpt.c
part_gpt
grub_gpt_partition_map_iterate
(,gpt5)/@/boot/grub
```

好家伙，这里把grub入口写死了，我旧盘root在gpt5，但新盘是gpt2，咋玩呢？一种方法是搞个Manjaro的rescure镜像，从镜像chroot进去给重装一下grub，见：https://wiki.manjaro.org/index.php/UEFI_-_Install_Guide

鉴于对这种写死做法的鄙夷，我决定换一种优雅的解决办法：

~~随便找了个 Ubuntu 的 Server 镜像，从里面把 /efi/{Boot,ubuntu} 一起拷贝出来~~

~~把 /boot/efi/EFI/Boot/bootx64.efi 用 Ubuntu 的替换掉~~

其实完全可以用`grub-mkimage`这个工具来自定义生成一个个性的efi文件：

```shell
grub-mkimage -o bootx64.efi -O x86_64-efi -p /EFI/helloworld ntfs hfs appleldr \
  boot cat efi_gop efi_uga elf fat hfsplus iso9660 linux keylayouts memdisk \
  minicmd part_apple ext2 extcmd xfs xnu part_bsd part_gpt search \
  search_fs_file chain btrfs loadbios loadenv lvm minix minix2 reiserfs \
  memrw mmap msdospart scsi loopback normal configfile gzio all_video efi_gop \
  efi_uga gfxterm gettext echo boot chain eval ls test sleep png gfxmenu part_msdos
```

把 /boot/efi/EFI/ubuntu 复制过去，修改一下 grub.cfg 里面的 uuid 指向新盘 root 分区的 uuid 即可

```shell
search.fs_uuid f622fc86-161c-42dc-9a19-9c3c756d6ced root
set prefix=($root)'/@/boot/grub'  # 这里我用的是 btrfs 子卷 @ 作为 rootfs
configfile $prefix/grub.cfg
```

可以看一下 Ubuntu 这个 grubx64.efi 的部分内容 `strings grubx64.efi | grep cfg`

```shell
%s/grub.cfg
feature_net_search_cfg
```

引导路径是这样的：EFI -> Boot -> bootx64.efi -> grubx64.efi -> grub.cfg -> rootfs/grub.cfg -> boot，比 Manjaro 多了按配置查找 grub.cfg 的这一步，我觉得很赞。

当然这个方式有个小瑕疵：如果你用类似 refind 这种 boot manager 的话，会发现启动 Manjaro 的启动图标变成了 Ubuntu，明显这玩意是靠 /boot/efi/EFI/xxx 来判断目标OS的，对于我这种 N 久不关机的人来说，可以忽略不计。

强迫症患者可以在正常进入 Manjaro 以后自行重装 grub，然后删除 /boot/efi/EFI/ubuntu 即可。



```
# NOTE: I am not responsible for any expired content.
create@2023-01-24T00:57:55+08:00
update@2023-02-09T15:16:17+08:00
comment@https://github.com/ferstar/blog/issues/68
```
