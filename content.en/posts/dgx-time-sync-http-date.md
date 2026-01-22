---
title: "Who Would've Thought: Still Using Crontab + HTTP Header for Time Sync in 6202"
slug: "crontab-http-header-time-sync"
date: "2026-01-22T14:30:00+08:00"
tags: ["time-sync","teleport","prometheus","ops","troubleshooting"]
description: "Isolated environment blocked UDP, NTP failed, Prometheus reported 38-second time drift, Teleport handshake failed. Ended up manually syncing clocks via HTTP Date Header + Crontab."
---

> I am not a native English speaker; this article was translated by AI.

## Here's What Happened

January 21, 2026. target cluster triggered alerts.

Prometheus error: `Warning: Error fetching server time: Detected 38.116000175476074 seconds time difference between your browser and the server.` 38 seconds—not huge, not tiny—but enough to break Teleport's security handshake.

Worse, target02 went completely dark—Teleport handshake failed, SSH unreachable.

## Troubleshooting Journey

### Step 1: Suspected Network Issues

Probed jump host connectivity from target01:

```bash
# TCP scan (OK)
for port in 22 80 8888; do nc -zv -w 2 100.64.0.5 $port; done

# UDP scan (something's off)
nc -uvz -w 2 100.64.0.5 8888  # shows success, but no return packets
```

TCP works. UDP looks like it works but packets vanish. Anyone who's dealt with isolated environments knows what that means.

### Step 2: Packet Capture Confirmed

Started packet capture on jump host (jump-host) while sending UDP from target01:

```bash
# jump-host
sudo tcpdump -i any udp port 8888 -n

# target01
nc -u 100.64.0.5 8888 <<< "test"
```

Result: Jump host captured zero UDP packets. UDP blocked at network layer.

### Step 3: Checked Proxy Configuration

```bash
curl -v http://100.64.0.5:8888
# Response: < Proxy-Agent: gost/2.12.0
```

Port 8888 runs gost proxy, but it's TCP-only. UDP? Not welcome here.

## The Real Culprit: Clock Drift

After circling back, the root cause surfaced—target node clocks were way off:

- **target01**: ~38 seconds behind, Prometheus charts had gaps and query offsets
- **target02**: Worse drift, Teleport security check failed immediately

No NTP available (isolated environment, UDP port 114 won't pass). chrony was spinning wheels doing nothing.

## Solution: HTTP Date Header Manual Sync

### Step 1: Disable Broken chrony

```bash
systemctl stop chronyd
systemctl disable chronyd
```

### Step 2: Manually Align Clock

The jump host's port 80 HTTP response has a `Date` field in the header. Precision is only to the second, but better than nothing:

```bash
# Extract Date from HTTP header and set system time
HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-)
[ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"
```

You read that right. In 2026, I'm syncing clocks with `curl` + `date -s`. Last time I did this was on OpenWrt, over a decade ago.

### Step 3: Persist with Crontab

Configure hourly sync on target01 and target02:

```bash
(crontab -l 2>/dev/null; echo '0 * * * * HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-) && [ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"') | crontab -
```

## Takeaways

1. **No NTP in isolated environments is common**. When UDP is blocked, HTTP is the fallback channel.

2. **Non-standard ports are traps**. Port 8888 is configured in gost, but target clients don't have the tunnel config, so direct UDP access is doomed.

3. **Prometheus is extremely sensitive to time drift**. Time sync robustness matters more than you'd think in large clusters.

---

Looking back at this whole flow: disable chrony → curl HTTP header → date set → crontab schedule. The whole chain reeks of "make it work" pragmatism.

Next isolated environment deployment, maybe I should wrap HTTP Date sync into a systemd timer? Sounds like a plan.