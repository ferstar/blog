---
title: "PS5 Minecraft Stuck on Loading: Split Microsoft HTTPS from Game UDP"
slug: "ps5-minecraft-hybrid-routing"
date: "2026-07-16T10:00:00+08:00"
tags: ['Networking', 'OpenWrt', 'Gaming']
description: "Minecraft on a PS5 stayed on the loading screen; packet capture showed slow Microsoft/Azure HTTPS setup, and proxying only TCP 443 while keeping DNS and UDP 19132 direct fixed it."
series: ['Home Network']
---

> I am not a native English speaker; this article was translated by AI.

The symptom looked like “Minecraft multiplayer is broken”: the PS5 had Internet access, the store and account did not show an error, but Minecraft would often sit on the loading screen for a long time when opening server or online-related pages.

The obvious suspects were DNS, IPv6, BedrockConnect, and even a Geyser instance on the LAN. None was the root cause.

The fix was small: **proxy TCP 443 only for this PS5 through ShellCrash; keep DNS and Minecraft UDP 19132 direct.**

{{< mermaid >}}
flowchart LR
  P[PS5] -->|TCP 443: Microsoft / Azure auth and resources| C[ShellCrash proxy]
  P -->|UDP 19132: Minecraft game traffic| I[Direct Internet]
  P -->|DNS| D[Normal DNS]
{{< /mermaid >}}

## Do not rush to change DNS

BedrockConnect solves an entry-point problem: how to enter a custom server on console Bedrock. It is not a general fix for slow Minecraft loading. DNS rewriting by the router, a transparent proxy, or IPv6 can certainly make it fail; but in this case the loading problem remained even after returning to default DNS.

Do not proxy the entire PS5 first, either. Minecraft's control plane and game data plane are different:

- sign-in, authorization, skins, and resource downloads are mostly TCP 443;
- actual multiplayer game traffic is UDP; Bedrock commonly uses port 19132;
- DNS is another independent variable.

Global proxying looks convenient, but it can drag UDP, LAN discovery, and MTU issues into the problem at once. The debugging surface gets much larger.

## How this was narrowed down

I checked three layers of evidence.

First, the router was not under load. Continuous Wi-Fi pings from the PS5 to the router had no loss and stayed within a few milliseconds. The LAN was not the bottleneck.

Second, direct HTTPS requests from the router to a Microsoft authorization endpoint completed over both IPv4 and IPv6. Microsoft services were not completely unreachable.

Third, packet capture during the loading stage showed DNS, TCP 443, and TLS traffic for Microsoft/Azure authorization and resource domains. It had not entered sustained Minecraft UDP game traffic. More importantly, after the PS5 sent a SYN, the SYN-ACK from Azure took more than a second to return.

That narrowed the issue from “the game server is unreachable” to “the direct path to Microsoft/Azure HTTPS is poor.” The router was healthy and game UDP had not started, so only that control-plane path needed optimization.

## Final rule: precise routing by MAC address

Here is the smallest rule set for OpenWrt plus ShellCrash. Replace `PS5_MAC` with the PS5 MAC address and `REDIR_PORT` with ShellCrash's redir port, the port actually listening on the router. The rules cover both IPv4 and IPv6.

```sh
#!/bin/sh

PS5_MAC='AA:BB:CC:DD:EE:FF'
REDIR_PORT='7892'

iptables -t nat -D PREROUTING -m mac --mac-source "$PS5_MAC" \
  -p tcp --dport 443 -j REDIRECT --to-ports "$REDIR_PORT" 2>/dev/null
iptables -t nat -I PREROUTING 1 -m mac --mac-source "$PS5_MAC" \
  -p tcp --dport 443 -j REDIRECT --to-ports "$REDIR_PORT"

ip6tables -t nat -D PREROUTING -m mac --mac-source "$PS5_MAC" \
  -p tcp --dport 443 -j REDIRECT --to-ports "$REDIR_PORT" 2>/dev/null
ip6tables -t nat -I PREROUTING 1 -m mac --mac-source "$PS5_MAC" \
  -p tcp --dport 443 -j REDIRECT --to-ports "$REDIR_PORT"
```

The script has three deliberate limits:

1. It matches one device MAC address only, so other devices are unaffected.
2. It matches TCP 443 only and leaves UDP 19132 alone.
3. It deletes the old rule before inserting the new one, so repeated runs do not accumulate duplicates.

It is also compatible with a ShellCrash MAC bypass for the PS5: leave the device bypassed from ShellCrash's general chain. This rule sits at the top of `PREROUTING` and sends TCP 443 specifically to the redir port; all other traffic still follows the original direct-routing policy.

## Persistence matters more than a temporary success

Manually inserted `iptables` rules disappear after a reboot, firewall reload, or ShellCrash reinitialization. I put the script in ShellCrash's task directory and called it from both a startup and firewall hook:

```text
/userdisk/data/ShellCrash/task/ps5-minecraft-hybrid-proxy.sh
/userdisk/data/ShellCrash/task/afstart
/userdisk/data/ShellCrash/task/affirewall
```

Directory and hook names differ by firmware. The important part is not copying these paths literally: run the script once after ShellCrash starts and once after the firewall reloads.

After each change, verify at least these three things:

```sh
iptables -t nat -vnL PREROUTING
ip6tables -t nat -vnL PREROUTING
ss -lntp | grep 7892
```

You should see a PS5-MAC-specific 443 redirect rule and a listening redir port. Then fully exit and reopen Minecraft; reboot the PS5 as well if it is still holding an old session.

## Remove rules that the evidence ruled out

During diagnosis I tried DNS rewriting, port forwarding, and LAN server redirection. Once they were shown not to be the current cause, they should all be removed instead of being kept “just in case.” In particular, a rule that DNATs UDP 19132 to a LAN host becomes a black hole when that target service is not running, and it looks exactly like a network failure.

The final configuration is one sentence: **proxy the Microsoft control plane; keep Minecraft UDP, DNS, and LAN traffic direct.**

This hybrid route is easier to explain and roll back than disabling IPv6 or proxying the whole console. If the symptoms change later, capture traffic first to see whether it is stuck on authorization HTTPS or has reached UDP game traffic, then change the matching layer only.
