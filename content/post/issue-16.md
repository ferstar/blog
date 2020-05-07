---
title: "转换ext4文件系统为btrfs"
date: "2020-01-23T08:09:06+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-01-23T08:09:06+08:00

> update_date: 2020-05-07T08:01:53+08:00

> comment_url: https://github.com/ferstar/blog/issues/16

主要用这个工具`fstransform`
先记录一下运行日志：

```shell
tianbot@ros2go:~$ sudo fstransform /dev/nvme0n1p4 btrfs --force-untested-file-systems
fstransform: starting version 0.9.3, checking environment
fstransform: checking for which... 	'/usr/bin/which'
fstransform: checking for expr... 	'/usr/bin/expr'
fstransform: checking for id... 	'/usr/bin/id'
fstransform: parsing command line arguments
fstransform: forcing trasformation of untested file systems (DANGEROUS). '--force-untested-file-systems' bytes specified on command line
fstransform: checking for stat... 	'/usr/bin/stat'
fstransform: checking for mkfifo... 	'/usr/bin/mkfifo'
fstransform: checking for blockdev... 	'/sbin/blockdev'
fstransform: checking for losetup... 	'/sbin/losetup'
fstransform: checking for fsck... 	'/sbin/fsck'
fstransform: checking for mkfs... 	'/sbin/mkfs'
fstransform: checking for mount... 	'/bin/mount'
fstransform: checking for umount... 	'/bin/umount'
fstransform: checking for mkdir... 	'/bin/mkdir'
fstransform: checking for rmdir... 	'/bin/rmdir'
fstransform: checking for rm... 	'/bin/rm'
fstransform: checking for dd... 	'/bin/dd'
fstransform: checking for sync... 	'/bin/sync'
fstransform: checking for fsmove... 	'/usr/sbin/fsmove'
fstransform: checking for fsremap... 	'/usr/sbin/fsremap'
fstransform: checking for fsck(source file-system)...	'/sbin/fsck'
fstransform: checking for fsck(target file-system)...	'/sbin/fsck'
fstransform: looking for optional commands
fstransform: checking for sleep... 	'/bin/sleep'
fstransform: checking for date... 	'/bin/date'
15:24:46 fstransform: environment check passed.
15:24:46 fstransform: saving output of this execution into /var/tmp/fstransform/fstransform.log.5394
15:24:46 fstransform: preparing to transform device '/dev/nvme0n1p4' to file-system type 'btrfs'
15:24:46 fstransform: device '/dev/nvme0n1p4' not found in the output of command /bin/mount, assuming it is not mounted
15:24:46 fstransform: device is now mounted at '/tmp/fstransform.mount.5394' with file-system type 'ext4'
         
15:24:46 fstransform: WARNING: this program is UNTESTED on target file system 'btrfs' !
         
15:24:46 fstransform: WARNING: this program is tested ONLY on file systems: minix ext2 ext3 ext4 reiserfs jfs xfs
         
15:24:46 fstransform: WARNING: continuing anyway due to option '--force-untested-file-systems' (DANGEROUS)
15:24:46 fstransform: device raw size = 348535128064 bytes
15:24:46 fstransform: creating sparse loop file '/tmp/fstransform.mount.5394/.fstransform.loop.5394' inside device '/dev/nvme0n1p4'...
15:24:46 dd: 1+0 records in
15:24:46 dd: 1+0 records out
15:24:46 dd: 1 byte copied, 0.000131407 s, 7.6 kB/s
15:24:46 fstransform: device file-system block size = 4096 bytes
15:24:46 fstransform: device usable size = 348535128064 bytes
15:24:46 dd: 1+0 records in
15:24:46 dd: 1+0 records out
15:24:46 dd: 1 byte copied, 0.000102059 s, 9.8 kB/s
15:24:46 fstransform: connected loop device '/dev/loop11' to file '/tmp/fstransform.mount.5394/.fstransform.loop.5394'
15:24:46 fstransform: formatting loop device '/dev/loop11' with file-system type 'btrfs'...
15:24:46 fstransform: mounting loop device '/dev/loop11' on '/tmp/fstransform.loop.5394' ...
15:24:46 fstransform: loop device '/dev/loop11' mounted successfully.
15:24:46 fstransform: preliminary steps completed, now comes the delicate part:
15:24:46 fstransform: fstransform will move '/dev/nvme0n1p4' contents into the loop file.
         
15:24:46 fstransform: WARNING: THIS IS IMPORTANT! if either the original device '/dev/nvme0n1p4'
                      or the loop device '/dev/loop11' become FULL,
                      
                       YOU  WILL  LOSE  YOUR  DATA !
                      
                      fstransform checks for enough available space,
                      in any case it is recommended to open another terminal, type
                        watch df /dev/nvme0n1p4 /dev/loop11
                      and check that both the original device '/dev/nvme0n1p4'
                      and the loop device '/dev/loop11' are NOT becoming full.
                      if one of them is becoming full (or both),
                      you MUST stop fstransform with CTRL+C or equivalent.
                      
                      this is your chance to quit.
                      press ENTER to continue, or CTRL+C to quit: 
15:25:24 fstransform: moving '/dev/nvme0n1p4' contents into the loop file.
15:25:24 fstransform: this may take a long time, please be patient...
15:25:24 fsmove: move() skipped `/tmp/fstransform.mount.5394/.fstransform.loop.5394', matches exclude list
15:25:45 fsmove: progress: 1.5% done, 180.7 gigabytes still to move
15:25:54 fsmove: progress: 2.9% done, 178.0 gigabytes still to move, estimated 15 minutes left
15:26:07 fsmove: progress: 4.4% done, 175.3 gigabytes still to move, estimated 15 minutes left
15:26:16 fsmove: progress: 5.9% done, 172.6 gigabytes still to move, estimated 15 minutes left
15:26:21 fsmove: progress: 7.4% done, 169.9 gigabytes still to move, estimated 15 minutes left
15:26:27 fsmove: progress: 8.8% done, 167.2 gigabytes still to move, estimated 15 minutes left
15:26:33 fsmove: progress: 10.3% done, 164.5 gigabytes still to move, estimated 10 minutes left
15:26:38 fsmove: progress: 11.8% done, 161.8 gigabytes still to move, estimated 10 minutes left
15:26:46 fsmove: progress: 13.3% done, 159.1 gigabytes still to move, estimated 10 minutes left
15:26:51 fsmove: progress: 14.7% done, 156.4 gigabytes still to move, estimated 10 minutes left
15:26:56 fsmove: progress: 16.2% done, 153.7 gigabytes still to move, estimated 10 minutes left
15:27:05 fsmove: progress: 17.7% done, 151.0 gigabytes still to move, estimated  8 minutes left
15:27:10 fsmove: progress: 19.2% done, 148.3 gigabytes still to move, estimated  8 minutes left
15:27:15 fsmove: progress: 20.6% done, 145.6 gigabytes still to move, estimated  6 minutes left
15:27:30 fsmove: progress: 22.1% done, 142.9 gigabytes still to move, estimated  5 minutes left
15:27:39 fsmove: progress: 23.6% done, 140.1 gigabytes still to move, estimated  5 minutes left
15:27:44 fsmove: progress: 25.1% done, 137.4 gigabytes still to move, estimated  5 minutes left
15:27:50 fsmove: progress: 26.5% done, 134.7 gigabytes still to move, estimated  6 minutes left
15:28:00 fsmove: progress: 28.0% done, 132.0 gigabytes still to move, estimated  6 minutes left
15:28:21 fsmove: progress: 29.5% done, 129.3 gigabytes still to move, estimated  5 minutes left
15:28:26 fsmove: progress: 31.0% done, 126.6 gigabytes still to move, estimated  6 minutes left
15:28:35 fsmove: progress: 32.4% done, 123.9 gigabytes still to move, estimated  6 minutes left
15:28:49 fsmove: progress: 33.9% done, 121.2 gigabytes still to move, estimated  5 minutes left
15:28:52 fsmove: progress: 35.4% done, 118.5 gigabytes still to move, estimated  8 minutes left
15:28:58 fsmove: progress: 36.9% done, 115.8 gigabytes still to move, estimated  8 minutes left
15:29:04 fsmove: progress: 38.3% done, 113.1 gigabytes still to move, estimated  6 minutes left
15:29:09 fsmove: progress: 39.8% done, 110.4 gigabytes still to move, estimated  5 minutes left
15:29:26 fsmove: progress: 41.3% done, 107.7 gigabytes still to move, estimated  6 minutes left
15:29:44 fsmove: progress: 42.8% done, 105.0 gigabytes still to move, estimated  8 minutes left
15:29:54 fsmove: progress: 44.2% done, 102.3 gigabytes still to move, estimated  7 minutes left
15:30:02 fsmove: progress: 45.7% done,  99.6 gigabytes still to move, estimated  5 minutes left
15:30:13 fsmove: progress: 47.2% done,  96.9 gigabytes still to move, estimated  6 minutes left
15:30:22 fsmove: progress: 48.7% done,  94.2 gigabytes still to move, estimated  6 minutes left
15:30:31 fsmove: progress: 50.1% done,  91.4 gigabytes still to move, estimated  4 minutes left
15:30:42 fsmove: progress: 51.6% done,  88.7 gigabytes still to move, estimated  4 minutes left
15:30:52 fsmove: progress: 53.1% done,  86.0 gigabytes still to move, estimated  4 minutes left
15:31:06 fsmove: progress: 54.6% done,  83.3 gigabytes still to move, estimated  6 minutes left
15:31:14 fsmove: progress: 56.0% done,  80.6 gigabytes still to move, estimated  7 minutes left
15:31:19 fsmove: progress: 57.5% done,  77.9 gigabytes still to move, estimated  6 minutes left
15:31:27 fsmove: progress: 59.0% done,  75.2 gigabytes still to move, estimated  4 minutes left
15:31:32 fsmove: progress: 60.5% done,  72.5 gigabytes still to move, estimated  4 minutes left
15:31:38 fsmove: progress: 61.9% done,  69.8 gigabytes still to move, estimated  4 minutes left
15:31:45 fsmove: progress: 63.4% done,  67.1 gigabytes still to move, estimated  4 minutes left
15:31:53 fsmove: progress: 64.9% done,  64.4 gigabytes still to move, estimated  4 minutes left
15:31:58 fsmove: progress: 66.4% done,  61.7 gigabytes still to move, estimated  3 minutes left
15:32:04 fsmove: progress: 67.8% done,  59.0 gigabytes still to move, estimated  3 minutes left
15:32:12 fsmove: progress: 69.3% done,  56.3 gigabytes still to move, estimated  3 minutes left
15:32:27 fsmove: progress: 70.8% done,  53.6 gigabytes still to move, estimated  2 minutes left
15:32:33 fsmove: progress: 72.3% done,  50.9 gigabytes still to move, estimated  2 minutes left
15:32:36 fsmove: job completed.
15:32:36 fstransform: unmounting and running '/sbin/fsck' (disk check) on loop file '/tmp/fstransform.mount.5394/.fstransform.loop.5394'
15:32:39 fsck: fsck from util-linux 2.31.1
15:32:39 fstransform: disconnected loop device '/dev/loop11' from file '/tmp/fstransform.mount.5394/.fstransform.loop.5394'
15:32:39 fstransform: unmounting device '/dev/nvme0n1p4' before disk check
15:32:42 fstransform: running '/sbin/fsck' (disk check) on device '/dev/nvme0n1p4'
15:32:42 fsck: fsck from util-linux 2.31.1
15:32:42 fsck: home: Inode 3336 extent tree (at level 2) could be narrower.  IGNORED.
15:32:43 fsck: home: 12/21274624 files (0.0% non-contiguous), 36800594/85091584 blocks
15:32:43 fstransform: mounting again device '/dev/nvme0n1p4' read-only
15:32:43 fstransform: launching '/usr/sbin/fsremap' in simulated mode
15:32:43 fsremap: starting job 1, persistence data and logs are in '/var/tmp/fstransform/fsremap.job.1'
15:32:43 fsremap: if this job is interrupted, for example by a power failure,
15:32:43 fsremap: you CAN RESUME it with: /usr/sbin/fsremap -n -q --resume-job=1 -- /dev/nvme0n1p4
15:32:43 fsremap: analysis completed: 135.22 gigabytes must be relocated
15:32:45 fsremap: allocated 3.50 gigabytes RAM as memory buffer
15:32:45 fsremap: primary-storage is 7.01 gigabytes, initialized and mmapped() to contiguous RAM
15:32:45 fsremap: (simulated) starting in-place remapping. this may take a LONG time ...
15:32:45 fsremap: (simulated) progress:  2.6% done, 135.2 gigabytes still to relocate
15:32:45 fsremap: (simulated) progress: 69.0% done,  45.4 gigabytes still to relocate
15:32:45 fsremap: (simulated) clearing 1.38 gigabytes free-space from device ...
15:32:45 fsremap: (simulated) job completed.
15:32:45 fstransform: launching '/usr/sbin/fsremap' in REAL mode to perform in-place remapping.
15:32:45 fsremap: starting job 2, persistence data and logs are in '/var/tmp/fstransform/fsremap.job.2'
15:32:45 fsremap: if this job is interrupted, for example by a power failure,
15:32:45 fsremap: you CAN RESUME it with: /usr/sbin/fsremap -q --resume-job=2 -- /dev/nvme0n1p4
15:32:45 fsremap: analysis completed: 135.22 gigabytes must be relocated
15:32:46 fsremap: allocated 3.50 gigabytes RAM as memory buffer
15:32:49 fsremap: primary-storage is 7.01 gigabytes, initialized and mmapped() to contiguous RAM
15:32:49 fsremap: successfully unmounted device '/dev/nvme0n1p4'
15:32:49 fsremap: everything ready for in-place remapping, this is your LAST chance to quit.
15:32:49 fsremap: WARN: press ENTER to proceed, or CTRL+C to quit

