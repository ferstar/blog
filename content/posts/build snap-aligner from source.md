---
title: "build snap-aligner from source"
slug: "build-snap-aligner-from-source"
date: "2016-06-16T05:27:00+08:00"
tags: ['OTHERS']
comments: true
---


运行网上现成的binary程序总是 报这么个错:
`snap-aligner index nt COMP_SNAP -locationSize 8 -t48`
```
Computed bias table in 222s
Allocating memory for hash tables...terminate called after throwing an instance of 'std::bad_alloc'
  what():  std::bad_alloc
Aborted
```
似乎是个内存泄漏的错误, 然而老夫内存大大滴, 1TB, Google一番发现原来如果内存碎片过多, 即使内存够用, 也有可能出现无法分配的情况。没的说，只能重新编译咯
```
git clone https://github.com/amplab/snap.git
# 发现需要 g++ > 4.6 zlib 1.2.8
# 苦逼的集群系统组件都太老......
```
## build g++ from source
看了下源码体积, 想想还是找找好心人打包好的rpm包比较现实
<http://superuser.com/questions/381160/how-to-install-gcc-4-7-x-4-8-x-on-centos>
然而身在天朝直连这个http://people.centos.org鸟网似乎很悲剧, 自带yum升级总是下载失败, 好吧, 只能挂代理先把需要的东西下载下来然后再传到集群然后再手动安装...
<http://people.centos.org/tru/devtools-1.1/6/x86_64/RPMS/>
东西都在上面的那个网址, 发动ctrl+f大法下载, 总共需要这么5个包
```
devtoolset-1.1-gcc-4.7.2-5.el6.x86_64.rpm
devtoolset-1.1-gcc-c4.7.2-5.el6.x86_64.rpm
devtoolset-1.1-libstdc++-devel-4.7.2-5.el6.x86_64.rpm
devtoolset-1.1-runtime-1-13.el6.noarch.rpm
scl-utils-build-20120927-2.el6_4.6.centos.x86_64.rpm
```
折腾完安装
`yum install *.rpm`
然后需要配置编译环境变量(系统默认的不敢动)
```
export CC=/opt/centos/devtoolset-1.1/root/usr/bin/gcc  
export CPP=/opt/centos/devtoolset-1.1/root/usr/bin/cpp
export CXX=/opt/centos/devtoolset-1.1/root/usr/bin/c++
```
## build zlib from source
这个似乎没多大必要
```
wget http://zlib.net/zlib-1.2.8.tar.gz
tar xvzf zlib-1.2.8.tar.gz
cd zlib-1.2.8
./configure --prefix=/prodata/ngs
make -j12 && make install
```
## 开心的make snap
```
make
mv snap-aligner /prodata/ngs/bin/
```
## 测试
`nohup snap-aligner index nt COMP_SNAP -locationSize 8 -t48 > test.log &`
## 扑街
```
Allocating memory for hash tables...terminate called after throwing an instance of 'std::bad_alloc'
  what():  std::bad_allocstd::bad_alloc
```
