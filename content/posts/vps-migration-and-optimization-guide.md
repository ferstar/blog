---
title: "VPS 迁移与性能压榨手册 (Debian 13 + XanMod + 443 端口复用)"
slug: "vps-migration-and-optimization-guide"
date: "2026-01-20T10:00:00+08:00"
tags: ["VPS", "Debian", "Nginx", "Linux", "Optimization"]
---

本文档记录了从 DigitalOcean 旧主机 (Ubuntu 20.04) 到新主机 (Debian 13 + XanMod) 的迁移过程及调优细节。

起因是原本 $6/mo 的实例（1GB RAM / 20GB DISK / 1TB BW）资源长期闲置，于是决定顺应“消费降级”的大潮，降配至 $4/mo 方案（512MB RAM / 10GB DISK / 500GB BW），怒省 1/3 的开销，性价比瞬间拉满。

如今博客已托管至“赛博菩萨” Cloudflare Pages，这台 512MB 的小鸡便能卸下重担，转而专职负责备用梯子和吃灰的公众号后台。虽然内存配置直接腰斩，让资源变得捉襟见肘，但在一番极限性能压榨下，这台小机器跑起来依然稳如老狗。

## 1. 基础环境
- **源主机 (Source)**: DigitalOcean Ubuntu 20.04 (IP 已隐藏)
- **新主机 (Target)**: DigitalOcean Debian 13 Trixie (IP 已隐藏)
- **Reserved IP**: 已挂载至新主机，用于 DNS 解析。
- **Hostname / PTR**: `ferstar.org` (通过重命名 DigitalOcean Droplet 自动触发 PTR 生成)。

## 2. 内核与内存优化 (Kernel 6.18+)

### 2.1 升级 XanMod Edge
安装具备 BBRv3 和最新调度特性的内核：
```bash
wget -qO - https://dl.xanmod.org/archive.key | gpg --dearmor | tee /usr/share/keyrings/xanmod-archive-keyring.gpg > /dev/null
echo 'deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main' | tee /etc/apt/sources.list.d/xanmod-kernel.list
apt update && apt install linux-xanmod-edge-x64v3 -y
```

### 2.2 内存压榨与持久化 (zswap + MGLRU + KSM)
针对 512MB RAM 的极限优化。由于部分内核参数不支持 `sysctl` 直接持久化，统一通过 `crontab` 的 `@reboot` 机制在开机时强制注入：

**持久化指令 (`crontab -e`):**
```bash
# 开启 MGLRU 所有优化层，显著降低小内存下的 OOM 风险
@reboot echo 7 > /sys/kernel/mm/lru_gen/enabled

# 开启 KSM 内存页合并，减少 Docker 容器间的重复内存占用
@reboot echo 1 > /sys/kernel/mm/ksm/run

# 开启 zswap 收缩器，允许内核更积极地在压缩区与物理 Swap 间平衡数据
@reboot echo Y > /sys/module/zswap/parameters/shrinker_enabled
```

**其他参数:**
- **zswap**: 开启内存压缩缓存，当前使用 **lzo** 算法。
- **Swap**: 1GB 物理文件兜底。

## 3. 网络架构：443 端口全能复用 (SNI Proxy)

利用 Nginx 1.29.4 (Mainline) 的 `stream` 模块实现基于域名的流量分流：

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

### 3.2 架构优势
- **极简防火墙**: 对外只需暴露一个 443 端口即可承载多种协议（HTTP/SSH/Proxy）。
- **安全性**: 隐藏了 SSH (22) 等敏感端口，有效对抗暴力破解扫描。
- **协议共存**: 真正的协议分流，不影响标准 HTTPS 访问，绕过严苛网络环境。

### 3.3 异步 IO 优化
在 `http` 块中启用线程池异步 IO，避免大文件读写阻塞主进程：
- `aio threads;`
- `thread_pool default threads=32 max_queue=65536;`
- `directio 4m;`

## 4. 防火墙配置 (UFW)

实施最小化端口开放策略，关闭 22 端口入站（由 443 转发替代）：
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

## 5. Let's Encrypt 泛域名证书管理

### 5.1 DNS 验证配置 (Cloudflare)
泛域名证书 (`*.ferstar.org`) 采用 `dns-cloudflare` 插件自动续期。
- **凭证文件**: `/root/certbot-creds.ini` (包含 CF API Token)。
- **插件安装**: `apt install python3-certbot-dns-cloudflare -y`。

### 5.2 自动续期逻辑
续期配置位于 `/etc/letsencrypt/renewal/ferstar.org.conf`：
```bash
post_hook = systemctl reload nginx && docker restart hysteria hysteria2 tuic-server
```

## 6. 应用配置模板

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
