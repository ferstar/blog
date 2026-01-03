---
title: "Killed (program cc1plus)"
slug: "solved-g-internal-compiler-error-killed-program-cc1plus"
date: "2015-08-12T14:41:00+08:00"
tags: ['OTHERS']
comments: true
---


兴高采烈编译`kobuki_bumper2pc_nodelet`中，突然蹦出这么个错，同时终端变的略卡，下意识的敲了下`free -h`，囧，原来是内存用尽了～

上swap拯救之

    # 在~目录建一个1G的swap文件，差不多应该够了
    dd if=/dev/zero of=~/swap.img bs=1M count=1000
    mkswap swap.img
    sudo swapon swap.img

再敲`free -h`确认下是否开启，结果如图

![2015-08-12 14:39:22屏幕截图.png](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/2015/08/1834023921.png_xyz)

已经用超一半swap，还好编译通过，好险～

阿西吧，编译`pano_py`时内存又爆掉，还得再加点swap

还是上面的方法，只需要新建一个`swap1.img`的swap file就可以
