---
title: "它不走 VPN，也不许你开：雅迪的 VPN 检测是怎么治住的"
slug: "how-to-avoid-yadea-vpn-detection"
date: "2026-10-11T21:45:00+08:00"
tags: ["Android", "KernelSU", "LSPosed", "VPN", "Yadea"]
series: ['Android Root']
description: "开着 VPN 打开雅迪 App 就弹「检测到VPN环境，请调整网络」然后直接退出；app 套了 360 加固还带反 Hook，上一篇文章那套进程内诊断全失灵。实测更气人：雅迪的流量根本不走 VPN，它照样管你全机的网络。最后用 VPN Hide 在 system_server 的 Binder 层和内核 kmod 层只对雅迪隐藏 VPN 特征，冷启动恢复正常——检测在它看不见的层级被拦下。"
---

[WPS 的 root 提示](/posts/how-to-avoid-wps-root-detection/)刚处理完，又轮到雅迪。手机开着 VPN 的时候打开雅迪 App，会弹一句「检测到VPN环境，请调整网络」，然后 App 直接退出，车况页面都进不去。

WPS 好歹只是提醒一下，雅迪是直接不让用。更离谱的是，雅迪自己的流量根本不走 VPN，我开不开 VPN 跟它的网络没关系，它就是要管。

## 现象

logcat 里很清楚：主进程打出「检测到VPN环境,请调整网络」，接着自己退出。`:pushservice` 推送进程也会弹同样的提示。

本来想拆 APK 看看，结果雅迪 8.8.12 套了 360 加固，拆出来只有壳代码，业务逻辑看不到。

## 进程内 hook 被加固拦住

WPS 那次是写个临时的 LSPosed 诊断模块，进进程 hook 检测方法、记录返回值。同样的办法放到雅迪上，加固壳初始化时就发现了，App 反复退出，走不到业务代码；把模块撤掉，又变回原来的 VPN 提示。进程内 hook 这条路走不通。试了下 Frida，版本兼容有问题，也没跑起来。

## 内存里 dump 出来的代码

静态拆不开，就等它运行时自己解密。正常启动后从内存里 dump 出业务 DEX，就能看到代码了。

顺着网络检测找，在个推 SDK 里有一段枚举网卡的代码，检查 `tun0`、`ppp0` 这类 VPN 网卡。不过没有证据证明那条提示就是它弹的，具体是哪个 API 触发的也没抓到，这里不下结论。

能确定的是另一件事。雅迪的 UID 是 `10450`，不在 VPN 接管的 UID 列表里，VPN 客户端的分应用名单里也没有它，它的流量本来就是直连的。所以在 VPN 客户端里把雅迪设成绕过也没用，它查的是整台手机有没有 VPN，跟自己的流量走哪条路无关。WPS 查的是装了什么应用，雅迪管的是整台手机的网络状态，伸得更远。

## 换到进程外面处理

进程里动不了，就只能在它看不到的地方改数据。[VPN Hide](https://github.com/okhsunrog/vpnhide) 就是这么做的，分两层：

- **Java 层**：LSPosed 模块挂在 system_server 上，在 Binder 的 `writeToParcel` 处把 `NetworkCapabilities`、`NetworkInfo`、`LinkProperties` 里的 VPN 信息去掉，App 通过 IPC 拿到的网络数据里就没有 VPN。整个过程不注入雅迪进程，加固的反 Hook 和内存完整性检测发现不了。
- **原生层**：用内核模块（kmod，基于 kprobe/kretprobe）在内核里隐藏 `tun` 网卡，接口枚举的 ioctl、`getifaddrs`、netlink 路由转储都会过滤，native 代码也查不到。后端可以选 kmod、KPM 或 Zygisk，Zygisk 是在进程内做 inline hook，可能被加固识破，这台手机的内核支持 kmod，就用了 kmod。

{{< mermaid >}}
flowchart TD
    Y["雅迪 App（360 加固 + 反 Hook）"]
    Y -->|"进程内 Hook 注入"| X["加固检测到介入，反复退出 ✗"]
    Y -->|"Java API 查询网络状态"| S["system_server<br/>VPN Hide：Binder 层过滤网络数据 ✓"]
    Y -->|"native 枚举网卡、路由"| K["内核<br/>VPN Hide kmod：藏起 tun0 ✓"]
{{< /mermaid >}}

kmod 不用刷内核，也不改 boot 镜像，是 KernelSU 模块开机时往现有内核里加载一个 `.ko`。但它确实改了运行中内核的行为，不兼容的话可能导致系统崩溃，卸载后也要再重启一次才能完全恢复。

配置只针对 `com.yadea.smartmoto` 开启 Java 和原生两层隐藏，LSPosed 作用域只勾系统框架，不勾雅迪。

## 结果

重启加载内核模块后，NekoBox 保持连接，雅迪连续两次冷启动都正常进了车辆首页，没再弹 VPN 提示，也没退出。

VPN Hide 有个统计页，开着抓了 43 秒，期间冷启动一次雅迪，一共记录到 156 次拦截：

| 查询类型 | 次数 |
|---|---|
| 原生 ioctl 网络接口查询 | 130 |
| IPv4 / IPv6 地址枚举 | 各 3 |
| Java `NetworkInfo` | 12 |
| Java `Network` 句柄 | 5 |
| Java `ConnectivityService` | 3 |

大头是原生层的 ioctl 接口查询，这条路能拿到接口列表、地址和启用状态，足够发现 `tun0` 这类 VPN 网卡。只在 Java 层过滤的话，这部分查询是拦不住的，这也是要同时开 kmod 的原因。不过这些计数里也包含正常的网络调用，不能理解成雅迪专门查了 156 次 VPN，也没法靠统计确定弹警告的是哪一次调用。

VPN Hide 自己的状态页显示「无需检查」，看着像没生效，其实是因为它本身不走 VPN，显示这个是正常的。

VPN Hide 只处理手机上能查到的 VPN 特征，不隐藏 root，也不管 Play Integrity。服务端那边的检测，比如 DNS 泄漏、IP 黑名单、TLS 指纹，它管不了。

## 和 WPS 对比

| | WPS | 雅迪 |
|---|---|---|
| 检测什么 | 装没装 root 管理器 | 手机上有没有 VPN |
| 检测代码有没有保护 | 没有 | 加固 + 反 Hook |
| 查到之后 | 弹 Toast | 弹提示后退出 |
| 在哪一层解决 | 包可见性（HMA） | system_server + 内核（VPN Hide） |

WPS 的检测就在应用层，没有保护，用 HMA 隐藏包名就够了。雅迪的检测藏在加固后面，进程里动不了，只能往下到 system_server 和内核去改它拿到的数据。

脱壳、dump 内存、读反编译代码、挑内核模块，这一套放在以前，就算是专业人士，为了一个厂商 App 的不合理管制花这么多工夫也不太值，普通用户更是只能忍着。现在有 AI 帮忙，普通人也能把这些活干完，自己的手机想怎么用，总算能自己说了算。
