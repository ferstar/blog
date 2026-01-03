---
title: "临时解决plasmashell狂占CPU的bug"
slug: "kde-plasmashell-high-cpu-fix"
date: "2020-05-07T08:29:38+08:00"
tags: ['Linux']
comments: true
---

> 怒装黑苹果了，香~

本子升到20.04, 顺路换成了KDE, 不过一直有个问题就是: 每次从休眠唤醒一段时间后, 桌面会变的异常卡, htop一发发现plasmashell占了近100%, 这明显不科学, google一发发现似乎是kde的陈年烂事, 没办法, 大力出奇迹~

```shell
killall plasmashell; kstart5 plasmashell; exit
```

后来发现把独显屏蔽似乎就没这个问题了, 看来还是NV显卡驱动的锅
![image](https://user-images.githubusercontent.com/2854276/81272274-db236e00-907f-11ea-99bc-f5219cbd83b1.png)

另外如果发现菜单图标雪花, 也可以通过kill大法搞定, 如图
![image](https://user-images.githubusercontent.com/2854276/81284262-78869e00-9090-11ea-91a7-c13f3dc179e2.png)

```
# NOTE: I am not responsible for any expired content.
create@2020-05-07T08:29:38+08:00
update@2024-06-12T02:46:00+08:00
comment@https://github.com/ferstar/blog/issues/20
```
