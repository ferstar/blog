---
title: "VPS 迁移与性能压榨手册 (Debian 13 + XanMod + 443 端口复用)"
slug: "vps-migration-and-optimization-guide"
date: "2026-01-20T10:00:00+08:00"
tags: ["VPS", "Debian", "Nginx", "Linux", "Optimization"]
description: "小内存 VPS 迁移后性能吃紧，借助 XanMod、内核/内存调优与 443 端口复用方案，低配也能稳定跑服务。"
---

这篇记录一次很朴素的 VPS 迁移：从 DigitalOcean 老机器（Ubuntu 20.04）搬到新机器（Debian 13 + XanMod）。

起因也朴素：原来的 $6/mo 实例（1GB RAM / 20GB DISK / 1TB BW）大部分时间闲着，博客又已经搬到 Cloudflare Pages，当个“赛博菩萨”托着。于是我把 Droplet 降到 $4/mo（512MB RAM / 10GB DISK / 500GB BW），每月省两刀，听起来不多，但穷折腾嘛，省到就是赚到。

降配后这台小鸡主要负责备用梯子和一个半休眠的公众号后台。512MB 内存当然不宽裕，所以顺手把内核、内存、Nginx 端口复用和证书续期都整理了一遍。

## 1. 基础环境

- **源主机 (Source)**: DigitalOcean Ubuntu 20.04 (IP 已隐藏)
- **新主机 (Target)**: DigitalOcean Debian 13 Trixie (IP 已隐藏)
- **Reserved IP**: 已挂载至新主机，用于 DNS 解析。
- **Hostname / PTR**: `ferstar.org` (通过重命名 DigitalOcean Droplet 自动触发 PTR 生成)。

## 2. 内核与内存优化 (Kernel 6.18+)

### 2.1 升级 XanMod Edge

为了 BBRv3 和更新的调度特性，直接上 XanMod Edge：

```bash
wget -qO - https://dl.xanmod.org/archive.key | gpg --dearmor | tee /usr/share/keyrings/xanmod-archive-keyring.gpg > /dev/null
echo 'deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main' | tee /etc/apt/sources.list.d/xanmod-kernel.list
apt update && apt install linux-xanmod-edge-x64v3 -y
```

`linux-xanmod-edge-x64v3` 要求 CPU 支持 x86-64-v3 指令集。如果机器不支持，就换 `linux-xanmod-edge-x64v2` 或 `linux-xanmod-edge-x64`，别硬装。

### 2.2 小内存三件套：zswap + MGLRU + KSM

512MB 内存没什么余量，只能让内核尽量会过日子。这里开了 MGLRU、KSM 和 zswap shrinker。部分参数不适合直接用 `sysctl` 持久化，我就放到 `crontab` 的 `@reboot` 里，简单粗暴但好查。

**持久化指令 (`crontab -e`):**

```bash
# 开启 MGLRU 所有优化层，显著降低小内存下的 OOM 风险
@reboot echo 7 > /sys/kernel/mm/lru_gen/enabled

# 开启 KSM 内存页合并，减少 Docker 容器间的重复内存占用
@reboot echo 1 > /sys/kernel/mm/ksm/run

# 开启 zswap 收缩器，允许内核更积极地在压缩区与物理 Swap 间平衡数据
@reboot echo Y > /sys/module/zswap/parameters/shrinker_enabled
```

其他配置：

- **zswap**: 开启内存压缩缓存，当前使用 **lzo** 算法。
- **Swap**: 1GB 物理文件兜底。

## 3. 443 端口复用 (SNI Proxy)

对外暴露的端口越少，维护起来越省事。这里用 Nginx 1.29.4 (Mainline) 的 `stream` 模块，根据 SNI 把流量分到不同后端；未知流量默认丢给 SSH。

### 3.1 Nginx 全局配置 (`/etc/nginx/nginx.conf`)

```nginx
stream {
    map $ssl_preread_server_name $stream_map {
        api.ferstar.org api;   # 微信机器人 -> 转发至本地 8444
        fm.ferstar.org  fm;    # 文件服务器 -> 转发至本地 8445
        default         ssh;   # 非 SSL 或未知域名默认转发至本地 22 (SSH)
    }
    upstream ssh  { server 127.0.0.1:22; }
    upstream api  { server 127.0.0.1:8444; }
    upstream fm   { server 127.0.0.1:8445; }
    
    server {
        listen 443 reuseport;
        proxy_pass $stream_map;
        ssl_preread on;
    }
}
```

这样做的好处很直接：

- 防火墙只放 80/443，规则清爽很多
- SSH 不直接暴露在 22 端口，少吃一堆扫描
- HTTPS、SSH 和代理类服务可以共用入口，出门在外也少一点玄学问题

### 3.2 异步 IO 优化

