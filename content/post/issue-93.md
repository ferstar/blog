---
title: "多层隧道 MTU 黑洞排查：scp 跑 30KB/s 的玄学"
date: "2025-12-31T12:09:54+08:00"
tags: ['Linux']
comments: true
---

> Gemini 协助编写

### 问题

跨地域算力池部署，Site-A 和 Site-B 之间跑了两层隧道：**WireGuard + IPsec**。安全合规要求，**全站禁 ICMP**——`ping` 和 `traceroute` 全废。

然后诡异的事情来了：
- **A → B**：50Mbps，跑满，没毛病
- **B → A**：SSH 能连，但 `scp` 大文件直接掉到 **30KB/s**

典型的"单行道"症状。链路没断，但某个协议层面的天花板被撞了。

一开始怀疑运营商限速、偷包，甚至想过是不是 QoS 策略在搞鬼。折腾半天，压根没往 MTU 方向想——典型的专家盲区：手里拿着抓包工具，看什么都像协议问题，反而忽略了最基础的链路参数。就像网络高手帮朋友排查问题，`tcpdump`、`wireshark` 一顿操作，最后发现是宽带欠费了。

---

### 排查：没 ICMP 怎么玩？

正常情况用 `ping -s <size> -M do` 探测路径 MTU。但 ICMP 被封了，收不到任何"包太大"的反馈。

只能靠 **TCP 行为指纹** 推断。用 `iperf3` 做对比实验：

#### 1) TCP 默认测试

```bash
# 接收端
iperf3 -s

# 发送端
iperf3 -c <SITE_A_IP> -t 10
```

现象：`Retr` 重传爆炸，带宽锁死在 ~0.4Mbps。

#### 2) UDP 对照

```bash
iperf3 -c <SITE_A_IP> -u -b 20M -t 10
```

现象：20Mbps 基本正常，丢包可控。说明链路本身没挂。

#### 3) TCP MSS 步进探测（关键）

```bash
iperf3 -c <SITE_A_IP> -t 10 -M 1400  # 坍缩，重传爆炸
iperf3 -c <SITE_A_IP> -t 10 -M 1350  # 瞬间恢复 ~49Mbps
```

**破案**：典型的 **PMTUD 黑洞**，在"致盲"环境下触发。

---

### 原理：谁在"谋杀"数据包？

#### MSS/MTU 换算

TCP MSS = 单个 TCP 段的 payload 上限，受路径 MTU 限制。

- IPv4 近似：`MSS ≈ MTU - 20(IP) - 20(TCP) - TCP_OPTIONS`
- 以太网 MTU 1500 时，默认 MSS 约 1460

多层隧道（WireGuard + IPsec）下，封装头部持续"吃掉"有效 MTU，默认大 MSS 就变成"超载包"。

#### 为什么变成黑洞？

1. 发送方按默认 MSS 发大包
2. 中间节点发现包太大，本该回 ICMP（Fragmentation Needed / Packet Too Big）
3. 但 **全站禁 ICMP**，这个关键信号被防火墙吃了
4. 发送方收不到通知，误判为"链路丢包"，疯狂重传同样大小的包
5. 吞吐被重传拖死

这就是 **MTU 黑洞**——包丢了，但没人告诉你为什么。

#### 隧道开销（别迷信固定数字）

- WireGuard：~60-80 bytes（取决于 IPv4/IPv6、UDP、实现细节）
- IPsec ESP：~50-90 bytes（取决于 transport/tunnel 模式、NAT-T、padding、加密套件）

**靠谱做法**：抓包确认实际封装开销，倒推安全 MTU/MSS。

---

### 解决方案

#### A. 根治（理想情况）

不是放行 `ping`，而是只放行 PMTUD 必要的 ICMP：
- IPv4：ICMP Type 3 Code 4（Fragmentation Needed）
- IPv6：ICMPv6 Type 2（Packet Too Big）

这样 TCP 能自动收敛到正确 MTU，不用硬编码 MSS。

**但现实是**：这类安全策略往往不归你管，合规要求动不了。往下看。

#### B. 权宜 1：降隧道 MTU

WireGuard/IPsec 嵌套场景，保守降接口 MTU，立刻止血。代价是 payload 利用率略降。

#### C. 权宜 2：MSS 钳制（我用的方案）

既然 ICMP 指望不上，直接在中转网关上暴力改写 SYN 包的 MSS：

```bash
#!/bin/bash
set -euo pipefail

# --- 配置 ---
PHY_IF="ens3"
REMOTE_NET="10.0.0.0/24"

# 1. 物理层优化（会增加 CPU 开销，按需开）
ip link set dev "$PHY_IF" mtu 1400
ethtool -K "$PHY_IF" tso off gso off gro off

# 2. MSS 钳制
# 转发流量：1280（保守）
iptables -t mangle -C FORWARD -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280 2>/dev/null || \
iptables -t mangle -I FORWARD -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280

# 本地发起：1350（略激进但本案例可用）
iptables -t mangle -C OUTPUT -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350 2>/dev/null || \
iptables -t mangle -I OUTPUT -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350
```

> 纯 nftables 环境需要用等价 nft 规则。

---

### 验证

#### 1) 确认 MSS 被改写

```bash
tcpdump -ni <IFACE> -vv 'tcp[tcpflags] & tcp-syn != 0 and host <REMOTE_HOST>'
```

#### 2) 确认规则命中

```bash
iptables -t mangle -vnL FORWARD --line-numbers
iptables -t mangle -vnL OUTPUT  --line-numbers
```

#### 3) 实测

`iperf3` 或 `scp` 回归，`Retr` 显著下降，吞吐恢复。

---

### 回滚

```bash
# 删 mangle 规则（按行号）
iptables -t mangle -D FORWARD <行号>
iptables -t mangle -D OUTPUT <行号>

# 恢复 MTU/offload
ip link set dev <IFACE> mtu 1500
ethtool -K <IFACE> tso on gso on gro on
```

---

### 总结

1. **MTU 是第一生产力**：VPN/Overlay 场景，默认 1500 就是坑
2. **非对称性思维**：单向限速通常不是带宽不够，而是包大小不对
3. **宁缺毋滥**：MSS 设保守点，牺牲一点载荷效率，换数量级的稳定性提升

在"无声"的网络里排障，理解协议头比会用工具更重要。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-12-31T12:09:54+08:00
Updated at: 2026-01-03T06:10:01+08:00
Origin issue: https://github.com/ferstar/blog/issues/93
```
