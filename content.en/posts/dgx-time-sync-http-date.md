---
title: "Who would have thought: still using crontab + HTTP Header for time sync in 6202"
slug: "crontab-http-header-time-sync"
date: "2026-01-22T14:30:00+08:00"
tags: ["time-sync","teleport","prometheus","ops","troubleshooting"]
description: "An isolated network blocked UDP, NTP/chrony could not sync time, Prometheus reported a 38-second drift, and Teleport handshakes failed; HTTP Date Header plus crontab pulled the nodes back into a usable range."
---

> I am not a native English speaker; this article was translated by AI.

## What happened

On January 21, 2026, the target cluster started alerting.

Prometheus first showed a clock drift warning: `Warning: Error fetching server time: Detected 38.116000175476074 seconds time difference between your browser and the server.`

38 seconds does not sound like much. For Prometheus queries, it is enough to break charts. For something like Teleport, with security checks in the handshake path, it is even worse. target02 was already unreachable at that point: Teleport handshake failed, and SSH was gone with it.

## Checking the network first

The first suspect was still the network. I tested reachability from target01 to the jump host:

```bash
# TCP scan, OK
for port in 22 80 8888; do nc -zv -w 2 100.64.0.5 $port; done

# UDP scan, looks OK at first glance, but no packets come back
nc -uvz -w 2 100.64.0.5 8888
```

TCP was fine. UDP looked suspicious. `nc -u` can easily make this look "connected" when nothing useful actually reached the other side, so I had to capture packets.

I started tcpdump on the jump host and sent one UDP packet from target01:

```bash
# jump-host
sudo tcpdump -i any udp port 8888 -n

# target01
nc -u 100.64.0.5 8888 <<< "test"
```

The jump host saw nothing. That was enough to confirm UDP was blocked somewhere in the isolated network.

I also checked port 8888 while I was there:

```bash
curl -v http://100.64.0.5:8888
# < Proxy-Agent: gost/2.12.0
```

That port was a gost proxy, mostly for TCP tunnels. UDP was not wired through it, so it was not going to keep NTP alive.

## It came down to clock drift

After all that, the actual issue was still clock drift:

- target01 was about 38 seconds behind, enough to make Prometheus queries and charts go weird.
- target02 had drifted further, and Teleport rejected the handshake outright.

NTP could not get out of the isolated environment. chrony was running, but only in the sense that it was repeatedly failing. The normal path was dead, so I needed something reachable inside the environment that could still act as a time reference.

The jump host's port 80 was reachable, and HTTP responses have a `Date` header.

## Using HTTP Date to recover first

I stopped chrony first so it would not keep fighting the manual correction:

```bash
systemctl stop chronyd
systemctl disable chronyd
```

Then I pulled `Date` from the jump host's HTTP header and fed it straight into `date -s`:

```bash
HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-)
[ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"
```

It is crude. Precision is only seconds. But the goal at that moment was not elegance; it was getting Teleport back within handshake tolerance. After running it, the Prometheus clock drift warning cleared, and target02 became reachable again.

Yes, it is 2026 and I am still syncing clocks with `curl` + `date -s`. The last time I remember doing this was probably on OpenWrt.

## Making it stick with crontab

After the quick recovery, I still needed to stop the nodes from drifting again. I put the same sync into crontab and ran it hourly:

```bash
(crontab -l 2>/dev/null; echo '0 * * * * HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-) && [ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"') | crontab -
```

It is not pretty, but it works well enough in this environment. It only needs HTTP. As long as the jump host is reachable, the nodes stay within an acceptable time window.

## Notes for next time

A few things worth writing down:

1. Do not assume NTP works in isolated networks. Once UDP 123 is blocked, chrony can look alive while syncing nothing.
2. Do not trust `nc -u` too much. UDP has no handshake, so a success message does not mean the remote side received anything.
3. Prometheus and Teleport are both sensitive to clock drift. A few dozen seconds can easily create symptoms that look like network failures.

If I deploy into a similar environment again, I will probably turn this HTTP Date sync into a small systemd timer. crontab is fine for firefighting; long term, it deserves something slightly less feral.
