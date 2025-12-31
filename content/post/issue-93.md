---
title: "无声的坍缩：多层隧道环境下的 MTU 黑洞排查实录"
date: "2025-12-31T12:09:54+08:00"
tags: ['Linux']
comments: true
---

> 本文由 Gemini 协助编写。

## 背景

在最近的一次跨地域算力池部署中，我遇到了一个非常有意思的网络“灵异事件”。

我们有两个站点（Site-A 和 Site-B），中间通过两层隧道（Overlay VPN + IPsec）打通。出于安全合规要求，**全站禁 Ping**。这意味着，我手里唯一的探测工具 `ping` 和 `traceroute` 彻底废了。

在这种“致盲”状态下，问题出现了：
- **流量方向 A -> B**：50Mbps，跑满。
- **流量方向 B -> A**：SSH 能连，但一传大文件（`scp`）速度就掉到 **30KB/s** 左右。

这种“单行道”式的带宽坍缩，通常意味着链路没断，但某种“协议层面的天花板”被触碰了。

## 排查过程：没有 ICMP 怎么排障？

在正常的网络排查中，我会用 `ping -s <size> -M do` 来探测路径 MTU。但现在 ICMP 被封禁，我收不到任何“包过大（Fragmentation Needed）”的回应。

既然不能 Ping，我只能通过 **TCP 行为指纹** 来进行推断。我使用 `iperf3` 进行了一组对比实验：

1. **默认测试**：发送端瞬间堆积大量重传，带宽锁定在 0.4Mbps。
2. **UDP 测试**：在设定 20Mbps 带宽时，通信基本正常。
3. **TCP MSS 探测**：这是关键。我手动在 `iperf3` 中步进设置 MSS（最大报文段大小）：
   - MSS = 1400 时，速度坍缩；
   - MSS = 1350 时，速度**瞬间恢复**到 49Mbps。

**结论呼之欲出**：这是一个典型的 **PMTU（Path MTU）黑洞**，而且还是在“被致盲”的环境下发生的。

## 原理解析：谁在“谋杀”数据包？

为什么 MSS 1400 就不行？我们来算一笔账：

| 组件 | 开销 (Overhead) |
| :--- | :--- |
| 标准以太网 MTU | 1500 字节 |
| 第一层隧道 (Overlay) | ~80 字节 |
| 第二层隧道 (IPsec) | ~70 字节 |
| **剩余载荷空间** | **~1350 字节** |

这就是整条路径的“物理上限”。当 TCP 尝试发送默认的 1460 字节大包时，中间节点发现包太大，本该回发一个 ICMP 消息说“兄弟，包太大了，拆一下”。

但由于我们**全站禁 Ping**，这个 ICMP 消息被防火墙默默丢弃了。发送方收不到通知，固执地认为链路丢包了，于是反复重传 1460 的大包，导致链路陷入死锁。这就是所谓的 **“MTU 黑洞”** —— 包丢了，但没人告诉你为什么。

## 解决方案：强制 MSS 钳制

既然无法改变中间节点的 ICMP 策略，我决定在流量必经的**中转网关**上执行“暴力”拦截。

### 1. 物理层优化
降低网卡 MTU 并关闭 Offload 加速，防止网卡在硬件层合并出违规的超大包。

### 2. 差异化 MSS 策略 (MSS Clamping)
针对“转发”和“本地”流量设置不同的 MSS 上限，确保嵌套隧道的兼容性。

### 优化脚本：`vpn-optimize.sh` (脱敏版)

```bash
#!/bin/bash
# VPN 网络优化脚本 - 解决多层隧道环境下的 MTU 黑洞问题

# --- 配置区 ---
PHY_IF="ens3"                # 物理网卡接口名
REMOTE_NET="10.0.0.0/24"     # 远程内网网段
TUNNEL_IP="100.64.0.1"       # 本地隧道出口 IP

# 1. 物理层优化
ip link set dev $PHY_IF mtu 1400
ethtool -K $PHY_IF tso off gso off gro off

# 2. 核心优化：TCP MSS 钳制 (MSS Clamping)
# 针对转发流量 (FORWARD)：设置为 1280 字节，确保本地 SCP 飞快
iptables -t mangle -C FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280 2>/dev/null || \
iptables -t mangle -I FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280

# 针对本地发起的流量 (OUTPUT)：设置为 1350 字节
iptables -t mangle -C OUTPUT -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350 2>/dev/null || \
iptables -t mangle -I OUTPUT -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350
```

## 经验总结

1. **MTU 是第一生产力**：只要涉及 VPN 或 Overlay，1500 必然踩坑。
2. **非对称性思维**：单向限速通常不是带宽限制，而是包大小限制。
3. **宁缺毋滥**：将 MSS 设为 1280/1350 虽然损失了约 2% 的载荷效率，但换来的是 100 倍的稳定性提升。

在“无声”的网络中排障，理解协议头比使用工具更重要。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-12-31T12:09:54+08:00
Updated at: 2025-12-31T12:09:54+08:00
Origin issue: https://github.com/ferstar/blog/issues/93
```
