---
title: "Solving Google Scholar Access Block"
slug: "resolve-google-scholar-with-ipv6-only"
date: 2018-03-08T09:49:42+08:00
tags: ['Linux', 'Idea']
comments: true
---

If you are still struggling with Google Scholar "Bot Verification" (Captcha) on your VPS, the 2018 method of manually editing `/etc/hosts` has become obsolete. The most reliable and low-maintenance solution today is leveraging **Cloudflare WARP**.

### The Logic
By installing the WARP client, you provide your VPS with a clean, high-reputation outbound IP address (dual-stack). Combined with modern routing tools like Xray or Sing-box, you can selectively route academic traffic through the WARP tunnel.

1. **Install WARP Client**
   Use the official Cloudflare repository for stability:
   ```bash
   curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ focal main" | tee /etc/apt/sources.list.d/cloudflare-client.list
   apt update && apt install cloudflare-warp
   ```

2. **Configure Split Routing (e.g., Sing-box)**
   Force `scholar.google.com` traffic to use the WARP outbound, prioritizing IPv6 where available.
   ```json
   {
     "outbounds": [
       { "type": "wireguard", "tag": "warp-out", ... }
     ],
     "route": {
       "rules": [
         {
           "domain_suffix": [ "scholar.google.com", "scholar.google.com.hk" ],
           "outbound": "warp-out"
         }
       ]
     }
   }
   ```

### Why this works?
- **Zero Maintenance**: No need to manually update IPv6 addresses when Google's CDN nodes rotate.
- **High Reputation**: WARP's IP ranges are generally considered "clean" by Google, significantly reducing Captcha frequency.

---

### Legacy Version (Just For Reference)

Google Scholar blocked most of DigitalOcean VPS IP(IPv4), so you should 
use IPv6 to access Google Scholar instead.

via: https://github.com/shadowsocks/shadowsocks-libev/issues/113

> OS: Ubuntu 16.04.3 LTS
> ss version: shadowsocks-libev 3.1.3

- **Configure shadowsocks-libev**
  Edit `/etc/default/shadowsocks-libev`:
```bash
# add '-6' to resolve hostname to IPv6 address first
DAEMON_ARGS="-u -6" 
```

- **Enable IPv6 in config**
  Edit `/etc/shadowsocks-libev/config.json`:
```json
"dns_ipv6": true
```

- **Manual DNS Override**
  Edit `/etc/hosts`:
```text
## Scholar
## type 'host google.com' to get the correct ipv6 address
2607:f8b0:4005:804::200e scholar.google.com
2607:f8b0:4005:804::200e scholar.l.google.com
```

- `systemctl restart shadowsocks-libev`
