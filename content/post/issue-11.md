---
title: "Ubuntu优化"
date: "2020-01-02T11:29:24+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-01-02T11:29:24+08:00

> update_date: 2020-01-08T04:07:50+08:00

> comment_url: https://github.com/ferstar/blog/issues/11

##### 1. 关闭错误报告

> 可以选择直接卸载`apport`这个软件包, 但最好还是改配置

```shell
# 看说明
sudo vi /etc/default/apport
```

> 贴个图

![DeepinScreenshot_select-area_20200102193713](https://user-images.githubusercontent.com/2854276/71665297-49d18180-2d97-11ea-81d5-ce927479c346.png)

##### 2.关于文件系统的选择

> 一句话，机械用`ext4`，固态用`btrfs` 或`xfs` 

fstab配置

```shell
UUID=159417ca-b0d4-40a0-aa51-6829ac259a2f /               ext4    defaults,noatime,commit=120,barrier=0,errors=remount-ro 0       0
```

## 3. TLP - Linux电源优化利器

> via: https://linrunner.de/en/tlp/docs/tlp-linux-advanced-power-management.html

> 有人说跟`powertop`搭配可能效果更好，然而我不觉得，这两货一起用卡的要死，所以只留一个就好

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