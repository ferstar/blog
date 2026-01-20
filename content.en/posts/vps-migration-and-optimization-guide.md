---
title: "VPS Migration and Performance Squeezing Guide (Debian 13 + XanMod + Port 443 Multiplexing)"
slug: "vps-migration-and-optimization-guide"
date: "2026-01-20T10:00:00+08:00"
tags: ["VPS", "Debian", "Nginx", "Linux", "Optimization"]
description: "A low-memory VPS struggles after migration; use XanMod, kernel/memory tuning, and port 443 multiplexing to keep services stable on a smaller plan."
---

> I am not a native English speaker; this article was translated by AI.

This guide records the migration process and optimization details from an old DigitalOcean host (Ubuntu 20.04) to a new host (Debian 13 + XanMod).

It all started when I realized my $6/mo instance (1GB RAM / 20GB DISK / 1TB BW) was idle most of the time. To follow the belt-tightening trend, I moved to the $4/mo plan (512MB RAM / 10GB DISK / 500GB BW), cutting the cost by a solid third.

Now that my blog is hosted on "Cyber Bodhisattva" (Cloudflare Pages), this 512MB droplet has been relieved of its heavy lifting. It now serves as a backup proxy and a dormant WeChat public account backend. Even though the RAM is cut in half, after some serious performance squeezing, the little machine still runs rock-solid.

## 1. Basic Environment
- **Source Host**: DigitalOcean Ubuntu 20.04 (IP hidden)
- **Target Host**: DigitalOcean Debian 13 Trixie (IP hidden)
- **Reserved IP**: Attached to the new host for DNS resolution.
- **Hostname / PTR**: `ferstar.org` (automatically triggered by renaming the DigitalOcean Droplet).

## 2. Kernel and Memory Optimization (Kernel 6.18+)

### 2.1 Upgrade to XanMod Edge
Install a kernel with BBRv3 and the latest scheduling features:
```bash
wget -qO - https://dl.xanmod.org/archive.key | gpg --dearmor | tee /usr/share/keyrings/xanmod-archive-keyring.gpg > /dev/null
echo 'deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main' | tee /etc/apt/sources.list.d/xanmod-kernel.list
apt update && apt install linux-xanmod-edge-x64v3 -y
```
Note: `linux-xanmod-edge-x64v3` requires a CPU that supports the x86-64-v3 instruction set. If not supported, use `linux-xanmod-edge-x64v2` or `linux-xanmod-edge-x64`.

### 2.2 Memory Squeezing and Persistence (zswap + MGLRU + KSM)
An extreme tuning set for 512MB RAM. Since some kernel parameters do not support direct persistence via `sysctl`, they are forced at boot via `crontab`'s `@reboot`:

**Persistence Commands (`crontab -e`):**
```bash
# Enable all MGLRU optimization tiers to significantly reduce OOM risk under low memory
@reboot echo 7 > /sys/kernel/mm/lru_gen/enabled

# Enable KSM memory page merging to reduce duplicate memory usage between Docker containers
@reboot echo 1 > /sys/kernel/mm/ksm/run

# Enable zswap shrinker to allow the kernel to balance data more aggressively between the compressed area and physical Swap
@reboot echo Y > /sys/module/zswap/parameters/shrinker_enabled
```

**Other Parameters:**
- **zswap**: Enabled memory compression cache, currently using the **lzo** algorithm.
- **Swap**: 1GB physical file as a fallback.

## 3. Network Architecture: All-in-One Port 443 Multiplexing (SNI Proxy)

Using the `stream` module of Nginx 1.29.4 (Mainline) to implement domain-based traffic steering:

### 3.1 Nginx Global Configuration (`/etc/nginx/nginx.conf`)
```nginx
stream {
    map $ssl_preread_server_name $stream_map {
        api.ferstar.org api;   # WeChat Bot -> Forward to local 8444
        fm.ferstar.org  fm;    # File Server -> Forward to local 8445
        default         ssh;   # Non-SSL or unknown domain defaults to local 22 (SSH)
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

### 3.2 Architectural Advantages
- **Minimal Firewall**: Only one port 443 needs to be exposed to the outside to carry multiple protocols (HTTP/SSH/Proxy).
- **Security**: Hides sensitive ports like SSH (22), effectively countering brute-force scanning.
- **Protocol Coexistence**: True protocol steering without affecting standard HTTPS access, bypassing strict network environments.

### 3.3 Async IO Optimization
Enable thread-pool async IO in the `http` block to prevent large file read/write from blocking the main process:
- `aio threads;`
- `thread_pool default threads=32 max_queue=65536;`
- `directio 4m;`

## 4. Firewall Configuration (UFW)

Use a minimal port-opening strategy, closing inbound port 22 (replaced by 443 forwarding):
```bash
ufw reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw allow 18443:18445/udp  # For proxy services
ufw enable
```

## 5. Let's Encrypt Wildcard Certificate Management

### 5.1 DNS Verification Configuration (Cloudflare)
The wildcard certificate (`*.ferstar.org`) uses the `dns-cloudflare` plugin for automatic renewal.
- **Credential File**: `/root/certbot-creds.ini` (contains CF API Token).
- **Plugin Installation**: `apt install python3-certbot-dns-cloudflare -y`.

### 5.2 Auto-renewal
Renewal configuration is located at `/etc/letsencrypt/renewal/ferstar.org.conf`:
```bash
post_hook = systemctl reload nginx && docker restart hysteria hysteria2 tuic-server
```

## 6. Application Configuration Templates

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
