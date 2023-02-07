---
title: "记一次莫名的BTRFS修复过程"
date: "2023-02-07T06:32:08+08:00"
tags: ['Linux']
comments: true
---

> 吃着火锅唱着歌，啪，分区被锁，dmesg 日志飘红 —— 盘挂了

赶紧重启进 LiveCD 尝试挂载`mount -o rescue=usebackuproot /dev/nvme0n1p5 /mnt`，扑街

```shell
[  183.966960] BTRFS info (device nvme0n1p5): using crc32c (crc32c-intel) checksum algorithm
[  183.966967] BTRFS info (device nvme0n1p5): trying to use backup root at mount time
[  183.966968] BTRFS info (device nvme0n1p5): using free space tree
[  183.968909] BTRFS info (device nvme0n1p5): bdev /dev/nvme0n1p5 errs: wr 0, rd 0, flush 0, corrupt 1, gen 0
[  183.985663] BTRFS info (device nvme0n1p5): enabling ssd optimizations
[  183.985665] BTRFS info (device nvme0n1p5): start tree-log replay
[  184.107729] BTRFS error (device nvme0n1p5): incorrect extent count for 122436976640; counted 1577, expected 1575
[  184.107744] BTRFS: error (device nvme0n1p5) in btrfs_replay_log:2395: errno=-5 IO failure (Failed to recover log tree)
[  184.120547] BTRFS error (device nvme0n1p5: state E): open_ctree failed
```

死马当活马医，`btrfsck --repair /dev/nvme0n1p5` 有个倒计时警告，不管了，直接上

```shell
enabling repair mode
WARNING:

        Do not use --repair unless you are advised to do so by a developer
        or an experienced user, and then only after having accepted that no
        fsck can successfully repair all types of filesystem corruption. Eg.
        some software or hardware bugs can fatally damage a volume.
        The operation will start in 10 seconds.
        Use Ctrl-C to stop it.
10 9 8 7 6 5 4 3 2 1
Starting repair.
Opening filesystem to check...
Checking filesystem on /dev/nvme0n1p5
UUID: 3681c364-deb7-4275-8e5d-9c6991467acb
repair mode will force to clear out log tree, are you sure? [y/N]: y
[1/7] checking root items
Fixed 0 roots.
[2/7] checking extents
data extent[124231548928, 61440] referencer count mismatch (parent 180895744) wanted 0 have 1
data extent[124231548928, 61440] bytenr mimsmatch, extent item bytenr 124231548928 file item bytenr 0
data extent[124231548928, 61440] referencer count mismatch (parent 4503599808266240) wanted 1 have 0
backpointer mismatch on [124231548928 61440]
repair deleting extent record: key [124231548928,168,61440]
adding new data backref on 124231548928 parent 180895744 owner 0 offset 0 found 1
Repaired extent references for 124231548928
super bytes used 112946282496 mismatches actual used 112946118656
No device size related problem found
[3/7] checking free space tree
free space info recorded 1575 extents, counted 1577
There are still entries left in the space cache
cache appears valid but isn't 122436976640
Clear free space cache v2
free space cache v2 cleared
[4/7] checking fs roots
[5/7] checking only csums items (without verifying data)
[6/7] checking root refs
[7/7] checking quota groups skipped (not enabled on this FS)
found 225892401152 bytes used, no error found
total csum bytes: 217257440
total tree bytes: 3289513984
total fs tree bytes: 2747269120
total extent tree bytes: 271155200
btree space waste bytes: 533066137
file data blocks allocated: 2738343133184
 referenced 315154259968
```

估摸着有戏，赶紧再挂一次`mount -o rescue=usebackuproot /dev/nvme0n1p5 /mnt`，居然就成了，赶紧`dmesg | grep -i btrfs`瞧一瞧

```shell
[  183.966960] BTRFS info (device nvme0n1p5): using crc32c (crc32c-intel) checksum algorithm
[  183.966967] BTRFS info (device nvme0n1p5): trying to use backup root at mount time
[  183.966968] BTRFS info (device nvme0n1p5): using free space tree
[  183.968909] BTRFS info (device nvme0n1p5): bdev /dev/nvme0n1p5 errs: wr 0, rd 0, flush 0, corrupt 1, gen 0
```

