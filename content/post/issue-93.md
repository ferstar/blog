---
title: "无声的坍缩：多层隧道环境下的 MTU 黑洞排查实录"
date: "2025-12-31T12:09:54+08:00"
tags: ['Linux']
comments: true
---

> 本文由 Gemini 协助编写。

## 背景

在最近的一次跨地域算力池部署中，我遇到了一个非常有意思的网络“灵异事件”。

我们有两个站点（Site-A 和 Site-B），中间通过两层隧道打通：**WireGuard + IPsec（site-to-site）**。出于安全合规要求，**全站禁 ICMP**（等价于：`ping`/`traceroute` 都不可用）。

在这种“致盲”状态下，问题出现了：
- **流量方向 A -> B**：50Mbps，跑满。
- **流量方向 B -> A**：SSH 能连，但一传大文件（`scp`）速度就掉到 **30KB/s** 左右。

这种“单行道”式的带宽坍缩，通常意味着链路没断，但某种“协议层面的天花板”被触碰了。

## 排查过程：没有 ICMP 怎么排障？

在正常的网络排查中，我会用 `ping -s <size> -M do` 来探测路径 MTU。但现在 ICMP 被封禁，我收不到任何“包过大（Fragmentation Needed）/ Packet Too Big”的反馈。

既然不能 `ping`，我只能通过 **TCP 行为指纹** 来进行推断。我使用 `iperf3` 做了一组对比实验（下面给出最小可复现命令）：

### 1) TCP 默认测试（观察重传）

在接收端（例如 Site-A）启动服务：

```bash
iperf3 -s
```

在发送端（例如 Site-B）发起测试（看输出里的 `Retr`/吞吐）：

```bash
iperf3 -c <SITE_A_IP> -t 10
```

现象：发送端瞬间堆积大量重传，带宽锁定在 ~0.4Mbps 量级。

### 2) UDP 对照（验证链路“并未彻底坏掉”）

```bash
iperf3 -c <SITE_A_IP> -u -b 20M -t 10
```

现象：在设定 20Mbps 带宽时，通信基本正常（丢包可控）。

### 3) TCP MSS 步进探测（关键证据）

```bash
iperf3 -c <SITE_A_IP> -t 10 -M 1400
iperf3 -c <SITE_A_IP> -t 10 -M 1350
```

现象：
- `MSS = 1400` 时，速度坍缩且重传爆炸；
- `MSS = 1350` 时，吞吐**瞬间恢复**到 ~49Mbps。

**结论呼之欲出**：这是一个典型的 **PMTUD（Path MTU Discovery）黑洞**，而且是在“被致盲”（无 ICMP）环境下发生的。

## 原理解析：谁在“谋杀”数据包？

### 1) 先把 MSS/MTU 的换算说清楚

TCP 的 MSS 是“单个 TCP 段里可承载的 payload”，它受路径 MTU 限制。

- IPv4 常见近似：`MSS ≈ MTU - 20(IP) - 20(TCP) - TCP_OPTIONS`
- 以太网 MTU 1500 时，典型默认 MSS 是 1460（隐含 TCP options 取 0 或被实现细节吸收在近似里；不同抓包/栈实现会略有差异）。

在多层隧道（WireGuard + IPsec）下，**有效路径 MTU 会被封装头部持续“吃掉”**，于是默认的大 MSS 很容易变成“超载包”。

### 2) 为什么会变成 PMTUD black hole？

当发送方按默认 MSS 发大包：
- 中间某个节点发现包太大，本该回发 ICMP（IPv4 的 Fragmentation Needed / IPv6 的 Packet Too Big）提示“兄弟，包太大了，降 MTU/MSS”。
- 但由于策略 **全站禁 ICMP**，这个关键 ICMP 被防火墙默默丢弃。
- 发送方收不到通知，只能把“包丢了”误判为“链路丢包”，于是反复重传同样大小的包，吞吐被重传拖死。

这就是所谓的 **“MTU 黑洞”** —— 包丢了，但没人告诉你为什么。

### 3) 关于 WireGuard / IPsec 的开销（不要迷信固定数字）

我最初用“~80 + ~70”做了一个直觉估算，但更准确的说法是：

- WireGuard 的开销取决于外层 IPv4/IPv6、UDP、以及实现细节；常见量级在 **60~80 bytes**。
- IPsec ESP 的开销与模式（transport/tunnel）、NAT-T、有无 padding、加密套件（例如 AES-GCM）有关；常见量级在 **50~90 bytes**。

