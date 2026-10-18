---
title: "我用 tailcat 改造了 RustDesk，扫码就能直连"
slug: "yet-another-remote-desktop-application-sealdesk"
date: "2026-10-16T22:30:00+08:00"
tags: ["Rust", "P2P", "Remote Desktop", "Tailscale", "Open Source", "Security"]
series: ["Open Source Projects"]
description: "自建 RustDesk 要买公网 VPS 部署 hbbs 与 hbbr，公共中继又常被限速、可用性不稳；SealDesk 把传输层换到 tailcat 上：零配置，不用注册账号、不用配服务器，扫码即连、P2P 优先，会话端到端加密；文内拆解架构改造、C-ABI 桥接、网络穿透与工程落地的关键取舍。"
---

昨天我把 SealDesk 开源了：RustDesk 的传输层换成 tailcat，被控端点一下分享，控制端扫个码就能连上。

RustDesk 的公共服务器不总是好用，自建又得买 VPS、起 `hbbs` 和 `hbbr`。SealDesk 把这套省掉了，账号也不用注册。

## 没有服务器，两端怎么找到对方

做这个项目的契机，是 Tailscale 开源了 [tailcat](https://github.com/tailscale/tailcat)。Tailscale 的穿透能力和 WireGuard 组网都好用，但标准用法离不开一个协调服务器（官方 SaaS 或自建 Headscale），身份认证、节点分发、ACL 都在那一层。tailcat 把数据面单独剥了出来：没有账号系统，没有控制平面，只剩下点对点通信本身。

`tc` 地址就是完整的连接凭证。服务端启动后生成一段 `tc` 开头的 Base64 字符串，150 字符左右，里面打包了 WireGuard 公钥、预共享密钥（PSK）和握手用的 DERP 节点区域，两端相认需要的密码学材料全在这一串里。

双方拿着这个地址在公共 DERP 节点上会合，STUN/UDP 打洞一旦成功，流量立刻切到两端直连的 WireGuard UDP 隧道；只有对称型 NAT 这类实在打不通的环境，才由 DERP 兜底转发密文，而它在数学上解不开 WireGuard 的载荷。这个会合用的中继就是 Tailscale 的公共 DERP，不用自己养，原来那套 `hbbs` / `hbbr` 就可以整个拿掉了。

## 扫码之后

握手不走中心服务器，配对码只负责把 `tc` 地址和临时密码带到控制端：

{{< mermaid >}}
flowchart TD
    subgraph 被控端 Host
        H1[启动 tailcat 监听服务] --> H2[生成 tc... 地址 + 临时密码]
        H2 --> H3[渲染 SEALDESK: 配对二维码]
        H3 --> H4[等待 DERP 会合信标]
    end

    subgraph 控制端 Controller
        C1[扫码 / 拖入图片 / 粘贴文本] --> C2[解析 tc 地址与临时密码]
        C2 --> C3[连接 tailcat 传输层]
    end

    subgraph 握手与通道建立
        C3 & H4 --> D1[公共 DERP 节点会合握手]
        D1 --> D2{STUN/UDP 打洞检测}
        D2 -->|打洞成功| D3[切换为 P2P WireGuard 直连通道]
        D2 -->|严格 NAT 限制| D4[回退至 DERP 加密兜底转发]
    end

    D3 & D4 --> R[RustDesk 桌面会话层: 认证、音视频流、键鼠控制]
{{< /mermaid >}}

被控端打开界面点「Share this device」，二维码就在界面正中。控制端在手机上直接扫；桌面端可以用摄像头扫码、选择二维码图片文件，或者直接粘贴剪贴板里的截图和文本。两端在同一个局域网里时，不用过外网也能互相发现直连，第一次连进来要在被控端点一下同意，顺手勾上「信任此设备」，下次就直接进。

临时密码可以刷新，地址可以重置，换掉之后旧配对码就失效。用完在任一端停止共享，所有会话跟着断开，后台不留任何进程。

## Go 和 Rust 之间的那层 C-ABI

tailcat 是纯 Go，RustDesk 核心是 Rust。我们在 `libs/tailcat-ffi` 里用 cgo 封了一层极简 C-ABI：服务端走 `TcServe`，传入本地 RustDesk 的 loopback 端口，隧道上的每条连接都被转发到这个口，返回生成的 `tc...` 地址；控制端走 `TcForward`，传入对端地址，它在本地开一个转发口，客户端连上去就进了隧道。所有返回的字符串统一用 `TcFree` 释放，跨 FFI 传指针不会泄漏。

Android 上多绕了一步：Go 1.27.1 的 `-buildmode=c-archive` 在 android/arm64 上直接报不支持，构建只好换成 c-shared，Rust 这边跟着改成链接 `libtailcat.so`。

## 绕开 rendezvous_mediator

原版 RustDesk 的网络层和 `rendezvous_mediator` 耦合很重，连接前要先问中心服务器拿对端的直连 IP 列表或中继地址。我们在 `src/client.rs`、`src/tailcat.rs` 和 `src/client/io_loop.rs` 里加了一条独立的 tailcat 通道：只要对端是 `tc...` 地址，就跳过所有中心化解析，桌面流直接走 tailcat 的加密连接。RustDesk 成熟的编解码（H.264/H.265/VP9）和键鼠注入机制原样保留。

## Android 换网就断流

控制端经常在 Wi-Fi 和蜂窝网络之间切换，一换网，路径更新跟不上，会话就容易断。Android 又不给应用 UID 用 netlink，Go 侧的 netmon 自己列不出网络接口，只能靠上层把接口列表喂过来。我们在 `libs/tailcat-ffi/android_interfaces.go` 里加了 `TcSetAndroidInterfaces`：Kotlin 层用 `java.net.NetworkInterface` 读出接口的名字和地址，Connectivity 一变化就通过 JNI 把 JSON 推给它，注册进 netmon，免得移动端远控走两步就重连。

## 平台和限制

各平台的 CI 和打包已经修好，Windows、macOS、Linux 和 Android 的跨平台安装包都放到了 Release 里（`.exe` / `.msi`、`.dmg`、`.deb` / `.rpm` / `.AppImage`、`.apk`）。桌面端双向互控均已测通，Android 目前主要作为控制端使用，暂时没有 iOS 构建。

macOS 版本没有买开发者证书做公证，初次打开如果被 Gatekeeper 拦截，终端里执行一条命令清掉隔离属性即可：

```bash
xattr -cr /Applications/SealDesk.app
```

和原版 RustDesk 互控走的是它原来的直连协议（TCP 21118 裸流，没有 tailcat 的 WireGuard 隧道介入），这一段不加密，连接前 SealDesk 会弹窗提示。

SealDesk 挂在 [runseal-labs](https://github.com/runseal-labs) 名下（Seal 取的是两端密封隔离的意思），仓库在 [github.com/runseal-labs/sealdesk](https://github.com/runseal-labs/sealdesk)，安装包见 [Releases](https://github.com/runseal-labs/sealdesk/releases)。不想再伺候 `hbbs` / `hbbr` 的可以拉下来试试，Issue 和 PR 都欢迎。
