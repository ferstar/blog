---
title: "Linux 6.17 网络优化：DualPI2 + BBR 彻底解决 50Mbps 窄带宽 Bufferbloat"
date: "2025-12-18T06:30:04+08:00"
tags: ['Linux']
comments: true
---

## 背景

在一台 50Mbps 带宽的云主机上部署 VPN 中转服务时，遇到了经典的 **Bufferbloat**（缓冲区膨胀）问题：一旦有大文件下载占满带宽，SSH 延迟从 50ms 飙升到 200ms+，严重影响交互体验。

传统的 `fq` + `bbr` 组合在窄带宽场景下效果有限，因为 `fq` 只做公平队列，无法主动控制排队延迟。

## 方案：DualPI2 + BBR

Linux 6.17 内核引入了 `sch_dualpi2` 调度器，专为低延迟设计：

| 调度器 | 工作方式 |
|--------|----------|
| `fq` | 公平队列，让每个连接平分带宽，但不管排队延迟 |
| `dualpi2` | 主动管理排队时间，通过 ECN 标记/丢包强制发送端降速，死守延迟底线 |

## 配置步骤

### 1. 内核要求

需要 Linux 6.17+ 内核（包含 `sch_dualpi2` 模块）。

### 2. sysctl 配置

编辑 `/etc/sysctl.conf`：

```conf
# --- 核心调度方案 ---
net.core.default_qdisc = dualpi2
net.ipv4.tcp_congestion_control = bbr

# --- 极致延迟优化 ---
net.ipv4.tcp_ecn = 1              # 必须开启，dualpi2 核心手段
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_recovery = 1         # RACK 快速修复乱序
net.ipv4.tcp_notsent_lowat = 8192 # 降低 BBR 内核缓冲量

# --- 缓冲区设置（针对 50Mbps，严防膨胀）---
net.core.rmem_max = 4194304
net.core.wmem_max = 4194304
net.ipv4.tcp_rmem = 4096 16384 4194304
net.ipv4.tcp_wmem = 4096 16384 4194304

# --- 稳定性优化 ---
net.core.somaxconn = 2048
net.ipv4.tcp_max_syn_backlog = 2048
net.mptcp.enabled = 1
```

### 3. 模块自动加载

```bash
echo "sch_dualpi2" | sudo tee /etc/modules-load.d/dualpi2.conf
```

### 4. 网卡持久化（udev 规则）

创建 `/etc/udev/rules.d/99-ens3-dualpi2.rules`：

```bash
ACTION=="add", SUBSYSTEM=="net", NAME=="ens3", RUN+="/sbin/tc qdisc replace dev ens3 root dualpi2"
```

> 将 `ens3` 替换为你的网卡名

### 5. 应用配置

```bash
sudo sysctl -p
sudo tc qdisc replace dev ens3 root dualpi2
```

## 验证方法

### 检查 dualpi2 状态

```bash
tc -s qdisc show dev ens3
# 观察 target 值，默认 5ms
```

### 压力测试（服务器禁 Ping 方案）

传统 `ping` 在禁 ICMP 的服务器上失效，改用内核 RTT 统计：

```bash
# 客户端：打满带宽
iperf3 -c <server> -t 60

# 服务端：观察内核 RTT
ss -tni
# 关注 rtt:X/Y — X 是平均 RTT，Y 是抖动(mdev)
```

## 测试结果

在 50Mbps 带宽满载情况下：

| 指标 | 结果 |
|------|------|
| 满载带宽 | 50 Mbps（峰值 51.4 Mbps）|
| 满载时 SSH RTT | 54.78ms（物理极限 48.33ms）|
| RTT 抖动 | **2.08ms** ✅ |
| 拥塞控制 | 全连接 BBR 生效 |
| 丢包恢复 | RACK 快速修复，无拥塞崩溃 |

**满载下载时 SSH 延迟仅高出物理极限 6.4ms，抖动 2ms，Bufferbloat 完全控制。**

## 原理解析

1. **DualPI2** 在微秒级压制排队延迟，默认 target 5ms
2. **BBR** 在毫秒级压制带宽膨胀，周期性探测真实 RTT
3. **ECN** 让发送端提前感知拥塞，避免丢包
4. **RACK** 快速修复乱序，避免拥塞窗口崩溃

这套组合在 50Mbps 窄带宽下实现了近乎完美的延迟/吞吐平衡。

## 参考

- [DualPI2 - IETF Draft](https://datatracker.ietf.org/doc/draft-ietf-tsvwg-aqm-dualq-coupled/)
- [BBR Congestion Control](https://github.com/google/bbr)
- [sch_dualpi2](https://datatracker.ietf.org/doc/rfc9332/)



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-12-18T06:30:04+08:00
Updated at: 2025-12-18T12:06:30+08:00
Origin issue: https://github.com/ferstar/blog/issues/92
```
