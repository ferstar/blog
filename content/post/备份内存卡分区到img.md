---
title: "备份内存卡分区到img"
date: "2015-08-12T19:15:43+08:00"
tags: ['OTHERS']
comments: true
---


    # 将sdb分区拷贝到硬盘
    sudo dd if=/dev/sdb of=ros_ready.img bs=4M
    # bmaptool工具建立索引，提高下次写入内存卡速度，缩短写入时间
    bmaptool create ros_ready.img &gt; ros_ready.bmap
    # 压缩img，减小文件体积
    tar cvzf ros_ready.tar.gz ros_ready.img ros_ready.bmap
    `</pre>

    写入到内存卡

    <pre>`sudo bmaptool copy --bmap ros_ready.bmap ros_ready.img /dev/sdb

展开内存卡剩余未用空间

`直接用gparted即可`