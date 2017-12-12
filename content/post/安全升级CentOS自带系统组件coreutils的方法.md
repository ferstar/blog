---
title: "安全升级CentOS自带系统组件coreutils的方法"
date: "2016-09-04T15:28:00+08:00"
tags: ['OTHERS']
comments: 
---


集群系统版本比较低, CentOS 6.6, 自带的一些比如`sort`命令, 不支持`parallel`参数, 所以需要小升级一下
```
#!/bin/sh

wget http://ftp.gnu.org/gnu/coreutils/coreutils-8.25.tar.xz
tar xfv coreutils-8.25.tar.xz
cd coreutils-8.25

FORCE_UNSAFE_CONFIGURE=1 ./configure \
            --prefix=/usr            \
            --libexecdir=/usr/lib    \
            --enable-no-install-program=kill,uptime
 
make -j48
make install

yes | mv -v /usr/bin/{cat,chgrp,chmod,chown,cp,date,dd,df,echo,head,sleep,nice,false,ln,ls,mkdir,mknod,mv,pwd,rm,rmdir,stty,sync,true,uname,test,[} /bin
yes | mv -v /usr/bin/chroot /usr/sbin
yes | mv -v /usr/share/man/man1/chroot.1 /usr/share/man/man8/chroot.8
sed -i s/\"1\"/\"8\"/1 /usr/share/man/man8/chroot.8
```
