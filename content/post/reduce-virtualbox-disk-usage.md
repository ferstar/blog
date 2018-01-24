---
title: "缩小Virtualbox动态磁盘大小"
date: 2018-01-24T10:13:56+08:00
tags: ['WINDOWS', 'VIRTUALBOX']
comments: true
---

Virtualbox运行一段时间后，虚拟硬盘会变的越来越大，但是虚拟机内部却没有这么多的文件。我的Windows XP虚拟机内部文件总大小只有4G多，但是虚拟硬盘文件已经达到8G。然而老夫256G SSD空间已所剩无几，急需榨取点空余磁盘。

![整理前](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/1/6b5172ee4fcf22a80042057d3e0ca121.png/xyz)

## 方法

1. 虚拟机系统进行碎片整理操作。

   ![虚拟机磁盘实际占用](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/1/664e171e2bc1fa0a1eed90b41e1d7296.png/xyz)

2. 使用`sdelete`将零写入虚拟机内的空白空间。

   ![清零](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/1/733c94e308fca306fffa17eb6ca5c7b0.png/xyz)

3. 在主机操作系统使用`VBoxManage`命令压缩`vdi`格式的虚拟磁盘文件。

   ```powershell
   # VBoxManage.exe及虚拟磁盘文件路径需要自行查找确认
   $ "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" modifyhd xp.vdi --compact
   0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%
   ```

4. 大功告成，检查一下成果，缩了近一半，well done！

   ![整理后](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/1/6ea2db3d177e33321c927bb4b339b8bd.png/xyz)

## 参考资料

- [SDelete v2.0](https://docs.microsoft.com/zh-cn/sysinternals/downloads/sdelete)

- [如何缩小VirtualBox虚拟机并释放磁盘空间](https://www.helplib.com/Linux/article_13911)

