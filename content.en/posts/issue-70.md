---
title: "AX3600: Upgrading ShellClash to Clash-Meta Core for Hysteria 2 Support"
slug: "ax3600-clash-meta-upgrade"
date: "2023-01-24T01:17:09+08:00"
tags: ['Linux', 'Networking']
series: ["Network & Security"]
description: "Solve the storage limitation on Xiaomi AX3600 routers. Learn how to use UPX compression to replace the Clash-Meta core, enabling support for Hysteria 2 and TUIC protocols."
---

The root process and ShellClash installation for this router are well-documented here: https://qust.me/post/ax3600_shellclash/

I won't repeat those steps. Instead, I'll focus on how to replace the Clash-Meta core to support modern proxy protocols like Hysteria 2 and TUIC.

### 1. Download Clash-Meta
Download the appropriate version (arm64): [Clash.Meta Releases](https://github.com/MetaCubeX/Clash.Meta/releases). I personally use the Alpha version for the latest features.

### 2. The Storage Challenge
Here's the problem: The unzipped Clash-Meta binary is nearly 20MB, but the AX3600's root partition usually has less than 8MB left after installing ShellClash.

**Solution: UPX Compression**
Download [UPX](https://github.com/upx/upx) and compress the binary:
`upx -9 clash`

This reduces the size to under 7MB, making it easy to fit into the router's storage.

```shell
root@XiaoQiang:~# du -sh /data/clash/clash
6.6M    /data/clash/clash
root@XiaoQiang:~# /data/clash/clash -v
Clash Meta alpha-096bb8d linux arm64 with go1.19.5 Mon Jan 23 06:08:40 UTC 2023
```

### 3. Cleaning Up Logs
The default firmware has a habit of filling up `/data/usr/log` with junk files, which can cause network lag. It's best to set up a cron job to clear it regularly.

Add this to your crontab (`crontab -l`):
```shell
*/3 * * * * rm -rf /data/usr/log/*  # Clear junk logs every 3 minutes
30 3 * * 1~7 /data/clash/start.sh restart >/dev/null 2>&1 # Restart Clash daily at 3:30 AM
```

### 4. Performance Tip
Since Hysteria can be CPU-intensive, I recommend limiting the downlink speed (e.g., to 100 Mbps) to keep the router load manageable.

---
*Created: 2023-01-24*
*Updated: 2026-01-04*
