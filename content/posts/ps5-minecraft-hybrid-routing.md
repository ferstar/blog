---
title: "PS5 Minecraft 卡在“正在加载”：把微软 HTTPS 和游戏 UDP 拆开走"
slug: "ps5-minecraft-hybrid-routing"
date: "2026-07-16T10:00:00+08:00"
tags: ['Networking', 'OpenWrt', 'Gaming']
description: "PS5 上的 Minecraft 长时间卡在“正在加载”；用抓包定位到微软/Azure 的 HTTPS 建连慢，只代理该主机的 TCP 443，保留 DNS 与 UDP 19132 直连后恢复正常。"
series: ['Home Network']
---

这次问题的表象很像“Minecraft 联机坏了”：PS5 能上网，商店和账号也没报错，但 Minecraft 进到服务器/联机相关页面后，经常长时间停在“正在加载”。

一开始自然会怀疑 DNS、IPv6、BedrockConnect，甚至局域网里的 Geyser。最后都不是根因。

真正有效的改法很小：**只让这台 PS5 的 TCP 443 走 ShellCrash；DNS 和 Minecraft 的 UDP 19132 保持直连。**

{{< mermaid >}}
flowchart LR
  P[PS5] -->|TCP 443: Microsoft / Azure auth and resources| C[ShellCrash proxy]
  P -->|UDP 19132: Minecraft game traffic| I[Direct Internet]
  P -->|DNS| D[Normal DNS]
{{< /mermaid >}}

## 先别急着改 DNS

BedrockConnect 解决的是“主机版基岩版怎样填自定义服务器”的入口问题，不是 Minecraft 加载慢的通用解法。DNS 被路由器、透明代理或 IPv6 改写时，确实可能让它不生效；但这次即使完全回到默认 DNS，加载问题仍在。

也不要先把整台 PS5 全局代理。Minecraft 的控制面和游戏数据面不是一回事：

- 登录、授权、皮肤与资源下载主要是 TCP 443；
- 实际联机游戏是 UDP，基岩版默认端口通常为 19132；
- DNS 是另一个独立变量。

全局代理看起来省事，实际上容易把 UDP、局域网发现和 MTU 问题一起带进来，排查面会迅速变大。

## 这次是怎样定位的

先看了三层事实。

第一层，路由器本身没有压力，PS5 到路由器的 Wi‑Fi 连续 ping 无丢包、延迟在几毫秒内。局域网不是瓶颈。

第二层，路由器直连访问微软授权端点时，IPv4 和 IPv6 的 HTTPS 都能完成；这说明不是“微软服务被完全封死”。

第三层，抓 PS5 的包时，加载阶段出现的是对 Microsoft/Azure 授权与资源域名的 DNS、TCP 443 与 TLS 流量；并没有进入持续的 Minecraft UDP 游戏流。更关键的是，PS5 发出 SYN 后，Azure 的 SYN-ACK 要一秒多才回来。

这把问题从“游戏服务器不可达”缩小成了“这条直连到微软/Azure 的 HTTPS 路径质量差”。路由器正常、游戏 UDP 也还没开始，应该只优化这条控制面路径。

## 最终规则：按 MAC 精确分流

下面是 OpenWrt + ShellCrash 的最小规则。把 `PS5_MAC` 换成 PS5 的 MAC，把 `REDIR_PORT` 换成 ShellCrash 的 redir port（本机实际监听的端口）。规则同时覆盖 IPv4 与 IPv6。

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

这段脚本有三个刻意的限制：

1. 只匹配一台设备的 MAC，不影响家里其他设备；
2. 只匹配 TCP 443，不碰 UDP 19132；
3. 先删除旧规则再插入，重复执行不会不断叠加相同规则。

如果 ShellCrash 给这台 PS5 配过“绕过代理”的 MAC 白名单，也不矛盾：让它继续绕过 ShellCrash 的通用链即可。这条规则插在 `PREROUTING` 顶部，专门把 TCP 443 送进 redir port；其余流量仍按原来的直连策略走。

## 持久化比临时生效更重要

手工插进去的 `iptables` 规则会在重启、重载防火墙或 ShellCrash 重新初始化后消失。我的做法是把脚本放在 ShellCrash 的任务目录，并让启动和防火墙钩子都调用它：

```text
/userdisk/data/ShellCrash/task/ps5-minecraft-hybrid-proxy.sh
/userdisk/data/ShellCrash/task/afstart
/userdisk/data/ShellCrash/task/affirewall
```

不同固件的目录或钩子名可能不同，重点不是硬抄路径，而是确认两件事：ShellCrash 启动后会执行一次，防火墙重载后也会执行一次。

每次改完，至少验证下面三项：

```sh
iptables -t nat -vnL PREROUTING
ip6tables -t nat -vnL PREROUTING
ss -lntp | grep 7892
```

应该能看到按 PS5 MAC 命中的 443 重定向规则，以及 redir port 正在监听。然后完全退出并重开 Minecraft；如果仍缓存旧会话，再重启 PS5。

## 不要留下已经证伪的规则

排查期间试过 DNS 改写、端口转发和局域网服务器重定向。确认它们不是当前问题后，应当全部删掉，而不是“先留着也许有用”。特别是把 UDP 19132 DNAT 到局域网某台机器的规则：一旦目标服务没有运行，它会制造一个很像网络故障的黑洞。

最后留下的配置只有一句话：**微软控制面走代理，Minecraft UDP、DNS 和局域网流量保持直连。**

这种混合路由比“关 IPv6”或“整机代理”更容易解释，也更容易回滚。以后如果症状变化，只要抓包先判断它卡在授权 HTTPS 还是已经进入 UDP 游戏流，再决定该动哪一层。
