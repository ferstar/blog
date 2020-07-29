---
title: "ThinkPad X220 装黑苹果小记"
date: "2020-07-12T04:50:33+08:00"
tags: ['macOS']
comments: false
---

> created_date: 2020-07-12T04:50:33+08:00

> update_date: 2020-07-15T00:20:36+08:00

> comment_url: https://github.com/ferstar/blog/issues/22

> 从这抄的EFI https://github.com/tluck/Lenovo-T420-Clover

各处拖的驱动集合了一下，硬件基本完美驱动。

不工作的：读卡器、PCI express，当然还有无线网卡，自带的无线网卡是无解的，淘宝十八块换了乞丐版BCM4322 DW1510网卡，10.15以下免驱。

蓝牙：BCM20702A0，也OK，不过平时又几乎不用

打了这么些驱动：
![image](https://user-images.githubusercontent.com/2854276/87239101-b8298780-c43d-11ea-96d4-3f110eaa131f.png)

关于Intel HD3000集显冻屏的问题，需要选择适合的旧版驱动才行，这个可以在http://dosdude1.com/mojave/ 拿到，安装后从未碰到冻屏死机问题，就是偶尔屏幕有细横线，基本不影响码字，话说这本子键盘手感真好！

![image](https://user-images.githubusercontent.com/2854276/87239143-30904880-c43e-11ea-85f3-350dc2d398c1.png)

因为用到的`Shades`调光软件是32位的，x220这块垃圾TN屏PWM调光，低亮度下闪瞎眼，只有靠这个软件才能活的样子，所以停留在Mojave养老了。

升级路径：10.13.6 -> Mojave Patcher -> 10.14.6

EFI链接`亲测最高可支持到10.15.5，乞丐网卡驱动正常`：https://github.com/ferstar/blog/files/4908021/EFI_X220.zip

其实最适合x220的macOS版本是10.12.x，各种完美，屏幕也不会有细线，更不用说冻屏啥的，然而一堆软件不支持，迫不得已上10.14.x。

传一个`Shades`软件：
[shades-intel.zip](https://github.com/ferstar/blog/files/4922167/shades-intel.zip)