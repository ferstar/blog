---
title: "源//ROS on RaspBerry Pi2"
date: "2015-08-31T22:51:20+08:00"
tags: ['OTHERS']
comments: 
---

首先按照下面的连接在树莓派上安装ubuntu
[1. Raspberry Pi 2 (with Ubuntu 14.04.2 2015-04-06)][1]
[2. Ubuntu ARM install of ROS Indigo][2]
> 需要注意的是链接里提供的镜像是基本的系统，展开只有2G不到，而拿来做开发的话，tf卡至少都在8G以上，剩下没有使用的空间可以在PC系统安装gparted，把写好的卡第二分区resize一下就可以了。

因为是port源，所以mirror站点几乎没有，找到个比主站稍快点的一个

注意：`libraspberrypi-dev`这个包不要安装，装了会影响到后续ros环境的编译，万一手欠装了，出错的时候`apt-get`是没法卸载的，那时候用`dpkg --remove libraspberrypi-dev`卸载，当然root权限是必须的

<!--more-->


```
#备份是个好习惯
sudo -i
cp /etc/apt/sources.list /etc/apt/sources.list.bak
vi /etc/apt/sources.list
```
如下内容：
```
# See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
# newer versions of the distribution.

deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty main restricted
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty main restricted

## Major bug fix updates produced after the final release of the
## distribution.
deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-updates main restricted
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-updates main restricted

## Uncomment the following two lines to add software from the 'universe'
## repository.
## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
## team. Also, please note that software in universe WILL NOT receive any
## review or updates from the Ubuntu security team.
deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty universe multiverse
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty universe multiverse
deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-updates universe multiverse
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-updates universe multiverse

## N.B. software from this repository may not have been tested as
## extensively as that contained in the main release, although it includes
## newer versions of some applications which may provide useful features.
## Also, please note that software in backports WILL NOT receive any review
## or updates from the Ubuntu security team.
deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-backports main restricted
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-backports main restricted

deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-security main restricted
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-security main restricted
deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-security universe
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-security universe
deb http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-security multiverse
deb-src http://ftp.tu-chemnitz.de/pub/linux/ubuntu-ports/ trusty-security multiverse
```
附加：
======
新发现湾湾的两个源里有port源可以用，速度不错
[http://free.nchc.org.tw/ubuntu-ports/][3]
[http://ftp.ubuntu-tw.org/mirror/ubuntu-ports/dists/][4]

[1]: https://wiki.ubuntu.com/ARM/RaspberryPi
[2]: http://wiki.ros.org/indigo/Installation/UbuntuARM
[3]: http://free.nchc.org.tw/ubuntu-ports/
[4]: http://ftp.ubuntu-tw.org/mirror/ubuntu-ports/dists/
