---
date = "2016-07-01T11:29:00+08:00"
title = "How to upgrade coreutils to latest version without breaking anything.(from"
tags = ['OTHERS']

---

很蛋疼的问题, 联想x6的机器太挑系统, 今天换了个rhel6.5似乎略稳定, 在更换了centos的源以后, 发现自带的yum软件包还是太老, sort命令还是不支持parallel选项, 没办法只有build from source这条路走了, 以下是过程

The base of these instructions was derived from the excellent LinuxFromScratch.org (link is external)--which basically shows you how to safely upgrade your coreutils.

Here we go....

Download the latest version from here: http://ftp.gnu.org/gnu/coreutils/ (link is external)

```
cd /usr/local/src
wget http://ftp.gnu.org/gnu/coreutils/coreutils-8.22.tar.xz
tar xfv coreutils-8.22.tar.xz
cd coreutils-8.22
```
This is key. We make sure to put everything in /usr/bin instead of /bin. -- i.e. so we don't run into compile problems if some of the coreutils are being used

```
FORCE_UNSAFE_CONFIGURE=1 ./configure \
            --prefix=/usr            \
            --libexecdir=/usr/lib    \
            --enable-no-install-program=kill,uptime
 
make
make install
```
Now we move what we installed in /usr/bin to /bin overwritting the old coreutils with new.
```
yes | mv -v /usr/bin/{cat,chgrp,chmod,chown,cp,date,dd,df,echo,head,sleep,nice,false,ln,ls,mkdir,mknod,mv,pwd,rm,rmdir,stty,sync,true,uname,test,[} /bin
yes | mv -v /usr/bin/chroot /usr/sbin
yes | mv -v /usr/share/man/man1/chroot.1 /usr/share/man/man8/chroot.8
sed -i s/\"1\"/\"8\"/1 /usr/share/man/man8/chroot.8
```
装完后发现其实 sort 还是原来的sort 新的在/usr/bin下面, 没办法, 只好人肉改下调用sort命令的路径了