15:33:32 fsremap: starting in-place remapping. this may take a LONG time ...
15:33:43 fsremap: progress: 2.6% done, 135.2 gigabytes still to relocate
15:36:29 fsremap: progress: 69.0% done,  45.4 gigabytes still to relocate, estimated  1 minute and 20 seconds left
15:37:43 fsremap: clearing 1.38 gigabytes free-space from device ...
15:41:25 fsremap: job completed.
15:41:28 fstransform: running again '/sbin/fsck' (disk check) on device '/dev/nvme0n1p4'
15:41:28 fsck: fsck from util-linux 2.31.1
15:41:28 fstransform: completed successfully. device '/dev/nvme0n1p4' now contains 'btrfs' file-system
```

转换完毕后挂载随便看几个文件看是不是正常，一般是OK的，然后改一下挂载参数
`/etc/fstab`

```shell
UUID=361c83ca-fa86-417a-96ce-29569c9bc98e /home   btrfs ssd,noatime,subvol=/   0
   0
```

下一步再搞一下透明压缩（用lzo算法）：

`btrfs filesystem defragment -v -clzo /mountpoint`

注意这是压缩已有文件。如果要真正的“实时透明压缩”请在挂载参数上加`compress-force=lzo`，这样存进去的文件都会被压缩了。

玩一玩子卷`subvolume`

新建只读子卷，当做备份

`sudo btrfs subvolume snapshot -r /@ /@backup`

若干天后可能胡折腾系统挂了，需要还原

```shell
1. 删除原来启动的子卷
sudo btrfs subvolume delete /@
2. 从原来备份的子卷再建一个同名子卷
sudo btrfs subvolume snapshot /@backup /@
```

所有更改就又回来了

BTRFS大法好!