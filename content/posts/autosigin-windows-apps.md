---
title: "给自己打包的应用增加数字签名"
slug: "autosigin-windows-apps"
date: 2018-01-16T11:59:35+08:00
tags: ['WINDOWS', 'SCIHUB']
comments: true
---

先前写的scihub spider软件打包后window10安装提示”Windows已保护你的电脑，SmartScreen筛选器已阻止启动一个未识别的应用“，虽然大家都知道这是我写的，人畜无害，点更多信息，就会显示”仍要运行“，也不是不能安装，但始终感觉不爽。搜了下发现是应用缺少数字签名导致，所以下载了微软官方的SignTool，完美解决问题。

附签名过程信息：

```shell
D:\backup\setup>signtool.exe
SignTool Error: A required parameter is missing.
Usage: signtool <command> [options]

        Valid commands:
                sign       --  Sign files using an embedded signature.
                timestamp  --  Timestamp previously-signed files.
                verify     --  Verify embedded or catalog signatures.
                catdb      --  Modify a catalog database.
                remove     --  Reduce the size of an embedded signed file.

For help on a specific command, enter "signtool <command> /?"

D:\backup\setup>signtool.exe sign /a SciHub-Spider-update-1.6.6.exe
Done Adding Additional Store
Successfully signed: SciHub-Spider-update-1.6.6.exe
```

安装程序签名后属性一栏会多出”数字签名“的标签，perfect！
