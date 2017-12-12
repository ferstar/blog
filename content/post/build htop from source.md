---
title: "build htop from source"
date: "2016-06-16T03:58:00+08:00"
tags: ['OTHERS']
comments: 
---


```
mkdir -p /prodata/tmp
cd /prodata/tmp
wget http://hisham.hm/htop/releases/1.0.3/htop-1.0.3.tar.gz
tar -xvf htop-1.0.3.tar.gz
cd htop-1.0.3
./configure --prefix=/prodata/ngs
make -j12
make install
```
运行良好


