---
title: "祖传系统无损迁机：btrfs send/receive 实操记录"
slug: "btrfs-send-receive-system-migration"
date: "2026-09-28T11:00:00+08:00"
tags: ["Linux", "Btrfs", "Arch", "Migration"]
description: "换盘换机不想重装配置？本文记录用 btrfs 只读快照 + send/receive 在线迁移 Arch 系统的完整顺序，含 UUID 替换的四个落点、引导重建，以及真迁新硬件时要补的检查清单。"
---

我有一套从 ThinkPad 时代一路用下来的 Arch 系统，配置调了几年，包列表、zsh 环境、各种 dotfiles 都是攒出来的，重装一遍要命。2023 年先后做过两次整机迁移：一次同机换盘，一次从 SATA 盘迁到 NVMe。用的都是同一套办法：btrfs 只读快照 + send/receive。这里把当时的顺序整理出来，顺便补上真迁新硬件时还要注意的事情。

## 为什么不用 rsync

rsync 能搬文件，但搬不动 btrfs 的三样东西：

- 子卷结构。我的布局按根、用户和系统缓存分成了 5 个平级子卷（`@`、`@home`、`@var@cache`、`@var@log`、`@var@lib@docker`），rsync 搬完就是一堆普通目录，子卷边界全丢。
- 数据校验。btrfs 每个数据块都有 checksum，send/receive 传的是文件系统本身的指令流，到位即可信，不需要传完再比一轮。
- 压缩属性。磁盘是 `compress-force=zstd` 挂载的，send/receive 保留文件系统语义，不像 rsync 那样要在目标端重新压一遍。

快照是写时复制的，打一个只读快照几乎瞬时，系统继续跑，不影响任何服务——这就是在线迁移的基础。

## 先清垃圾再打快照

快照搬的是整个子卷，垃圾搬过去还是垃圾，只是让 send 更慢、目标盘更挤。打快照前值得过一遍：

- 包管理缓存：`pacman -Sc`，以及 AUR 助手的构建缓存（比如 `~/.cache/yay`，大户）
- 孤儿包：`pacman -Rns $(pacman -Qtdq)`
- 系统日志：`journalctl --vacuum-size=100M`
- 用户态缓存（`~/.cache` 里的浏览器缓存等）和回收站

清完再打快照，传的数据量能小一个档次。上次我清掉的一千多 MB AUR 构建缓存，要是跟着快照走就白搬了。

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

统一挂载参数（全程一致）：

```
compress-force=zstd,noatime,ssd,space_cache=v2
```

### 1. 挂载源盘和目标盘

```bash
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/sda2 /tmp/src
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/nvme0n1p4 /tmp/dst
```

### 2. 给每个子卷打只读快照

btrfs send 只认只读快照：

```bash
for i in $(ls -d @* | grep -v _ub); do sudo btrfs subvolume snapshot -r $i ${i}_ro; done
```

### 3. 逐个发送

```bash
sudo btrfs send @_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@log_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@cache_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@lib@docker_ro | sudo btrfs receive /tmp/dst
```

### 4. 快照转正

receive 收到的是 `@_ro` 这种只读子卷。对它再打一个可写快照得到正式的 `@`，再删掉 `_ro` 中间产物：

```bash
for i in $(ls -d *_ro); do
  sudo btrfs subvolume snapshot $i $(echo $i | cut -d '_' -f 1)
  sudo btrfs subvolume delete $i
done
```

### 5. 替换 UUID

这是整个流程里最容易翻车的一步。新分区有新 UUID，`blkid` 查到后用 sed 全局替换旧 UUID，主要改四个地方：

```
etc/fstab                     # 挂载表
etc/timeshift/timeshift.json  # 快照工具
boot/grub/grub.cfg            # 引导配置
boot/grub/grub-btrfs.cfg      # btrfs 快照引导菜单
```

### 6. 处理 ESP 和引导项

```bash
sudo mount /dev/nvme0n1p1 /tmp/dst/@/boot/efi
sudo efibootmgr -c -d /dev/nvme0n1 -p 1 -L "Arch" -l '\efi\boot\bootx64.efi'
```

### 7. 收尾切盘

```bash
sync
sudo umount /tmp/dst/@/boot/efi
sudo umount /tmp/dst
reboot
sudo efibootmgr -v   # 重启后确认引导项
```

## 在线迁移的代价和边界

整个迁移不需要停机。快照瞬时完成，send/receive 跑得再久系统也照常用，改 fstab 和 grub 改的都是目标盘上的副本，与当前运行的系统无关。唯一的中断是最后那次重启切盘——换盘本来就得重启，这不算迁移额外增加的代价。

打完快照后旧盘上的少量新写入（比如新产生的日志）会有意留在旧盘上。个人机器场景这点损失无所谓，所以我没有用增量 send（`send -p`）去补差量；如果是带着不能停的数据库在线搬，才需要先全量、切盘前再补一次增量的两段式做法。

## 真迁新硬件时要补的检查

上面两次都是同机换盘，省掉了最麻烦的一节：硬件差异。换机时对照 ArchWiki 的[迁移指南](https://wiki.archlinux.org/title/Migrate_installation_to_new_hardware)过一遍：

- CPU 换厂商（Intel ↔ AMD）：microcode 包要换（`intel-ucode` / `amd-ucode`）
- GPU 换厂商：显卡驱动要换
- 引导方式差异：目标机 UEFI 设置不同（如 CSM 开关、Secure Boot 状态），必要时新建 ESP 分区并重新注册引导项

另外两处在下次迁移时可以顺手改掉：

1. fstab 和 grub 配置重新生成，不再手 sed。用 `genfstab -U /mnt` 生成挂载表，在目标盘 chroot 里跑 `grub-mkconfig -o /boot/grub/grub.cfg`。手改的 `grub.cfg` 在下次 grub 升级时总有被覆盖掉的隐患。
2. 用 `btrfs send --proto 2 --compressed-data`（需要 btrfs-progs 6.0+ 和内核 6.0+，现在的 Arch 都满足）。它直接传输 zstd 压缩块，不做解压再压缩，跨机传输能省不少时间。

还有一个容易踩的坑：btrfs 快照不递归。如果子卷里嵌套了别的子卷，快照里它只是个空目录。我的 5 个子卷平级挂在顶层，天然没这个问题；要是哪天在 `@home` 里再嵌子卷，send 前就得单独处理。
