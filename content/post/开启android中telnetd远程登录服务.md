---
title: "开启android中telnetd远程登录服务"
date: "2014-02-09T10:14:00+08:00"
tags: ['OTHERS']
comments: 
---


通过数据线及adb命令登录手机android系统很不方便，若PC机及手机均有wifi功能，可使PC通过wifi远程登录android,会带来很多方便。

### 要实现这个功能，首先要在手机上开启telnetd 服务，方法如下：

1.  确认手机上装有busybox软件，若没有需自行下载安装。
2.  运行busybox命令，确认输出中有telnetd，若无需更换其他busybox。
3.  要取得手机的root权限，手机上要装有terminal 软件。
4.  在terminal下使用 su 命令转为 root 用户， 键入命令 `telnetd -l /system/bin/sh`（要事先检查/system/bin/sh是否存在）
5.  PC及手机连接同一个wifi 网络，在PC上telnet登录手机的 ip 地址即可。 作为客户端连接其他电脑也很简单： `busybox
telnet IPAdress Port` 即可

### 注意事项：

#### telnet登录手机系统后，默认的sh shell可能不好用，比如使用backspace键有乱码，不能按上下箭头重复历史命令，输出没有颜色等，此时可自行选用bash、csh等常用的shell来解决。可用以下两种方法：

1.  直接在telnet窗口下运行bash或csh命令。
2.  在启动telnetd时直接指定需要的shell，如`telnetd -l /system/xbin/bash`，这样telnet登录后默认shell就是bash 。

### 另外，为防止登录过程中手机wifi休眠造成网络中断，要对手机wifi的休眠功能进行正确设置。