所以更可靠的做法是：**用抓包/文档确认你这条路径的实际封装开销，然后倒推一个安全 MTU/MSS**。

## 解决方案：从“根治”到“权宜”

### A. 根治（如果合规允许）：只放行“必要的 ICMP”，不是放行 `ping`

很多环境“禁 ping”其实只是不希望被探测，但 PMTUD 依赖的 ICMP 属于“控制面必要信号”。如果策略允许，建议至少放行：
- IPv4：ICMP Type 3 Code 4（Fragmentation Needed）
- IPv6：ICMPv6 Type 2（Packet Too Big）

这通常是最干净的修复：TCP 能自动收敛到正确 MTU，不需要在网关硬编码 MSS。

### B. 权宜 1：直接把隧道/出口 MTU 调到安全值

在 WireGuard/IPsec 的嵌套场景下，保守一点把相关接口 MTU 先降下来，往往就能立刻止血（代价是 payload 利用率略降）。

### C. 权宜 2：强制 MSS 钳制（MSS Clamping）

既然无法依赖 ICMP，我选择在流量必经的**中转网关**上执行“暴力”拦截：改写握手 SYN 上的 MSS，保证后续数据段不超过嵌套隧道的“物理上限”。

> 说明：也有人用 `--clamp-mss-to-pmtu`，但在 PMTUD black hole 环境里，路径 PMTU 信息本身可能不可靠/不可达；固定一个“已验证可用”的 MSS 往往更可控。

### 优化脚本：`vpn-optimize.sh`（脱敏版）

```bash
#!/bin/bash
set -euo pipefail

# VPN 网络优化脚本 - 解决 WireGuard + IPsec 多层隧道环境下的 MTU 黑洞问题

# --- 配置区 ---
PHY_IF="ens3"                # 物理网卡接口名
REMOTE_NET="10.0.0.0/24"     # 远程内网网段
TUNNEL_IP="100.64.0.1"       # 本地隧道出口 IP（示例）

# 1. 物理层优化（谨慎使用：会增加 CPU 开销；建议先验证确实需要再关）
ip link set dev "$PHY_IF" mtu 1400
ethtool -K "$PHY_IF" tso off gso off gro off

# 2. 核心优化：TCP MSS 钳制 (MSS Clamping)
# 针对转发流量 (FORWARD)：设置为 1280 字节（更保守）
iptables -t mangle -C FORWARD -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280 2>/dev/null || \
iptables -t mangle -I FORWARD -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280

# 针对本地发起的流量 (OUTPUT)：设置为 1350 字节（略激进但在本案例可用）
iptables -t mangle -C OUTPUT -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350 2>/dev/null || \
iptables -t mangle -I OUTPUT -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350
```

> 兼容性提示：部分系统的 `iptables` 实际是 `iptables-nft` 兼容层；如果你是纯 nftables 环境，需要用等价的 nft 规则实现。

## 验证闭环（非常重要）

1) **确认 MSS 真的被改写**：抓 SYN 包查看 MSS 选项是否落在你设定的值。

```bash
tcpdump -ni <IFACE> -vv 'tcp[tcpflags] & tcp-syn != 0 and host <REMOTE_HOST>'
```

2) **确认规则命中**：

```bash
iptables -t mangle -vnL FORWARD --line-numbers
iptables -t mangle -vnL OUTPUT  --line-numbers
```

3) **用 iperf3/实际 scp 回归**：`Retr` 显著下降、吞吐恢复到预期。

## 回滚（止血后可随时撤销）

- 删除 mangle 规则：用 `iptables -t mangle -D ...` 按 `--line-numbers` 指定行号删除。
- 恢复 MTU/offload：

```bash
ip link set dev <IFACE> mtu 1500
ethtool -K <IFACE> tso on gso on gro on
```

## 经验总结

1. **MTU 是第一生产力**：只要涉及 VPN/Overlay，默认 1500 很容易踩坑。
2. **非对称性思维**：单向限速通常不是“带宽不够”，而是“包大小不对”。
3. **宁缺毋滥**：把 MSS 设保守一点，牺牲少量载荷效率，换来稳定性和吞吐的数量级提升。

在“无声”的网络中排障，理解协议头比使用工具更重要。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-12-31T12:09:54+08:00
Updated at: 2025-12-31T20:20:18+08:00
Origin issue: https://github.com/ferstar/blog/issues/93
```
