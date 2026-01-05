---
title: "Troubleshooting MTU Black Holes in Multi-Layer Tunnels: The Mystery of 30KB/s scp"
slug: "mtu-black-hole-scp-optimization"
date: "2025-12-31T12:09:54+08:00"
tags: ['Linux']
description: "A deep dive into MTU black hole troubleshooting for multi-layer tunnels (WireGuard + IPsec) in ICMP-disabled environments. Learn how to identify and fix path MTU issues using TCP MSS clamping."
---

> I am not a native English speaker; this article was translated by Gemini.

### The Problem

During a cross-regional GPU cluster deployment, two layers of tunnels were established between Site-A and Site-B: **WireGuard + IPsec**. Due to security compliance, **ICMP was disabled site-wide**—`ping` and `traceroute` were useless.

Then came a strange symptom:
- **A → B**: 50Mbps, full speed, perfect.
- **B → A**: SSH connects, but `scp` of large files drops to exactly **30KB/s**.

This is a classic "one-way street" symptom. The link isn't broken, but a protocol-level ceiling is being hit.

---

### Troubleshooting: How to play without ICMP?

Normally, you'd use `ping -s <size> -M do` to detect Path MTU. But with ICMP blocked, there's no feedback for "Packet Too Big."

I had to rely on **TCP behavioral fingerprints**. I conducted experiments with `iperf3`:

#### 1) Default TCP Test
Bandwidth locked at ~0.4Mbps with massive retransmissions (`Retr`).

#### 2) UDP Control Test
20Mbps worked normally with controllable loss. The link itself was fine.

#### 3) TCP MSS Stepping (The Breakthrough)
```bash
iperf3 -c <SITE_A_IP> -t 10 -M 1400  # Bandwidth collapses, heavy retrans
iperf3 -c <SITE_A_IP> -t 10 -M 1350  # Instant recovery to ~49Mbps
```

**Case Closed**: A classic **PMTUD Black Hole** triggered in a "blind" network environment. This is a typical "expert's blind spot": you have `tcpdump` and `wireshark` running, looking for complex protocol issues, while ignoring the most fundamental link parameters.

---

### The Theory: Who is "Murdering" the Packets?

#### MTU/MSS Breakdown
TCP MSS is the maximum payload of a single TCP segment, limited by the Path MTU.

- IPv4 approx: `MSS ≈ MTU - 20(IP) - 20(TCP) - Options`
- Standard Ethernet MTU 1500 results in ~1460 MSS.

In multi-layer tunnels (WireGuard + IPsec), the encapsulation headers continuously "eat" the available MTU. The default large MSS becomes an "overloaded packet."

#### Why the Black Hole?
1. The sender sends a large packet based on default MSS.
2. An intermediate node finds the packet too large and tries to return an ICMP (Fragmentation Needed).
3. But **ICMP is blocked**, so this signal is lost.
4. The sender never receives the notice, assumes the packet was dropped due to congestion, and retransmits the *same oversized packet* indefinitely.
5. Throughput is killed by retransmissions.

---

### Solutions

#### A. The Cure (Ideal)
Allow specifically required ICMP types:
- IPv4: ICMP Type 3 Code 4 (Fragmentation Needed)
- IPv6: ICMPv6 Type 2 (Packet Too Big)

#### B. Workaround 1: Lower Interface MTU
Lower the MTU on the WireGuard or IPsec interfaces to stop the bleeding.

#### C. Workaround 2: MSS Clamping (My Implementation)
Since ICMP is unreliable, force the MSS rewrite on the transit gateway:

```bash
#!/bin/bash
set -euo pipefail

# --- Config ---
PHY_IF="ens3"
REMOTE_NET="10.0.0.0/24"

# 1. Physical Layer Optimization (increases CPU overhead, enable as needed)
ip link set dev "$PHY_IF" mtu 1400
ethtool -K "$PHY_IF" tso off gso off gro off

# 2. MSS Clamping
# For Forwarded traffic: 1280 (Conservative)
iptables -t mangle -C FORWARD -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280 2>/dev/null || \
iptables -t mangle -I FORWARD -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1280

# For Local traffic: 1350 (Aggressive but functional in this case)
iptables -t mangle -C OUTPUT -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350 2>/dev/null || \
iptables -t mangle -I OUTPUT -p tcp -d "$REMOTE_NET" --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1350
```

---

### Summary
1. **MTU is the Foundation**: In VPN/Overlay scenarios, the default 1500 is a trap.
2. **Asymmetric Thinking**: One-way speed limits are often MTU issues, not bandwidth caps.
3. **Better Safe than Sorry**: Set a conservative MSS. Sacrificing a bit of payload efficiency is worth a 100x gain in stability.
