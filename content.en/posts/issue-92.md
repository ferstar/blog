---
title: "Linux 6.17 Network Tuning: DualPI2 + BBR to Eliminate Bufferbloat on 50Mbps Bandwidth"
slug: "linux-network-bbr-dualpi2"
date: "2025-12-18T06:30:04+08:00"
tags: ['Linux']
series: ["Network & Security"]
description: "Say goodbye to lag during large downloads. Learn how to use the DualPI2 scheduler introduced in Linux 6.17 combined with BBR to fix Bufferbloat on narrow bandwidth links."
---

> I am not a native English speaker; this article was translated by Gemini.

## Background

When deploying a VPN relay service on a 50Mbps cloud host, I encountered the classic **Bufferbloat** problem: whenever a large download saturated the bandwidth, SSH latency spiked from 50ms to over 200ms, severely degrading the interactive experience.

The traditional `fq` + `bbr` combo has limited effectiveness on narrow bandwidth links because `fq` only ensures fair queuing—it doesn't actively control queuing delay.

## The Solution: DualPI2 + BBR

Linux 6.17 introduced the `sch_dualpi2` scheduler, designed specifically for low latency:

| Scheduler | Mechanism |
|--------|----------|
| `fq` | Fair Queuing: Ensures each connection gets equal bandwidth but ignores queuing delay. |
| `dualpi2` | Active Queue Management: Controls queuing time using ECN marking or packet drops to force senders to slow down, strictly maintaining a latency floor. |

## Configuration Steps

### 1. Requirements
Linux Kernel 6.17 or higher (includes the `sch_dualpi2` module).

### 2. sysctl Configuration
Edit `/etc/sysctl.conf`:

```conf
# --- Core Scheduling Scheme ---
net.core.default_qdisc = dualpi2
net.ipv4.tcp_congestion_control = bbr

# --- Latency Optimization ---
net.ipv4.tcp_ecn = 1              # Essential for dualpi2
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_recovery = 1         # RACK for fast reordering fixes
net.ipv4.tcp_notsent_lowat = 8192 # Lower BBR kernel buffering

# --- Buffer Settings (Preventing Bloat on 50Mbps) ---
net.core.rmem_max = 4194304
net.core.wmem_max = 4194304
net.ipv4.tcp_rmem = 4096 16384 4194304
net.ipv4.tcp_wmem = 4096 16384 4194304

# --- Stability Optimization ---
net.core.somaxconn = 2048
net.ipv4.tcp_max_syn_backlog = 2048
net.mptcp.enabled = 1
```

### 3. Auto-load Module
```bash
echo "sch_dualpi2" | sudo tee /etc/modules-load.d/dualpi2.conf
```

### 4. Persistence (udev Rule)
Create `/etc/udev/rules.d/99-ens3-dualpi2.rules`:
```bash
ACTION=="add", SUBSYSTEM=="net", NAME=="ens3", RUN+="/sbin/tc qdisc replace dev ens3 root dualpi2"
```

> Replace `ens3` with your network interface name.

### 5. Apply Configuration
```bash
sudo sysctl -p
sudo tc qdisc replace dev ens3 root dualpi2
```

## Verification Methods

### Check DualPI2 Status
```bash
tc -s qdisc show dev ens3
# Observe the target value, default is 5ms
```

### Stress Testing (Solution for ICMP-Disabled Servers)
Traditional `ping` fails on servers with ICMP blocked. Use kernel RTT statistics instead:

```bash
# Client: Saturate the bandwidth
iperf3 -c <server> -t 60

# Server: Observe Kernel RTT
ss -tni
# Focus on rtt:X/Y — X is mean RTT, Y is jitter (mdev)
```

## Results

Under full 50Mbps load:

| Metric | Result |
|------|------|
| Throughput | 50 Mbps (Peak 51.4 Mbps) |
| SSH RTT under load | 54.78ms (Physical limit 48.33ms) |
| RTT Jitter | **2.08ms** ✅ |

**SSH latency remained only 6.4ms above the physical limit during full downloads, with 2ms jitter. Bufferbloat is completely eliminated.**
