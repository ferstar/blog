---
title: "Epson Lq 630 Communicate Error"
date: 2018-06-27T17:28:52+08:00
tags: ['WINDOWS']
comments: false
---

早上去财务报销，出纳小妹针式打印机罢工，报了这么个错

![printer-error](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/6/10241202527c1740882410421210ac11.png)

于是顺手解决了下。

1. 怀疑线缆问题，关机，重插拔线缆，开机，未果；

2. 怀疑驱动问题，删除打印机驱动，重装，扑街；

3. 怀疑 Windows 打印服务队列出问题，清空重置之，搞定。

   ```powershell
   @echo off
   echo Stopping print spooler.
   echo.
   net stop spooler
   echo deleting temp files.
   echo.
   del %windir%\system32\spool\printers\*.* /q
   echo Starting print spooler.
   echo.
   net start spooler
   ```

以上内容复制粘贴进新建文档中保存，重命名为任意以`bat`为后缀的文件双击运行即可（Windows7及以上系统需要右键以管理员权限运行）

打完单据，潇洒转身走人，深藏功与名~