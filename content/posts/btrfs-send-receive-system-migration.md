---
title: "祖传系统无损迁机:btrfs send/receive 实操记录"
slug: "btrfs-send-receive-system-migration"
date: "2026-09-28T11:00:00+08:00"
tags: ["Linux", "Btrfs", "Arch", "Migration"]
description: "换盘换机不想重装配置?本文记录用 btrfs 只读快照 + send/receive 在线迁移 Arch 系统的完整顺序,含 UUID 替换的四个落点、引导重建,以及真迁新硬件时要补的检查清单。"
---

我有一套从 ThinkPad 时代一路用下来的 Arch 系统,配置调了几年,包列表、zsh 环境、各种 dotfiles 都是攒出来的,重装一遍要命。2023 年先后做过两次整机迁移:一次同机换盘,一次从 SATA 盘迁到 NVMe。用的都是同一套办法:**btrfs 只读快照 + send/receive**。本文把当时的顺序整理出来,顺便补上"真迁新硬件"时还要注意的东西。

## 为什么不用 rsync

rsync 能搬文件,但搬不动 btrfs 的三样东西:

- **子卷结构**。我的布局是 `@`、`@home`、`@var@cache`、`@var@log`、`@var@lib@docker` 五个平级子卷,rsync 搬完就是一堆普通目录,子卷边界全丢。
- **数据校验**。btrfs 每个数据块都有 checksum,send/receive 传的是文件系统本身的指令流,到位即可信,不需要传完再比一轮。
- **压缩属性**。磁盘是 `compress-force=zstd` 挂载的,send/receive 保留文件系统语义,不像 rsync 那样要在目标端重新压一遍。

而快照是写时复制的,打一个只读快照几乎瞬时,系统继续跑,不影响任何服务——这就是在线迁移的基础。

## 第零步:先清垃圾再打快照

快照搬的是整个子卷,垃圾搬过去还是垃圾,只是让 send 更慢、目标盘更挤。打快照前值得过一遍:

- 包管理缓存:`pacman -Sc`,以及 AUR 助手的构建缓存(比如 `~/.cache/yay`,大户)
- 孤儿包:`pacman -Rns $(pacman -Qtdq)`
- 系统日志:`journalctl --vacuum-size=100M`
- 用户态缓存(`~/.cache` 里的浏览器缓存等)和回收站

清完再打快照,传的数据量能小一个档次——我上次清掉的一千多 MB AUR 构建缓存,要是跟着快照走就白搬了。

## 完整顺序

{{< mermaid >}}
flowchart LR
    A[挂载源盘/目标盘] --> B[逐子卷打只读快照]
    B --> C[send 对 receive]
    C --> D[快照转正为可写子卷]
    D --> E[替换 UUID: fstab/timeshift/grub]
    E --> F[挂 ESP 注册引导]
    F --> G[sync 卸载 重启切盘]
{{< /mermaid >}}

统一挂载参数(全程一致):

```
compress-force=zstd,noatime,ssd,space_cache=v2
```

**第一步,挂上源盘和目标盘:**

```
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/sda2 /tmp/src
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/nvme0n1p4 /tmp/dst
```

**第二步,给每个子卷打只读快照**(send 只认只读快照):

```
for i in $(ls -d @* | grep -v _ub); do sudo btrfs subvolume snapshot -r $i ${i}_ro; done
```

**第三步,逐个发送:**

```
sudo btrfs send @_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@log_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@cache_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@lib@docker_ro | sudo btrfs receive /tmp/dst
```

**第四步,快照转正**。receive 收到的是 `@_ro` 这样的只读子卷,对它再打一个可写快照得到正式的 `@`,然后删掉 `_ro` 中间产物:

```
for i in $(ls -d *_ro); do
  sudo btrfs subvolume snapshot $i $(echo $i | cut -d '_' -f 1)
  sudo btrfs subvolume delete $i
done
```

**第五步,替换 UUID**,这是整个流程里最容易翻车的一步。新分区有新 UUID,`blkid` 查到后,sed 全局替换旧 UUID,落点有四个:

```
etc/fstab                     # 挂载表
etc/timeshift/timeshift.json  # 快照工具
boot/grub/grub.cfg            # 引导配置
boot/grub/grub-btrfs.cfg      # btrfs 快照引导菜单
```

**第六步,处理 ESP 和引导项:**

```
sudo mount /dev/nvme0n1p1 /tmp/dst/@/boot/efi
sudo efibootmgr -c -d /dev/nvme0n1 -p 1 -L "Arch" -l '\efi\boot\bootx64.efi'
```

**第七步,收尾切盘:**

```
sync
sudo umount /tmp/dst/@/boot/efi
sudo umount /tmp/dst
reboot
sudo efibootmgr -v   # 重启后确认引导项
```

## 这个过程是在线的

值得强调:整个迁移**不需要停机**。快照瞬时完成,send/receive 跑得再久系统也照常用,改 fstab、grub 改的都是目标盘上的副本,与运行中的系统无关。唯一的中断就是最后那次重启切盘——而换盘启动本来就要重启一次,这不算迁移的代价。

快照之后旧盘上的少量新写入(新日志之类)会有意留在旧盘上。家用机场景这点损失无所谓,所以我没有上增量 send(`send -p`)去补差量;如果要带着不能停的数据库在线搬,才需要"先全量、切盘前再补一次增量"的两段式。

## 真迁新硬件,还要补什么

上面两次都是同机换盘,所以少了最难啃的一节:**硬件差异**。ArchWiki 的[迁移指南](https://wiki.archlinux.org/title/Migrate_installation_to_new_hardware)提醒得很到位,换机时逐项对一遍:

- **CPU 换厂商**(Intel↔AMD):microcode 包要换(`intel-ucode`/`amd-ucode`)
- **GPU 换厂商**:显卡驱动要换
- **老主板 MBR → 新主板 UEFI**:要新建 ESP 分区,引导方式整体重来

另外两处我打算在下次迁移时改进:

1. **fstab 和 grub 配置重新生成,而不是手 sed**。用 `genfstab -U /mnt` 生成挂载表,在目标盘 chroot 里跑 `grub-mkconfig -o /boot/grub/grub.cfg`。手改的 grub.cfg 总会有下次升级被覆盖生成的隐患。
2. **`btrfs send --proto 2 --compressed-data`**(需要 btrfs-progs 6.0+ 和内核 6.0+,现在的 Arch 都满足)。它直接传输 zstd 压缩块,不做解压-再压缩,跨机传输能省不少时间。

还有一个容易踩的坑提前记一笔:btrfs 快照**不递归**。如果子卷里嵌套了别的子卷,快照里它只是个空目录。我的五个子卷是平级挂在顶层,天然没这个问题,但如果哪天在 `@home` 里再嵌子卷,send 前要单独处理。

## 备份性质的不同

这套流程做完后,我发现它不止能迁机:同一个快照既能 send 到新盘,也能 send 到外置硬盘做整机备份。所以后来看到 [btrbk](https://github.com/digint/btrbk) 这类增量备份工具时会觉得眼熟——它们做的事就是把"打快照 → send → 保留父快照做增量"这套动作自动化。一次性迁移手搓就够了,定期备份值得上工具。
