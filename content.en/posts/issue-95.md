---
title: "Practical Guide: GPU Cluster Access Control and Auditing with Teleport + Tailscale"
slug: "teleport-tailscale-gpu-access"
date: "2026-01-03T03:58:20+08:00"
tags: ['Linux', 'Idea']
description: "How to manage secure remote access for GPU clusters (DGX H800) in isolated environments using Teleport as a bastion and Tailscale for tunneling, featuring silent session recording and audit bypass."
---

> I am not a native English speaker; this article was translated by AI.

I have several DGX H800 nodes in an internal network, and occasionally need to grant remote access to vendors for debugging. The requirements are simple:

1. Vendors must be able to connect and work.
2. Full session recording/auditing is required, but it should be "silent" (vendors shouldn't know they are being recorded).
3. Our internal team needs a privileged channel to bypass the bastion host and connect directly.

After some research, I chose **Teleport** as the bastion host and **Tailscale** to bridge the internal network tunnel. With AI's help for documentation and configuration, I got it running in about an hour. Here are the pitfalls I encountered and how I fixed them.

---

### Architecture in a Nutshell

```
Public User → Nginx(443) → Teleport Proxy(3080) → GPU Nodes
                                    ↑
                        Tailscale Tunnel bridges the internal network
```

---

### Pitfall 1: Too Many Ports

Teleport defaults to opening several ports (3022-3080), which makes firewall rules tedious. I discovered the **Multiplexing** mode, which solves this with a single port:

```yaml
# teleport.yaml
auth_service:
  proxy_listener_mode: multiplex
```

This uses the ALPN protocol to identify traffic types (HTTPS/SSH/Tunnel), all flowing through port 3080. One port to rule them all.

---

### Pitfall 2: Agent Installation Failures in Isolated Nodes

Installing the Teleport Agent on isolated GPU nodes requires a proxy. `yum` kept failing due to certificate errors. The fix was to explicitly configure the proxy in the repo file:

```ini
# /etc/yum.repos.d/teleport.repo
[teleport]
proxy=http://[Bastion_VIP]:8888
```

---

### Pitfall 3: WebSocket Disconnections

When using Nginx to reverse proxy the Teleport Web Terminal, the page would load but the terminal would disconnect instantly. Three specific Nginx settings are mandatory:

```nginx
proxy_pass https://127.0.0.1:3080;  # MUST use https
proxy_ssl_verify off;                # For self-signed certs
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

---

### Pitfall 4: Docker Ports Bypassing iptables

This is the most dangerous one. Ports mapped by Docker bypass the `INPUT` chain and go straight through `DOCKER-USER`. My previous rules were useless, leaving 3080 wide open to the public internet.

The fix:

```bash
iptables -F DOCKER-USER
# Allow only localhost and Tailscale network
iptables -A DOCKER-USER -s 127.0.0.1 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -s 100.64.0.0/10 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 3080 -j DROP
```

---

### Pitfall 5: Nginx Pointing to VPN IP Caused Circular Dependency

Earlier, I configured Nginx to use the Tailscale VPN IP. However, if the VPN flickered, the management page went down.

Switching to `127.0.0.1` (localhost) ensures that if the VPN goes down, the management console is still accessible from the public network.

---

### Permissions Design

| Role | Access Method | Auditing |
|:---|:---|:---|
| Admin | SSH Port 22 + Ed25519 Key | None |
| Vendor | Web Terminal | Full recording (hidden from vendor) |

RBAC Tip: Strip the `audit` permission from the vendor's `restricted-dev` role to achieve "silent auditing."

---

### Core Configuration

**docker-compose.yml**

```yaml
services:
  teleport:
    ports:
      - '3080:3080'
      - '127.0.0.1:3025:3025'  # Management API local only
```

**teleport.yaml**

```yaml
proxy_service:
  public_addr: [teleport.example.com:443, 100.64.0.x:3080]
```

---

With this setup, vendors work within the Web UI, while we maintain direct SSH access. Session recordings are available at any time, while the system remains invisible to the public internet.

Works for me.
