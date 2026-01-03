---
title: "为知笔记在Ubuntu 18.04上的编译过程"
slug: "wiznote-ubuntu-compile-process"
date: "2020-02-18T02:14:03+08:00"
tags: ['Linux']
comments: true
---

> created_date: 2020-02-18T02:14:03+08:00

> update_date: 2020-02-18T02:21:06+08:00

> comment_url: https://github.com/ferstar/blog/issues/17

- 装Qt，注意安装的时候要选择桌面开发环境，默认没有选

http://mirrors.ustc.edu.cn/qtproject/archive/qt/5.9/5.9.0/qt-opensource-linux-x64-5.9.0.run

- 安装一坨依赖
```shell
sudo apt-get install git build-essential cmake zlib1g-dev extra-cmake-modules fcitx-libs-dev mesa-common-dev libjasper-dev libxkbcommon-dev
```

- 克隆源码到本地
```shell
cd ~
mkdir WizTeam
cd WizTeam
git clone https://github.com/ferstar/WizQTClient.git
cd WizQTClient
git checkout 2.8.2
```

- 编译fcitx-qt5解决中文输入问题
```shell
git clone https://github.com/fcitx/fcitx-qt5.git
cd fcitx-qt5 
cmake .
make 
sudo make install
# 拷贝platforminputcontext/libfcitxplatforminputcontextplugin.so到Qt安装目录的Tools/QtCreator/lib/Qt/plugins/platforminputcontexts目录内
```

- 编译打包
```shell
chmod a+x linuxdeployqt
export PATH="$HOME/Qt5.9.0/5.9/gcc_64/bin":$PATH
./linux-package.sh
```

- 无法登录的问题

以上步骤成功完成后会生成一个AppImage文件，双击即可运行，但登录会报错`Failed to exec json request, network error=99, message=`
Google一番发现是openssl库的问题导致其联网同步时安全验证失败,官网上提供了解决方案
```shell
sudo apt-get install aptitude
# 安装aptitude
sudo aptitude install libssl1.0-dev
# aptitude会自动解决依赖，这里我们需要降级系统默认的ssl包，选择接受即可
```
重新打开为知笔记即可正常登录

> 预编译版本见：https://github.com/ferstar/WizQTClient/releases/tag/v2.8.2

![image](https://user-images.githubusercontent.com/2854276/74698328-5c652480-5238-11ea-9040-b8ee4de7ee3d.png)