文件服务还在这台机子上跑，所以在 `http` 块里开了线程池异步 IO，避免大文件读写卡住 worker：

- `aio threads;`
- `thread_pool default threads=32 max_queue=65536;`
- `directio 4m;`

## 4. 防火墙配置 (UFW)

22 入站关掉，由 443 stream 转发兜底。规则保持够用就行：

```bash
ufw reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw allow 18443:18445/udp  # 供代理服务使用
ufw enable
```

## 5. Let's Encrypt 泛域名证书

### 5.1 DNS 验证 (Cloudflare)

泛域名证书 (`*.ferstar.org`) 用 `dns-cloudflare` 插件续期。

- **凭证文件**: `/root/certbot-creds.ini` (包含 CF API Token)。
- **插件安装**: `apt install python3-certbot-dns-cloudflare -y`。

### 5.2 自动续期后置动作

续期配置在 `/etc/letsencrypt/renewal/ferstar.org.conf`，证书更新后重载 Nginx，并重启几个用证书的容器：

```bash
post_hook = systemctl reload nginx && docker restart hysteria hysteria2 tuic-server
```

## 6. 应用配置模板

下面这些配置没做太多“抽象封装”，主要图个迁移时能直接对照。

### 6.1 Hysteria v1

**`docker-compose.yml`**

```yaml
services:
  hysteria:
    image: tobyxdd/hysteria:v1.3.5
    container_name: hysteria
    logging:
      driver: "json-file"
      options: {max-size: "10m", max-file: "3"}
    restart: unless-stopped
    command: ["-config", "/etc/config.json", "server"]
    volumes:
      - ./config.json:/etc/config.json
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports: ["18443:443/udp"]
    sysctls: {net.ipv4.tcp_congestion_control: bbr}
```

**`config.json`**

```json
{
  "listen": ":443",
  "cert": "/etc/letsencrypt/live/DOMAIN/fullchain.pem",
  "key": "/etc/letsencrypt/live/DOMAIN/privkey.pem",
  "auth": { "mode": "passwords", "config": ["PASSWORD"] },
  "up_mbps": 1000,
  "down_mbps": 1000
}
```

### 6.2 Hysteria v2

**`docker-compose.yml`**

```yaml
services:
  hysteria2:
    image: tobyxdd/hysteria:latest
    container_name: hysteria2
    restart: unless-stopped
    command: ["server", "-c", "/etc/hysteria/config.yaml"]
    logging:
      driver: "json-file"
      options: {max-size: "10m", max-file: "3"}
    volumes:
      - ./config.yaml:/etc/hysteria/config.yaml:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports: ["18445:443/udp"]
    sysctls: {net.ipv4.tcp_congestion_control: bbr}
```

**`config.yaml`**

```yaml
listen: :443
tls:
  cert: /etc/letsencrypt/live/DOMAIN/fullchain.pem
  key: /etc/letsencrypt/live/DOMAIN/privkey.pem
auth:
  type: password
  password: "PASSWORD"
bandwidth:
  up: 1 gbps
  down: 1 gbps
```

### 6.3 TUIC v5

**`docker-compose.yml`**

```yaml
services:
  tuic:
    image: ghcr.io/itsusinn/tuic-server:1.4.5
    container_name: tuic-server
    logging:
      driver: "json-file"
      options: {max-size: "10m", max-file: "3"}
    restart: always
    ports: ["18444:443/udp"]
    volumes:
      - ./config.json:/etc/tuic/config.json:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
```

**`config.json`**

```json
{
    "server": "[::]:443",
    "users": { "UUID": "PASSWORD" },
    "certificate": "/etc/letsencrypt/live/DOMAIN/fullchain.pem",
    "private_key": "/etc/letsencrypt/live/DOMAIN/privkey.pem",
    "alpn": ["h3"],
    "udp_relay_ipv6": true,
    "zero_rtt_handshake": false,
    "dual_stack": true,
    "log_level": "warn"
}
```

### 6.4 Filebrowser

**`docker-compose.yml`**

```yaml
services:
  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    logging:
      driver: "json-file"
      options: {max-size: "10m", max-file: "3"}
    user: 0:0
    ports: ["127.0.0.1:1122:80"]
    volumes:
      - /root/fm/filebrowser/srv:/srv
      - /root/fm/filebrowser/database.db:/database.db
    command: ["--address", "0.0.0.0", "--port", "80", "--database", "/database.db", "--root", "/srv"]
    restart: unless-stopped
```

## 结尾

这次迁移没有什么高深操作，核心就是把旧机器上的职责重新盘一遍：博客外包给 Cloudflare Pages，小 VPS 只保留必要服务；能省的端口省掉，能压的内存压一下。512MB 当然谈不上宽裕，但跑这些轻量任务已经够用了。