这时候分区已经正常了，但是这行数字看着扎眼，强迫症不能忍：` errs: wr 0, rd 0, flush 0, corrupt 1, gen 0`

再来一发`btrfs scrub start /mnt`，开`dmesg -w`看下哪些文档没得救

```shell
BTRFS info (device nvme0n1p5): scrub: started on devid 1
BTRFS warning (device nvme0n1p5): checksum error at logical 54326345728 on dev /dev/nvme0n1p5, physical 56482217984, root 259, inode 611588, offset 1441792, length 4096, links 1 (path: ferstar/Downloads/log (2).tar.gz)
BTRFS error (device nvme0n1p5): bdev /dev/nvme0n1p5 errs: wr 0, rd 0, flush 0, corrupt 2, gen 0
BTRFS error (device nvme0n1p5): unable to fixup (regular) error at logical 54326345728 on dev /dev/nvme0n1p5
BTRFS warning (device nvme0n1p5): checksum error at logical 123690389504 on dev /dev/nvme0n1p5, physical 125846261760, root 259, inode 2161195, offset 593920, length 4096, links 1 (path: ferstar/pyprojects/hkex/data/files/cf/0cdb845691cbe2c22789c727e00745)
BTRFS warning (device nvme0n1p5): checksum error at logical 123690455040 on dev /dev/nvme0n1p5, physical 125846327296, root 259, inode 2161195, offset 659456, length 4096, links 1 (path: ferstar/pyprojects/hkex/data/files/cf/0cdb845691cbe2c22789c727e00745)
BTRFS error (device nvme0n1p5): bdev /dev/nvme0n1p5 errs: wr 0, rd 0, flush 0, corrupt 3, gen 0
BTRFS error (device nvme0n1p5): bdev /dev/nvme0n1p5 errs: wr 0, rd 0, flush 0, corrupt 4, gen 0
BTRFS error (device nvme0n1p5): unable to fixup (regular) error at logical 123690455040 on dev /dev/nvme0n1p5
BTRFS error (device nvme0n1p5): unable to fixup (regular) error at logical 123690389504 on dev /dev/nvme0n1p5
BTRFS warning (device nvme0n1p5): checksum error at logical 123690463232 on dev /dev/nvme0n1p5, physical 125846335488, root 259, inode 2161195, offset 667648, length 4096, links 1 (path: ferstar/pyprojects/hkex/data/files/cf/0cdb845691cbe2c22789c727e00745)
BTRFS error (device nvme0n1p5): bdev /dev/nvme0n1p5 errs: wr 0, rd 0, flush 0, corrupt 5, gen 0
BTRFS error (device nvme0n1p5): unable to fixup (regular) error at logical 123690463232 on dev /dev/nvme0n1p5
BTRFS info (device nvme0n1p5): scrub: finished on devid 1 with status: 0
```

把没救的文档删掉，然后清一下错误计数器`btrfs dev stats -z /mnt`

卸载再挂载一次，日志终于正常，完美

```shell
Btrfs loaded, crc32c=crc32c-intel, zoned=yes, fsverity=yes
BTRFS: device fsid 3681c364-deb7-4275-8e5d-9c6991467acb devid 1 transid 104541 /dev/nvme0n1p5 scanned by systemd-udevd (270)
BTRFS info (device nvme0n1p5): using crc32c (crc32c-intel) checksum algorithm
BTRFS info (device nvme0n1p5): disk space caching is enabled
BTRFS info (device nvme0n1p5): enabling ssd optimizations
BTRFS info (device nvme0n1p5): checking UUID tree
BTRFS info (device nvme0n1p5: state M): trying to use backup root at mount time
BTRFS info (device nvme0n1p5: state M): force zstd compression, level 3
```

附上参考资料：

- https://zyyme.com/btrfs-fix.html
- https://btrfs.readthedocs.io
- https://blog.firerain.me/article/21
- https://www.reddit.com/r/btrfs/comments/plmm01/comment/hcc83el



```
# NOTE: I am not responsible for any expired content.
create@2023-02-07T06:32:08+08:00
update@2023-02-07T06:32:08+08:00
comment@https://github.com/ferstar/blog/issues/75
```
