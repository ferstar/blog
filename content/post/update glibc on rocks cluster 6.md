---
date = "2016-06-16T02:49:00+08:00"
title = "update glibc on rocks cluster 6.2"
tags = ['OTHERS']
---

运行snap-aligner提示需要glibc 2.14, 然而集群系统自带版本是2.12, 所以需要升级, 考虑到系统稳定性, 决定找个别的地方编译升级之
```
snap-aligner: /lib64/libc.so.6: version `GLIBC_2.14' not found (required by snap-aligner)
```
## 下载
`wget http://ftp.gnu.org/gnu/glibc/glibc-2.14.tar.gz`
## 编译
```
tar -zxvf glibc-2.14.tar.gz
cd glibc-2.14
mkdir build
cd build
../configure --prefix=/prodata/ngs/glibc-2.14
make -j12
make install
```
## 错误处理
1. 缺`ld.so.conf`

```
/prodata/tmp/glibc-2.14/build/elf/ldconfig: Can't open configuration file /prodata/ngs/glibc-2.14/etc/ld.so.conf: No such file or directory
```
找找看系统里面有没有`find / -type f -iname "ld.so.conf"`
嗯, 很好, 系统里面有, 搬过去`cp /etc/ld.so.conf /prodata/ngs/glibc-2.14/etc/ld.so.conf`
然后再`make install`搞定

## 指定动态库的查找路径
方法一： export LD_LIBRARY_PATH=LD_LIBRARY_PATH:/XXX 但是登出后就失效
方法二： 修改~/.bashrc或~/.bash_profile或系统级别的/etc/profile
1. 在其中添加例如export PATH=/opt/ActiveP/lib:$LD_LIBRARY_PATH
2. source .bashrc  (Source命令也称为“点命令”，也就是一个点符号（.）。source命令通常用于重新执行刚修改的初始化文件，使之立即生效，而不必注销并重新登录)
方法三：这个没有修改LD_LIBRARY_PATH但是效果是一样的实现动态库的查找， 
1. /etc/ld.so.conf下面加一行/usr/local/lib
2. 保存过后ldconfig一下（ldconfig 命令的用途,主要是在默认搜寻目录(/lib和/usr/lib)以及动态库配置文件/etc/ld.so.conf内所列的目录下,搜索出可共享的动态链接库(格式如前介绍,lib*.so*),进而创建出动态装入程序(ld.so)所需的连接和缓存文件.缓存文件默认为/etc/ld.so.cache,此文件保存已排好序的动态链接库名字列表.）
在rocks cluster 6.2的实际情况是方法三并无效果, 所以采用了方法二
具体做法:
```
vi ~/.bashrc
# 加一行
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/prodata/ngs/glibc-2.14/lib
# 保存退出
source ~/.bashrc
```
## 正常运行
`snap-aligner`
```
Welcome to SNAP version 1.0beta.18.

Usage: snap <command> [<options>]
Commands:
   index    build a genome index
   single   align single-end reads
   paired   align paired-end reads
   daemon   run in daemon mode--accept commands remotely
Type a command without arguments to see its help.
```
## 奇怪的错误
`snap-aligner index nt COMP_SNAP -locationSize 8 -t48`
```
Computed bias table in 222s
Allocating memory for hash tables...terminate called after throwing an instance of 'std::bad_alloc'
  what():  std::bad_alloc
Aborted
```