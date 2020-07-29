---
title: "解决Windows资源保护找到损坏文件但无法修复的问题"
date: 2018-05-11T13:04:37+08:00
tags: ['WINDOWS']
comments: true
---

昨天更新Windows10 5月累计补丁，早上发现蓝牙耳机无法连接，折腾驱动神马的未果，怀疑是系统文件受损导致，Google一番，官方推荐`sfc /scannow`验证系统并修复受损文件，但得到的提示如下：

```powershell
开始系统扫描。此过程将需要一些时间。

开始系统扫描的验证阶段。
验证 100% 已完成。

Windows 资源保护找到了损坏文件但无法修复
其中某些文件。CBS.Log windir\Logs\CBS\CBS.log 中有详细信息。
例如 C:\Windows\Logs\CBS\CBS.log。请注意，在脱机服务方案中，
当前不支持日志记录。
```

意思是找到受损文件，但是`sfc`命令无法修复，然后找到了这篇文章

https://wangye.org/blog/archives/1081

照做后恢复正常。

```powershell
C:\WINDOWS\system32>findstr /C:"[SR] Cannot repair member file" %windir%\logs\cbs\cbs.log >"%userprofile%\Desktop\sfcdetails.txt"

C:\WINDOWS\system32>DISM.exe /Online /Cleanup-image /Scanhealth

部署映像服务和管理工具
版本: 10.0.16299.15

映像版本: 10.0.16299.431

[==========================100.0%==========================] 可以修复组件存储。
操作成功完成。

C:\WINDOWS\system32>DISM.exe /Online /Cleanup-image /Restorehealth

部署映像服务和管理工具
版本: 10.0.16299.15

映像版本: 10.0.16299.431

[==========================100.0%==========================] 还原操作已成功完成。
操作成功完成。

C:\WINDOWS\system32>Sfc /scannow

开始系统扫描。此过程将需要一些时间。

开始系统扫描的验证阶段。
验证 100% 已完成。

Windows 资源保护找到了损坏文件并成功修复了它们。
CBS.Log windir\Logs\CBS\CBS.log 中有详细信息。例如
C:\Windows\Logs\CBS\CBS.log。请注意，在脱机服务方案中，
当前不支持日志记录。

系统文件修复更改在下次重新启动之后生效。
```

