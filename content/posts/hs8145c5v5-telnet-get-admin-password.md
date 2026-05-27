---
title: "HS8145C5/V5 光猫：一行命令查出 telecomadmin 超管密码"
slug: "hs8145c5-v5-telnet-get-admin-password"
date: "2026-05-27T18:30:00+08:00"
tags: ['NETWORK', '光猫']
comments: true
description: "运营商送的光猫只有 useradmin 权限？不用刷机不用改配置文件，一条 display 命令直接吐出加密的超管密码，解密后即可用 telecomadmin 全权限登录。"
---

家里电信宽带配的 HS8145C5（或 V5）光猫，默认只给了 `useradmin` 普通用户权限，很多设置项看不到。网上教程大多让你改配置文件、甚至换华为界面，其实如果只是想要超管密码，有一个更直接的办法。

### 前提：光猫已开 Telnet

新出厂的光猫 Telnet 默认是关闭的，需要先用 **ONT 维修使能工具**（V3-V5 使能版）开一次 Telnet：

1. 光猫拔掉所有线缆，仅 LAN1 口插网线连电脑
2. 电脑 IP 设为 `192.168.1.x`（x ≠ 1）
3. 打开 ONT 工具，选 V5 使能，选对应网卡，点启动
4. 等到右侧设备列表出现绿色 **success**（光猫所有灯常亮），点停止、拔电重启

重启后 Telnet 就开了。这一步只需要做一次，之后只要不恢复出厂，Telnet 一直可用。

### 一行命令查超管密码

Telnet 连上光猫后，直接执行：

```shell
telnet 192.168.1.1
root
adminHW
su
display current-configuration grep telecomadmin
```

屏幕上会打印出包含 `telecomadmin` 的那一行，类似：

```
<X_HW_WebUserInfoInstance InstanceID="2" ModifyPasswordFlag="1" UserName="telecomadmin" Password="$2;xxxxxxxxxxxxxxxxxx$" UserLevel="0" Enable="1" .../>
```

`Password` 字段里 `$2;` 到 `$` 之间的部分就是加密后的超管密码。

### 解密 $2 密文

拿到加密串后，用 **华为配置加解密工具**（网上随便搜就有）的"密文解密"功能，把 `$2;...$` 整段粘进去，点解密，明文密码就出来了。

或者搜一下"华为配置加解密工具"，找个本地版的也行。

### 然后用 telecomadmin 登录

浏览器访问 `192.168.1.1`，用户名填 `telecomadmin`，密码填解密出来的明文，你就有了光猫的全部管理权限——改桥接、开 DMZ、删 TR069，想干什么干什么。

