---
title: "万万没想到 6202 年了我还用 crontab + HTTP Header 同步时钟"
slug: "crontab-http-header-time-sync"
date: "2026-01-22T14:30:00+08:00"
tags: ["time-sync","teleport","prometheus","ops","troubleshooting"]
description: "隔离环境拦了 UDP，NTP/chrony 对不上时钟，Prometheus 报 38 秒时间偏差，Teleport 握手失败；最后用 HTTP Date Header 加 crontab 把节点时间拉回可用范围。"
---

## 起因

2026 年 1 月 21 日，目标集群开始告警。

Prometheus 页面先报了一条时间偏差：`Warning: Error fetching server time: Detected 38.116000175476074 seconds time difference between your browser and the server.`

38 秒听着不大，放在 Prometheus 查询里足够让图表断层；放在 Teleport 这种带安全校验的链路里，就更够呛了。target02 当时已经连不上，Teleport 握手失败，SSH 也进不去。

## 先查网络

第一反应还是网络。先在 target01 上探测跳板机：

```bash
# TCP 扫描，正常
for port in 22 80 8888; do nc -zv -w 2 100.64.0.5 $port; done

# UDP 扫描，看起来通，但收不到回程包
nc -uvz -w 2 100.64.0.5 8888
```

TCP 没问题，UDP 的结果就比较可疑了。`nc -u` 这种检查本来就容易给人一种“通了”的错觉，实际包有没有到对端，还得抓一下。

跳板机上开 tcpdump，target01 发一个 UDP 包：

```bash
# jump-host
sudo tcpdump -i any udp port 8888 -n

# target01
nc -u 100.64.0.5 8888 <<< "test"
```

跳板机侧一个包都没看到，基本可以确认 UDP 在隔离网络里被挡掉了。

顺手看了下 8888：

```bash
curl -v http://100.64.0.5:8888
# < Proxy-Agent: gost/2.12.0
```

这是 gost 代理端口，主要走 TCP 隧道。UDP 没配通，指望它帮 NTP 续命不现实。

## 问题落到时钟上

绕了一圈，真正的问题还是时钟漂移：

- target01 慢了大概 38 秒，Prometheus 查询和图表开始飘。
- target02 偏得更厉害，Teleport 校验直接失败。

隔离环境里 NTP 出不去，chrony 也只是挂在那里努力失败。常规路子走不通，只能找一个环境里稳定可达、又能提供时间参考的东西。

刚好跳板机 80 端口能访问，HTTP 响应头里有 `Date`。

## 用 HTTP Date 先救回来

先停掉一直对不上的 chrony，免得它继续添乱：

```bash
systemctl stop chronyd
systemctl disable chronyd
```

然后从跳板机 HTTP Header 里取 `Date`，直接喂给 `date -s`：

```bash
HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-)
[ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"
```

这招很土，精度也就秒级，但当时先顾不上漂亮，目标是把 Teleport 拉回能握手的范围。实际执行完以后，Prometheus 的时间差告警消失，target02 也能重新连上。

没错，2026 年了，我还在用 `curl` + `date -s` 同步时钟。上次这么干大概还是折腾 OpenWrt 的时候。

## crontab 固化

临时救回来以后，还得防止它继续漂。先用 crontab 每小时拉一次：

```bash
(crontab -l 2>/dev/null; echo '0 * * * * HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-) && [ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"') | crontab -
```

这东西谈不上优雅，但在隔离环境里挺好使：只依赖 HTTP，只要跳板机可达，就能把时间控制在一个可接受的范围内。

## 记一笔

这次主要踩了几个点：

1. 隔离环境里别默认 NTP 可用。UDP 123 被拦以后，chrony 看起来在跑，实际一直对不上。
2. `nc -u` 的结果别太当真。UDP 没有握手，显示 success 不等于对端真的收到了包。
3. Prometheus 和 Teleport 都很吃时间一致性。几十秒的漂移，已经足够制造一堆看起来像网络问题的假象。

后面如果还要在类似环境里部署，我大概率会把这套 HTTP Date 同步收成一个 systemd timer。crontab 能救急，长期跑还是得稍微像个人样。
