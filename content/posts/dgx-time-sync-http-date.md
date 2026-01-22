---
title: "万万没想到 6202 年了我还用 crontab + HTTP Header 同步时钟"
slug: "crontab-http-header-time-sync"
date: "2026-01-22T14:30:00+08:00"
tags: ["time-sync","teleport","prometheus","ops","troubleshooting"]
description: "隔离环境 UDP 被拦截导致 NTP 失效，Prometheus 报错时间偏差 38 秒，Teleport 握手失败。最终用 HTTP Date Header + Crontab 定时任务手动对齐时钟。"
---

## 事情是这样的

2026 年 1 月 21 日，目标集群 集群告警了。

Prometheus 报错：`Warning: Error fetching server time: Detected 38.116000175476074 seconds time difference between your browser and the server.` 38 秒，说多不多说少不少，但足够让 Teleport 的安全校验挂掉。

更离谱的是，target02 直接失联了——Teleport 握手失败，根本连不上 SSH。

## 排查过程

### 第一步：以为是网络问题

在 target01 上探测跳板机的连通性：

```bash
# TCP 扫描（正常）
for port in 22 80 8888; do nc -zv -w 2 100.64.0.5 $port; done

# UDP 扫描（有猫腻）
nc -uvz -w 2 100.64.0.5 8888  # 显示 success，但收不到回程包
```

TCP 通，UDP 看起来通但数据包丢了。熟悉的配方，隔离环境的老朋友们都知道这意味着什么。

### 第二步：抓包确认

在跳板机（jump-host）开启抓包，同时从 target01 发送 UDP 包：

```bash
# jump-host 执行
sudo tcpdump -i any udp port 8888 -n

# target01 执行
nc -u 100.64.0.5 8888 <<< "test"
```

结果：跳板机侧完全没有捕获到任何 UDP 包。UDP 在隔离网络层被拦截了。

### 第三步：检查代理

```bash
curl -v http://100.64.0.5:8888
# 响应：< Proxy-Agent: gost/2.12.0
```

8888 端口是 gost 代理，但它主要处理 TCP 隧道。UDP？这儿不接待。

## 真正的凶手：时钟漂移

绕了一圈，问题根源浮出水面——目标节点的时钟已经飞了：

- **target01**：时钟滞后约 38 秒，Prometheus 图表数据断点、查询偏移
- **target02**：时钟偏移更严重，Teleport 安全校验直接 fail

没有 NTP（隔离环境 UDP 114 端口通不过），chrony 也在那儿干瞪眼。

## 解决方案：HTTP Date Header 手动同步

### 步骤一：禁用失效的 chrony

```bash
systemctl stop chronyd
systemctl disable chronyd
```

### 步骤二：手动对齐时钟

跳板机 80 端口的 HTTP 响应头里有个 `Date` 字段，虽然精度是秒级，但总比没有强：

```bash
# 提取 HTTP Header 中的 Date 字段并设置系统时间
HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-)
[ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"
```

没错，2026 年了，我还在用 `curl` + `date -s` 同步时钟。上次这么干还是在 OpenWrt 上，那已经是十多年前的事了。

### 步骤三：定时任务持久化

在 target01 和 target02 上配置每小时自动同步：

```bash
(crontab -l 2>/dev/null; echo '0 * * * * HTTP_DATE=$(curl -sI http://100.64.0.5 | grep -i "^Date:" | cut -d" " -f2-) && [ -n "$HTTP_DATE" ] && date -s "$HTTP_DATE"') | crontab -
```

## 教训

1. **隔离环境没有 NTP 是常态**。UDP 被拦截时，HTTP 是最后的安全通道。

2. **非标端口的陷阱**。8888 虽然在 gost 中配置了，但 目标 客户端没同步配置隧道，直接访问这个 UDP 端口必然失败。

3. **Prometheus 对时间极度敏感**。大规模集群里，时间同步的鲁棒性比想象中重要得多。

---

事后回想这套流程：禁用 chrony → curl HTTP Header → date 设置 → crontab 定时。整个链路充满了"能跑就行"的务实感。

下次再有隔离环境部署，或许该考虑把 HTTP Date 同步做成 systemd timer 服务？