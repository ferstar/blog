---
title: "ThinkPad X220 装黑苹果小记"
date: "2020-07-12T04:50:33+08:00"
tags: ['TODO', 'macOS']
comments: false
---

> created_date: 2020-07-12T04:50:33+08:00

> update_date: 2020-07-12T04:50:33+08:00

> comment_url: https://github.com/ferstar/blog/issues/22

> 从这抄的EFI https://github.com/tluck/Lenovo-T420-Clover

各处拖的驱动集合了一下，硬件基本完美驱动。

不工作的：读卡器、PCI express，当然还有无线网卡，自带的无线网卡是无解的，淘宝十八块换了乞丐版BCM4322 DW1510网卡，10.15以下免驱。

蓝牙：BCM20702A0，也OK，不过平时又几乎不用

打了这么些驱动：
![image](https://user-images.githubusercontent.com/2854276/87239101-b8298780-c43d-11ea-96d4-3f110eaa131f.png)

关于Intel HD3000集显冻屏的问题，需要选择适合的旧版驱动才行，这个可以在http://dosdude1.com/mojave/拿到，我提取了其中的驱动安装工具包

![image](https://user-images.githubusercontent.com/2854276/87239143-30904880-c43e-11ea-85f3-350dc2d398c1.png)

