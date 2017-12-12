---
title: "centos 6.x 升级python版本"
date: "2016-06-07T10:23:00+08:00"
tags: ['OTHERS']
comments: 
---


> centos 6.x自带python版本是2.6.6, 实在太老, 需要稍微更新一下
## 更新系统(开发工具集)
    yum -y update
    yum groupinstall -y 'development tools'
## 源码安装py2
    wget https://www.python.org/ftp/python/2.7.11/Python-2.7.11.tar.xz
    xz -d Python-2.7.11.tar.xz && tar xvf Python-2.7.11.tar
## 编译详情
    # 进入目录:
    cd Python-2.7.11
    # 运行配置 configure:
    ./configure --prefix=/home/ferstar/software
    # 编译安装(机器有12个核心, 所以我加了-j12参数, 加速make过程):
    make -j12
编译过程出现下面的错误
> Python build finished, but the necessary bits to build these modules were not found:
> bsddb185  dl  imageop  sunaudiodev

Google一番发现这几个模块在centos上是不必要的, 所以可以忽略

    make install
    # 也可以使用 make altinstall命令安装, 这样在生成的python二进制文件末尾会带上版本号
    # 环境变量
    vi ~/.bashrc
    export PATH="$HOME/software:$PATH"
    source ~/.bashrc
    # 测试一下
    python --version
    # 正常显示
    Python 2.7.11
    
## 安装setuptools

从这里下载源码
<https://pypi.python.org/pypi/setuptools#advanced-installation>

    tar xvzf setuptools-22.0.5.tar.gz
    cd setuptools-22.0.5
    python setup.py install
    
## 安装pip

下载源码<https://pypi.python.org/pypi/pip>

    tar xvzf pip-8.1.2.tar.gz
    cd pip-8.1.2
    python setup.py install
    
## 使用阿里镜像加速pip下载
见<http://mirrors.aliyun.com/help/pypi>
