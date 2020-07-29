---
title: "深度截图工具是个好东西"
date: "2013-10-19T17:45:18+08:00"
tags: ['LINUX', 'SHELL']
comments: true
---


深度截图工具比ubuntu比自带的截图强大很多，类qq截图，简单安装步骤如下

1.  git clone https://github.com/linuxdeepin-packages/deepin-scrot.git
2.  cd deep-scrot<!--more-->
3.  ./updateTranslate.sh
4.  cd ./src/
5.  ./deepinScrot.py #提示缺少Xlib
6.  sudo apt-fast install python-xlib
7.  键盘设置路径~/deepin-scrot/src/deepin-scrot %u 快捷键设置为ctrl+alt+A组合，如下链接所示[http://hi.baidu.com/ferstar/item/3508c70c2ba82413cd34ea35](http://hi.baidu.com/ferstar/item/3508c70c2ba82413cd34ea35)
8.  完成
