---
title: "Odroid ROS镜像封装记录"
date: "2015-12-17T13:58:38+08:00"
tags: ['ODROID', 'ROS', 'LINUX']
comments: true
---

棒子的这板子比树莓派2犀利了那么一点, 具体型号是`odroid-XU4`

## 备份镜像

查看内存卡分区

```
df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb2        14G  5.9G  7.7G  44% /media/ferstar/trusty
/dev/sdb1       129M  5.1M  124M   4% /media/ferstar/BOOT
```

备份

```
sudo dd if=/dev/sdb of=~/odroid/o_ros.img
```

md5

```
md5sum o_ros.img > o_ros.img.md5sum
```

## 修改分区

均使用`gparted`工具完成操作

### 添加swap

`sudo gparted /dev/sdb`如图

![分区概览][1]

缩小根分区, 留2G给swap

![缩小根分区][2]

建立swap分区

![建立swap分区][3]

### 更改根分区格式(f2fs)

同样操作, 动动鼠标而已, 只是gparted对f2fs支持不是很完美, 格式化完成后分区显示不正常
如图
![整个分区细节][4]

### 恢复原`/`分区内容

挂载之前备份的镜像`o_ros.img`

检查镜像信息

```
fdisk -l o_ros.img

Disk o_ros.img: 14.5 GiB, 15523119104 bytes, 30318592 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x000c4046

Device     Boot  Start      End  Sectors   Size Id Type
o_ros.img1        3072   266239   263168 128.5M  6 FAT16
o_ros.img2      266240 30317568 30051329  14.3G 83 Linux
```

挂载此镜像`/`分区

```
mkdir root
sudo mount -o loop,offset=136314880 o_ros.img root
# 其中偏移量(offset)是根据上面镜像信息的起点(266240)乘以单元数(512)得到
```

拷贝所有`/`内容到新的f2fs分区

```
mkdir f2fs
sudo mount /dev/sdb2 f2fs
sudo cp -a root/* f2fs
# 注意 -a 这个参数必须要加上
```

## 配置分区参数

查看UUID
`sudo blkid /dev/sdb*`

```
/dev/sdb: PTUUID="000c4046" PTTYPE="dos"
/dev/sdb1: SEC_TYPE="msdos" LABEL="BOOT" UUID="6E35-5356" TYPE="vfat" PARTUUID="000c4046-01"
/dev/sdb2: UUID="b1aa5440-7e59-40d1-ab11-0b9659ca3210" TYPE="f2fs" PARTUUID="000c4046-02"
/dev/sdb3: LABEL="swap" UUID="a6e99b01-86d1-4615-a2e0-fc424a452cd8" TYPE="swap" PARTUUID="000c4046-03"
```

更改`fstab`
```
# UNCONFIGURED FSTAB FOR BASE SYSTEM                               
                                                                   
# UUID=e139ce78-9841-40fe-8823-96a304a09859 /   ext4    errors=remount-ro,noatim
UUID=b1aa5440-7e59-40d1-ab11-0b9659ca3210 / f2fs    errors=remount-ro,defaults,noatime,discard 0 1
UUID=6E35-5356  /media/boot vfat    defaults,rw,owner,flush,umask=000   0 0 
UUID=a6e99b01-86d1-4615-a2e0-fc424a452cd8 swap swap defaults 0 0                
tmpfs       /tmp    tmpfs   nodev,nosuid,mode=1777          0 0
```

更改`boot.ini`

`root=UUID`部分替换为格式化后的新`uuid=b1aa5440-7e59-40d1-ab11-0b9659ca3210`

## tf卡插入重启看效果

杯具了~~~系统一跪不起, 查了下文档, odroid kenerl还没加入`f2fs`的驱动支持, 顿时感到世界深深的恶意...

还好有备份, 刷回云云不提

## 备份备份备份说三遍...

[1]: http://7xivdp.com1.z0.glb.clouddn.com/png/2015/12/c15a5e9d656e25f165fc8a59315d47e3.png/xyz
[2]: http://7xivdp.com1.z0.glb.clouddn.com/png/2015/12/3175234083078b49ffed03ec3c09ab4f.png/xyz
[3]: http://7xivdp.com1.z0.glb.clouddn.com/png/2015/12/dc42631e1bf2c7400011b39d72fad3cd.png/xyz
[4]: http://7xivdp.com1.z0.glb.clouddn.com/png/2015/12/54316ff659ae38fbf35ae530a38525d9.png/xyz