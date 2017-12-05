+++
date = "2016-08-19T10:11:00+08:00"
title = "Installation of Bash on Windows is just a few clicks"
tags = ['OTHERS']

+++

N久之前就用过一次Windows10的bash, 不过效果惨不忍睹, bug百出, 遂放弃. 然而最近手痒, 想看看这货有啥进展.
这是安装教程
msdn blog via <https://msdn.microsoft.com/commandline/wsl/install_guide>
坑爹, 非得是逼着开发者给他当系统测试小白鼠才给装
```
Windows PowerShell
版权所有 (C) 2016 Microsoft Corporation。保留所有权利。
PS C:\WINDOWS\system32> Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux

Path          :
Online        : True
RestartNeeded : False

PS C:\WINDOWS\system32> bash
-- Beta 版功能 --
这将在 Windows 上安装由 Canonical 分发的 Ubuntu，
根据其条款的授权参见此链接:
https://aka.ms/uowterms

键入“y”继续: y
正在从 Windows 应用商店下载... 26%
```
这个速度, 巨硬商店下载速度还是很不给力的说~

## 卸载保平安

```
PS C:\WINDOWS\system32> lxrun /uninstall /full
这将在 Windows 中卸载 Ubuntu。
这将删除 Ubuntu 环境以及任何修改、新应用程序和用户数据。
键入“y”继续: y
正在卸载...
```