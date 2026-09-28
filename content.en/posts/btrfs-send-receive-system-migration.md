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

- **Subvolume structure**. My layout has five sibling subvolumes: `@`, `@home`, `@var@cache`, `@var@log`, `@var@lib@docker`. After rsync they become plain directories; the subvolume boundaries are gone.
- **Data verification**. Every btrfs block has a checksum. send/receive streams filesystem instructions, so the data is trustworthy the moment it lands — no post-copy comparison pass needed.
- **Compression**. My drives are mounted with `compress-force=zstd`. send/receive preserves filesystem semantics instead of decompressing and recompressing at the target the way rsync would.

And since snapshots are copy-on-write, taking a read-only snapshot is near-instant while the system keeps running — that is what makes this an online migration.

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

**Step 1, mount source and target:**

```
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/sda2 /tmp/src
sudo mount -t btrfs -o compress-force=zstd,noatime,ssd,space_cache=v2 /dev/nvme0n1p4 /tmp/dst
```

**Step 2, take a read-only snapshot of every subvolume** (send only accepts read-only snapshots):

```
for i in $(ls -d @* | grep -v _ub); do sudo btrfs subvolume snapshot -r $i ${i}_ro; done
```

**Step 3, send each one:**

```
sudo btrfs send @_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@log_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@cache_ro | sudo btrfs receive /tmp/dst
sudo btrfs send @var@lib@docker_ro | sudo btrfs receive /tmp/dst
```

**Step 4, promote the snapshots.** What receive produces are read-only subvolumes named `@_ro` and so on. Take a writable snapshot of each to get the real `@`, then delete the `_ro` intermediates:

```
for i in $(ls -d *_ro); do
  sudo btrfs subvolume snapshot $i $(echo $i | cut -d '_' -f 1)
  sudo btrfs subvolume delete $i
done
```

**Step 5, replace UUIDs** — the most error-prone part of the whole flow. The new partition has a new UUID; look it up with `blkid`, then sed-replace the old one everywhere. There are four places to touch:

```
etc/fstab                     # mount table
etc/timeshift/timeshift.json  # snapshot tool
boot/grub/grub.cfg            # boot config
boot/grub/grub-btrfs.cfg      # btrfs snapshot boot menu
```

**Step 6, handle the ESP and boot entry:**

```
sudo mount /dev/nvme0n1p1 /tmp/dst/@/boot/efi
sudo efibootmgr -c -d /dev/nvme0n1 -p 1 -L "Arch" -l '\efi\boot\bootx64.efi'
```

**Step 7, wrap up and switch over:**

```
sync
sudo umount /tmp/dst/@/boot/efi
sudo umount /tmp/dst
reboot
sudo efibootmgr -v   # verify the boot entry after reboot
```

## This whole process is online

Worth emphasizing: the migration **requires no downtime**. The snapshot is instant; the system keeps running normally no matter how long send/receive takes; the fstab and grub edits happen on copies that live on the target disk, unrelated to the running system. The only interruption is the final reboot into the new disk — and booting from a swapped disk requires a reboot anyway, so that is not really a migration cost.

A few writes that land on the old disk after the snapshot (fresh logs and the like) are intentionally left behind. For a home machine that loss is irrelevant, so I did not bother with incremental send (`send -p`) to bridge the gap. Only when migrating a database that cannot stop would you need the two-phase approach: full send first, then one incremental pass right before cutover.

## Moving to genuinely different hardware

Both migrations above were disk swaps on the same machine, which skips the hardest part: **hardware differences**. The [ArchWiki migration guide](https://wiki.archlinux.org/title/Migrate_installation_to_new_hardware) says this well; when switching machines, walk through:

- **CPU vendor change** (Intel↔AMD): swap the microcode package (`intel-ucode`/`amd-ucode`)
- **GPU vendor change**: swap the graphics driver
- **Old board MBR → new board UEFI**: a new ESP partition is needed, and the boot setup gets redone

Two improvements I plan to make next time:

1. **Regenerate fstab and grub config instead of hand-sedding them.** Use `genfstab -U /mnt` for the mount table, and run `grub-mkconfig -o /boot/grub/grub.cfg` in a chroot on the target. A hand-edited grub.cfg always risks being overwritten by a future grub upgrade.
2. **`btrfs send --proto 2 --compressed-data`** (needs btrfs-progs 6.0+ and kernel 6.0+; any current Arch qualifies). It transfers zstd-compressed blocks directly without a decompress-recompress round trip, which saves real time on cross-machine transfers.

One more trap worth writing down: btrfs snapshots are **not recursive**. A nested subvolume appears as an empty directory inside a snapshot. My five subvolumes are all siblings at the top level so this never bites me, but if I ever nest a subvolume inside `@home`, it needs separate handling before send.

## A different kind of backup

After working through this flow I realized it does more than migrate machines: the same snapshot can be sent to an external drive for a full-system backup. That is why tools like [btrbk](https://github.com/digint/btrbk) felt immediately familiar — they automate exactly the "snapshot → send → keep parent for incremental" loop. For a one-off migration, doing it by hand is fine; for recurring backups, use the tool.
