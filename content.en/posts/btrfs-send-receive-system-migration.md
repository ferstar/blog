---
title: "Losslessly Carrying a Long-Served Arch System to New Hardware with btrfs send/receive"
slug: "btrfs-send-receive-system-migration"
date: "2026-09-28T11:00:00+08:00"
tags: ["Linux", "Btrfs", "Arch", "Migration"]
description: "Dreading a reinstall just because you swapped disks or machines? This post documents the complete workflow of online-migrating an Arch system with read-only btrfs snapshots plus send/receive: the four UUID touchpoints, boot rebuild, and the hardware-difference checklist you need for a true cross-machine move."
---

> I am not a native English speaker; this article was translated by AI.

I have an Arch system that has followed me since my ThinkPad days. Years of accumulated package lists, zsh setup, and dotfiles make a reinstall a genuinely painful prospect. In 2023 I did two full system migrations: one disk swap on the same machine, one from a SATA drive to NVMe. Both used the same approach: **btrfs read-only snapshots plus send/receive**. This post lays out the exact sequence I used, along with what to watch out for when moving to genuinely different hardware.

## Why not rsync

rsync moves files, but it cannot carry three things that matter on btrfs:

- Subvolume structure. My layout splits root, home, and caches across five sibling subvolumes (`@`, `@home`, `@var@cache`, `@var@log`, `@var@lib@docker`). After rsync they become plain directories; the subvolume boundaries are gone.
- Data verification. Every btrfs block has a checksum. send/receive streams filesystem instructions, so the data is trustworthy the moment it lands — no post-copy comparison pass needed.
- Compression. My drives are mounted with `compress-force=zstd`. send/receive preserves filesystem semantics instead of decompressing and recompressing at the target the way rsync would.

And since snapshots are copy-on-write, taking a read-only snapshot is near-instant while the system keeps running — that is what makes this an online migration.

## Clean the junk before snapshotting

The snapshot ships the whole subvolume — garbage carried over is still garbage, only slower to send and more crowded on the target. Before snapshotting, it is worth walking through:

- Package caches: `pacman -Sc`, plus the AUR helper's build cache (e.g. `~/.cache/yay` — usually the biggest offender)
- Orphaned packages: `pacman -Rns $(pacman -Qtdq)`
- System journals: `journalctl --vacuum-size=100M`
- User caches (browser caches under `~/.cache` and the like) and the trash

Clean first, then snapshot — the transferred volume drops noticeably. The gig-plus of AUR build cache I cleaned out last time would otherwise have been shipped along for free.

## The complete sequence

{{< mermaid >}}
flowchart LR
    A[Mount source/target] --> B[RO snapshot per subvolume]
    B --> C[send piped to receive]
    C --> D[Promote snapshots to writable subvolumes]
    D --> E[Replace UUIDs: fstab/timeshift/grub]
    E --> F[Mount ESP, register boot entry]
    F --> G[sync, unmount, reboot into new disk]
{{< /mermaid >}}

One set of mount options used throughout:

```
compress-force=zstd,noatime,ssd,space_cache=v2
```

### 1. Mount source and target

```bash
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/sda2 /tmp/src
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/nvme0n1p4 /tmp/dst
```

### 2. Take a read-only snapshot of every subvolume

send only accepts read-only snapshots:

```bash
for i in $(ls -d @* | grep -v _ub); do sudo btrfs subvolume snapshot -r $i ${i}_ro; done
```

### 3. Send each one

```bash
sudo btrfs send @_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@log_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@cache_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@lib@docker_ro | sudo btrfs receive /tmp/dst
```

### 4. Promote the snapshots

What receive produces are read-only subvolumes named `@_ro` and so on. Take a writable snapshot of each to get the real `@`, then delete the `_ro` intermediates:

```bash
for i in $(ls -d *_ro); do
  sudo btrfs subvolume snapshot $i $(echo $i | cut -d '_' -f 1)
  sudo btrfs subvolume delete $i
done
```

### 5. Replace UUIDs

The most error-prone part of the whole flow. The new partition has a new UUID; look it up with `blkid`, then sed-replace the old one everywhere. There are four places to touch:

```
etc/fstab                     # mount table
etc/timeshift/timeshift.json  # snapshot tool
boot/grub/grub.cfg            # boot config
boot/grub/grub-btrfs.cfg      # btrfs snapshot boot menu
```

### 6. Handle the ESP and boot entry

```bash
sudo mount /dev/nvme0n1p1 /tmp/dst/@/boot/efi
sudo efibootmgr -c -d /dev/nvme0n1 -p 1 -L "Arch" -l '\efi\boot\bootx64.efi'
```

### 7. Wrap up and switch over

```bash
sync
sudo umount /tmp/dst/@/boot/efi
sudo umount /tmp/dst
reboot
sudo efibootmgr -v   # verify the boot entry after reboot
```

## Online migration costs and boundaries

The migration requires no downtime. The snapshot is instant; the system keeps running normally no matter how long send/receive takes; the fstab and grub edits happen on copies that live on the target disk, unrelated to the running system. The only interruption is the final reboot into the new disk — and booting from a swapped disk requires a reboot anyway, so that is not really a migration cost.

A few writes that land on the old disk after the snapshot (fresh logs and the like) are intentionally left behind. For a home machine that loss is irrelevant, so I did not bother with incremental send (`send -p`) to bridge the gap. Only when migrating a database that cannot stop would you need the two-phase approach: full send first, then one incremental pass right before cutover.

## Moving to genuinely different hardware

Both migrations above were disk swaps on the same machine, which skips the hardest part: hardware differences. The [ArchWiki migration guide](https://wiki.archlinux.org/title/Migrate_installation_to_new_hardware) says this well; when switching machines, walk through:

- CPU vendor change (Intel ↔ AMD): swap the microcode package (`intel-ucode` / `amd-ucode`)
- GPU vendor change: swap the graphics driver
- Boot mode differences: the target machine's UEFI setup may differ (CSM off, Secure Boot state); create a new ESP if needed and re-register the boot entry

Two improvements I plan to make next time:

1. Regenerate fstab and grub config instead of hand-sedding them. Use `genfstab -U /mnt` for the mount table, and run `grub-mkconfig -o /boot/grub/grub.cfg` in a chroot on the target. A hand-edited grub.cfg always risks being overwritten by a future grub upgrade.
2. Use `btrfs send --proto 2 --compressed-data` (needs btrfs-progs 6.0+ and kernel 6.0+; any current Arch qualifies). It transfers zstd-compressed blocks directly without a decompress-recompress round trip, which saves real time on cross-machine transfers.

One more trap worth writing down: btrfs snapshots are not recursive. A nested subvolume appears as an empty directory inside a snapshot. My five subvolumes are all siblings at the top level so this never bites me, but if I ever nest a subvolume inside `@home`, it needs separate handling before send.
