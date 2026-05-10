---
title: "VPS Migration and Performance Squeezing Guide (Debian 13 + XanMod + Port 443 Multiplexing)"
slug: "vps-migration-and-optimization-guide"
date: "2026-01-20T10:00:00+08:00"
tags: ["VPS", "Debian", "Nginx", "Linux", "Optimization"]
description: "A low-memory VPS struggles after migration; use XanMod, kernel/memory tuning, and port 443 multiplexing to keep services stable on a smaller plan."
---

> I am not a native English speaker; this article was translated by AI.

This is a plain migration note: moving from an old DigitalOcean host (Ubuntu 20.04) to a new one (Debian 13 + XanMod).

The reason was also plain. My old $6/mo instance (1GB RAM / 20GB DISK / 1TB BW) was idle most of the time, and the blog had already moved to Cloudflare Pages, the reliable “cyber bodhisattva” in the corner. So I downgraded the Droplet to the $4/mo plan (512MB RAM / 10GB DISK / 500GB BW). Saving two dollars a month is not life-changing, but for this kind of tinkering, saving anything still feels like a win.

After the downgrade, this little VPS mainly runs a backup proxy and a half-asleep WeChat public account backend. 512MB RAM is not generous, so I also cleaned up the kernel, memory settings, Nginx port multiplexing, and certificate renewal while migrating.

## 1. Basic environment

- **Source Host**: DigitalOcean Ubuntu 20.04 (IP hidden)
- **Target Host**: DigitalOcean Debian 13 Trixie (IP hidden)
- **Reserved IP**: Attached to the new host for DNS resolution.
- **Hostname / PTR**: `ferstar.org` (automatically triggered by renaming the DigitalOcean Droplet).

## 2. Kernel and memory tuning (Kernel 6.18+)

### 2.1 Upgrade to XanMod Edge

For BBRv3 and newer scheduler features, I went straight to XanMod Edge:

```bash
wget -qO - https://dl.xanmod.org/archive.key | gpg --dearmor | tee /usr/share/keyrings/xanmod-archive-keyring.gpg > /dev/null
echo 'deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main' | tee /etc/apt/sources.list.d/xanmod-kernel.list
apt update && apt install linux-xanmod-edge-x64v3 -y
```

`linux-xanmod-edge-x64v3` requires x86-64-v3 CPU support. If the VPS does not support it, use `linux-xanmod-edge-x64v2` or `linux-xanmod-edge-x64` instead. No need to be heroic here.

### 2.2 The small-memory set: zswap + MGLRU + KSM

With only 512MB RAM, there is not much headroom, so the kernel needs a little help. I enabled MGLRU, KSM, and the zswap shrinker. Some of these parameters are awkward to persist through `sysctl`, so I put them in `crontab` with `@reboot`. Crude, but easy to inspect later.

**Persistence commands (`crontab -e`):**

```bash
# Enable all MGLRU optimization tiers to significantly reduce OOM risk under low memory
@reboot echo 7 > /sys/kernel/mm/lru_gen/enabled

# Enable KSM memory page merging to reduce duplicate memory usage between Docker containers
@reboot echo 1 > /sys/kernel/mm/ksm/run

# Enable zswap shrinker to allow the kernel to balance data more aggressively between the compressed area and physical Swap
@reboot echo Y > /sys/module/zswap/parameters/shrinker_enabled
```

Other settings:

- **zswap**: Enabled memory compression cache, currently using the **lzo** algorithm.
- **Swap**: 1GB physical file as a fallback.

## 3. Port 443 multiplexing (SNI proxy)

Fewer exposed ports usually means less daily noise. Here I use the `stream` module from Nginx 1.29.4 (Mainline) to route traffic by SNI. Unknown traffic falls back to SSH.

### 3.1 Nginx global config (`/etc/nginx/nginx.conf`)

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

The benefits are straightforward:

- the firewall only needs 80/443 exposed, so the rules stay clean
- SSH is not directly exposed on port 22, which cuts down scan noise
- HTTPS, SSH, and proxy services can share one entry point, which is handy on awkward networks

### 3.2 Async IO tuning

File serving still runs on this box, so I enabled thread-pool async IO in the `http` block to keep large file reads and writes from blocking workers:

- `aio threads;`
- `thread_pool default threads=32 max_queue=65536;`
- `directio 4m;`

## 4. Firewall config (UFW)

Inbound 22 is closed and handled through the 443 stream fallback. The rules are intentionally boring:

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

## 5. Let's Encrypt wildcard certificate

### 5.1 DNS validation (Cloudflare)

The wildcard certificate (`*.ferstar.org`) is renewed through the `dns-cloudflare` plugin.

- **Credential File**: `/root/certbot-creds.ini` (contains CF API Token).
- **Plugin Installation**: `apt install python3-certbot-dns-cloudflare -y`.

### 5.2 Post-renewal hook

The renewal config lives at `/etc/letsencrypt/renewal/ferstar.org.conf`. After a certificate update, reload Nginx and restart the containers that use the certificate:

```bash
post_hook = systemctl reload nginx && docker restart hysteria hysteria2 tuic-server
```

## 6. Application config templates

These templates are not trying to be a clever abstraction. They are here so the next migration has something concrete to compare against.

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

## Closing notes

There is nothing deep about this migration. The main idea was to rethink what the old VPS still needed to do: let Cloudflare Pages handle the blog, keep only the small services on the VPS, expose fewer ports, and squeeze memory where it is safe to do so. 512MB is still tight, but for these lightweight jobs it is enough.