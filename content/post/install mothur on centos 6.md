---
title: "install mothur on centos 6.6"
date: "2016-07-19T17:03:00+08:00"
tags: ['OTHERS']
comments: true
---


> 以下皆为历史, 开始拥抱`conda`
[NGS解放生产力工具--Miniconda&Bioconda](http://0ne.farbox.com/post/ngs/ngsjie-fang-sheng-chan-li-gong-ju-miniconda-bioconda)

这玩意最新版依赖的g++库版本太高, 升级贼麻烦, 所以退而求其次, 找个略旧的版本build from source吧

`wget https://codeload.github.com/mothur/mothur/tar.gz/v1.35.0 -O mothur.zip`

下载后解压, 先make, 出错, 什么arch不对云云
所以查看下makefile, 发现这个makefile写的蛮有爱, 按照机器需求小改如下
```
ifeq  ($(strip $(64BIT_VERSION)),yes)
    #if you are using centos uncomment the following lines
    CXX = g++

    #if you are a mac user use the following line
    #TARGET_ARCH += -arch x86_64

    #if you using cygwin to build Windows the following line
    #CXX = x86_64-w64-mingw32-g++
    #CC = x86_64-w64-mingw32-g++
    #FORTAN_COMPILER = x86_64-w64-mingw32-gfortran
    #TARGET_ARCH += -m64 -static

    #if you are a linux user use the following line
    CXXFLAGS += -mtune=native -march=native

    CXXFLAGS += -DBIT_VERSION
    FORTRAN_FLAGS = -m64
endif
```
改完保存, make -j12, 成功生成二进制文件mothur和uchime, 随便拖到哪里都可以用了, 当然必须是要指定PATH的