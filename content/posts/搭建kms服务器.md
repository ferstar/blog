---
title: "搭建kms服务器"
slug: "setup-kms-activation-server-linux"
date: "2017-07-19T16:07:00+08:00"
tags: ['KMS', 'WINDOWS', 'OFFICE', 'UBUNTU']
comments: true
---


在digitalocean开了个vps, 于是就想着搭建这么一个东西, 方便激活

## 服务器配置

1. 从https://github.com/Wind4/vlmcsd releases页面下载binary包

2. `vlmcsdmulti-x64-glibc`移动到`/usr/local/bin`目录

3. 改下名字--> `vlmcsd`

4. 自启动`vlmcsd -l /var/log/vlmcsd.log`扔到`/etc/rc.local`

5. 控制面板防火墙放开`1688`端口

6. 看一下日志`tailf /var/log/vlmcsd.log`

   ```
   2017-07-19 07:47:28: Listening on [::]:1688
   2017-07-19 07:47:28: Listening on 0.0.0.0:1688
   2017-07-19 07:47:28: vlmcsd 1111, built 2017-06-17 00:53:13 UTC started successfully
   ```

   ​

## 激活配置

### Windows:

以管理员身份打开命令提示符,然执行下列命令：

```powershell
cd /d "%SystemRoot%\system32"
slmgr /skms kms.xxx.com
slmgr /ato
slmgr /xpr
```

### Office:

以管理员身份打开命令提示符,进入软件安装目录,然后执行下列命令:
```powershell
# 以Office 2016为例:
进入32位版本安装目录：
cd /d "%ProgramFiles(x86)%\Microsoft Office\Office16"
# 进入64位版本安装目录:
cd /d "%ProgramFiles%\Microsoft Office\Office16"
# 然后执行下列命令:
cscript ospp.vbs /sethst:kms.ferstar.org
cscript ospp.vbs /act
cscript ospp.vbs /dstatus
```

通过以上步骤就可以免费激活你的Windows系统和Office软件.
如果激活失败或输入过其他密钥,请先替换为[微软官方密钥](https://technet.microsoft.com/en-us/library/jj612867.aspx)
以安装政府版密钥为例(Ent G 400 Years):
`slmgr /ipk YYVX9-NTFWV-6MDM3-9PT4T-4M68B` 

### 注意

1. KMS方式激活的有效期只有180天.
2. 每隔一段时间系统会自动KMS服务器请求续期.
