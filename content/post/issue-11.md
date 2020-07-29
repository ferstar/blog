---
title: "Ubuntu优化"
date: "2020-01-02T11:29:24+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-01-02T11:29:24+08:00

> update_date: 2020-05-07T08:17:10+08:00

> comment_url: https://github.com/ferstar/blog/issues/11

## 1. 关闭错误报告

> 可以选择直接卸载`apport`这个软件包, 但最好还是改配置

```shell
# 看说明
sudo vi /etc/default/apport
```

> 贴个图

![DeepinScreenshot_select-area_20200102193713](https://user-images.githubusercontent.com/2854276/71665297-49d18180-2d97-11ea-81d5-ce927479c346.png)

## 2.关于根分区文件系统的选择

> `ext4`老当益壮，选他没错

> `btrfs`真香, subvolume很赞!

拿了个64GB的U盘（因为我想搞个Ubuntu2GO的东东）跑了下分：

跑分代码如下，哪抄的忘了，就是随机建大量小文件，然后再写&读，看耗时多少

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

filecount = 30000
filesize = 1024


import random, time
from os import system
flush = "sudo su -c 'sync ; echo 3 > /proc/sys/vm/drop_caches'"

randfile = open("/dev/urandom", "r")

print "\ncreate test folder:"
starttime = time.time()
system("rm -rf test && mkdir test")
print time.time() - starttime
system(flush)

print "\ncreate files:"
starttime = time.time()
for i in xrange(filecount):
    rand = randfile.read(int(filesize * 0.5 + filesize * random.random()))
    outfile = open("test/" + unicode(i), "w")
    outfile.write(rand)
print time.time() - starttime
system(flush)

print "\nrewrite files:"
starttime = time.time()
for i in xrange(int(filecount / 10)):
    rand = randfile.read(int(filesize * 0.5 + filesize * random.random()))
    outfile = open("test/" + unicode(int(random.random() * filecount)), "w")
    outfile.write(rand)
print time.time() - starttime
system(flush)

print "\nread linear:"
starttime = time.time()
for i in xrange(int(filecount / 10)):
    infile = open("test/" + unicode(i), "r")
    outfile.write(infile.read());
print time.time() - starttime
system(flush)

print "\nread random:"
starttime = time.time()
outfile = open("/dev/null", "w")
for i in xrange(int(filecount / 10)):
    infile = open("test/" + unicode(int(random.random() * filecount)), "r")
    outfile.write(infile.read());
print time.time() - starttime
system(flush)

print "\ndelete all files:"
starttime = time.time()
system("rm -rf test")
print time.time() - starttime
system(flush)
```

U盘被我格成这样：

```shell
# sudo gdisk -l /dev/sda
Disk /dev/sda: 124822487 sectors, 59.5 GiB
Model: ROS2GO          
Sector size (logical/physical): 512/512 bytes
Disk identifier (GUID): B3D0C73A-433D-44C1-8F80-FA90167AAADC
Partition table holds up to 128 entries
Main partition table begins at sector 2 and ends at sector 33
First usable sector is 34, last usable sector is 124822453
Partitions will be aligned on 2048-sector boundaries
Total free space is 1942420 sectors (948.4 MiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048        20482047   9.8 GiB     8300  ext4
   2        20482048        40962047   9.8 GiB     8300  btrfs
   3        40962048        61442047   9.8 GiB     8300  f2fs
   4        61442048        81922047   9.8 GiB     8300  xfs
   5        81922048       102402047   9.8 GiB     8300  reiserfs
```

各分区挂载参数均是Ubuntu系统默认参数

```shell
f2fs (rw,nosuid,nodev,relatime,lazytime,background_gc=on,discard,no_heap,user_xattr,inline_xattr,acl,inline_data,inline_dentry,flush_merge,extent_cache,mode=adaptive,active_logs=6,alloc_mode=reuse,fsync_mode=posix,uhelper=udisks2)
btrfs (rw,nosuid,nodev,relatime,space_cache,subvolid=5,subvol=/,uhelper=udisks2)
ext4 (rw,nosuid,nodev,relatime,uhelper=udisks2)
xfs (rw,nosuid,nodev,relatime,attr2,inode64,logbufs=8,logbsize=32k,noquota,uhelper=udisks2)
reiserfs (rw,nosuid,nodev,relatime,uhelper=udisks2)
```

测试机系统：

![DeepinScreenshot_select-area_20200110101815](https://user-images.githubusercontent.com/2854276/72120333-9f5aef00-3392-11ea-9e2e-131115439826.png)

内核版本：

`Linux xiaoxinpro 5.3.0-24-generic #26-Ubuntu SMP Thu Nov 14 01:33:18 UTC 2019 x86_64 x86_64 x86_64 GNU/Linux
`

跑分结果：

|          | create files | rewrite files | read linear | read random | delete all files |
| -------- | ------------ | ------------- | ----------- | ----------- | ---------------- |
| ext4     | 0.593394041  | 3.646025896   | 0.960836887 | 2.286855936 | 0.646140814      |
| btrfs    | 5.707916975  | 2.0158391     | 0.446825027 | 2.039553881 | 2.933115005      |
| f2fs     | 0.737277031  | 2.216201067   | 0.841583014 | 2.216186047 | 17.70262408      |
| xfs      | 0.781413078  | 5.908052206   | 1.212768078 | 3.198234081 | 4.744434118      |
| reiserfs | 1.735713959  | 1.866363049   | 0.23438096  | 1.559979916 | 2.575639963      |

![bench](https://user-images.githubusercontent.com/2854276/72119789-92d59700-3390-11ea-80c3-b3af0b1f83f7.png)

对于系统性能影响最大的应该是随机读写，这么看来还是`reiserfs`牛逼，几乎全面领先，可惜这货作者杀老婆，进局子了，但并不妨碍我用脚投票，~~选`reiserfs`做根分区文件系统~~，然并卵，Ubuntu用这货做根分区丢资料，放弃。剩下的，`ext4`还是老当益壮，`btrfs`也可以，`xfs`则并没有如网传那样犀利，`f2fs`删除文件居然那么慢。

## 3. TLP - Linux电源优化利器

> via: https://linrunner.de/en/tlp/docs/tlp-linux-advanced-power-management.html

> 有人说跟`powertop`搭配可能效果更好，然而我不觉得，这两货一起用卡的要死，所以只留一个就好

> btrfs 文件系统的话, 需要改个东西

```shell
# AHCI link power management (ALPM) for disk devices:
#   min_power, med_power_with_dipm(*), medium_power, max_performance.
# (*) Kernel >= 4.15 required, then recommended.
# Multiple values separated with spaces are tried sequentially until success.
# Default:
#  - "med_power_with_dipm max_performance" (AC)
#  - "med_power_with_dipm min_power" (BAT)

SATA_LINKPWR_ON_AC="med_power_with_dipm max_performance"
SATA_LINKPWR_ON_BAT="med_power_with_dipm max_performance"
```

## 4. 要不要`swap`分区

我倾向于不要，万一想要`swap`了完全可以用`swapfile`的形式随用随开

Archlinux Wiki的[文档真是优秀](https://wiki.archlinux.org/index.php/Swap#Swap_file)

摘抄几个命令

#### Swap file creation

For copy-on-write file systems like [Btrfs](https://wiki.archlinux.org/index.php/Btrfs), first create a zero length file, set the `No_COW` attribute on it with [chattr](https://wiki.archlinux.org/index.php/Chattr), and make sure compression is disabled:

```
# truncate -s 0 /swapfile
# chattr +C /swapfile
# btrfs property set /swapfile compression none
```

See [Btrfs#Swap file](https://wiki.archlinux.org/index.php/Btrfs#Swap_file) for more information.

Use `fallocate` to create a swap file the size of your choosing (M = [Mebibytes](https://en.wikipedia.org/wiki/Mebibyte), G = [Gibibytes](https://en.wikipedia.org/wiki/Gibibyte)). For example, creating a 512 MiB swap file:

```
# fallocate -l 512M /swapfile
```

**Note:** *fallocate* may cause problems with some file systems such as [F2FS](https://wiki.archlinux.org/index.php/F2FS).[[1\]](https://github.com/karelzak/util-linux/issues/633) As an alternative, using *dd* is more reliable, but slower:

```
# dd if=/dev/zero of=/swapfile bs=1M count=512 status=progress
```

Set the right permissions (a world-readable swap file is a huge local vulnerability):

```
# chmod 600 /swapfile
```

After creating the correctly sized file, format it to swap:

```
# mkswap /swapfile
```

Activate the swap file:

```
# swapon /swapfile
```

Finally, edit the fstab configuration to add an entry for the swap file:

```
/etc/fstab
/swapfile none swap defaults 0 0
```

For additional information, see [fstab#Usage](https://wiki.archlinux.org/index.php/Fstab#Usage).

**Note:** The swap file must be specified by its location on the file system not by its UUID or LABEL.

#### Remove swap file

To remove a swap file, it must be turned off first and then can be removed:

```
# swapoff /swapfile
# rm -f /swapfile
```

---

> 关于性能也抄几句，我给`vm.swappiness`配了`1`

## Performance

Swap operations are usually significantly slower than directly accessing data in RAM. Disabling swap entirely to improve performance can sometimes lead to a degradation, since it decreases the memory available for VFS caches, causing more frequent and costly disk I/O.

Swap values can be adjusted to help performance:

### Swappiness

The *swappiness* [sysctl](https://wiki.archlinux.org/index.php/Sysctl) parameter represents the kernel's preference (or avoidance) of swap space. Swappiness can have a value between 0 and 100, the default value is 60. A low value causes the kernel to avoid swapping, a higher value causes the kernel to try to use swap space. Using a low value on sufficient memory is known to improve responsiveness on many systems.

To check the current swappiness value:

```
$ sysctl vm.swappiness
```

Alternatively, the files `/sys/fs/cgroup/memory/memory.swappiness` or `/proc/sys/vm/swappiness` can be read in order to obtain the raw integer value.

**Note:** As `/proc` is a lot less organized and is kept only for compatibility purposes, you are encouraged to use `/sys` instead.

To temporarily set the swappiness value:

```
# sysctl -w vm.swappiness=10
```

To set the swappiness value permanently, create a [sysctl.d(5)](https://jlk.fjfi.cvut.cz/arch/manpages/man/sysctl.d.5) configuration file. For example:

```
/etc/sysctl.d/99-swappiness.conf
vm.swappiness=10
```

To test and more on why this may work, take a look at [this article](http://rudd-o.com/en/linux-and-free-software/tales-from-responsivenessland-why-linux-feels-slow-and-how-to-fix-that).

## 5. 常用软件

- Google Chrome/Chromium

支持的一些启动参数如下所示，我一般用的是`--disk-cache-dir=/tmp/chrome_cache --process-per-site`，即缓存扔到`/tmp`分区，每个站点使用一个进程

对于Chromium，可以在`/etc/chromium-browser/default`添加自己想要的配置参数，而对于Google Chrome，貌似只能从这里`/usr/share/applications/chromium-browser.desktop`加

```shell
--user-data-dir="[PATH]"  自定义用户数据目录
--start-maximized                启动就最大化
--no-sandbox                         取消沙盒模式
--single-process                    单进程运行
--process-per-tab                 每个标签使用单独进程
--process-per-site                每个站点使用单独进程
--in-process-plugins            插件不启用单独进程
--disable-popup-blocking 禁用弹出拦截
--disable-javascript             禁用JavaScript
--disable-java                         禁用Java
--disable-plugins                   禁用插件
--disable-images                   禁用图像
-incognito                               启动进入隐身模式
--enable-udd-profiles        启用账户切换菜单
--proxy-pac-url                   使用pac代理 [via 1/2]
--lang=zh-CN                        设置语言为简体中文
--disk-cache-dir="[PATH]" 自定义缓存目录
--disk-cache-size=              自定义缓存最大值（单位byte）
--media-cache-size=         自定义多媒体缓存最大值（单位byte）
--bookmark-menu              在工具栏增加一个书签按钮
--enable-sync                       启用书签同步
```

- Foxit Reader

> 安装方法见：https://websiteforstudents.com/how-to-install-foxit-reader-on-ubuntu-16-04-17-10-18-04-desktop/

- Barrier 在Linux和其他设备之间共享键盘和鼠标

> 我是从snap安装的，挺方便，务必带好梯子

> https://snapcraft.io/barrier

- FlameShot - 火焰截图

- DeepinTerminal - 深度终端

- CopyQ - 剪贴板增强

- Qv2ray - 梯子客户端

- Typora - MarkDown编辑器