---
title: "Practical Guide: GPU Cluster Access Control and Auditing with Teleport + Tailscale"
slug: "teleport-tailscale-gpu-access"
date: "2026-01-03T03:58:20+08:00"
tags: ['Linux', 'Idea']
comments: true
description: "Vendors need access while audits must stay silent; use Teleport + Tailscale with multiplexing and bypass channels; achieve secure, low-friction GPU cluster access."
---

> I am not a native English speaker; this article was translated by AI.

There are several DGX H800 nodes in a private network. They are not public-facing, but vendors occasionally need remote access for troubleshooting. The requirements sound simple, until network paths and auditing get involved:

1. Vendors need to connect and do their work.
2. Sessions must be fully recorded, but the audit entry points should not be exposed to them.
3. Our own team still needs a direct path, without going through the bastion every single time.

The final setup is Teleport for bastion access and auditing, plus Tailscale for internal connectivity and an ops bypass path. These are the bits that tripped me up, recorded here so I do not step on the same rake again.

---

### The rough shape

{{< mermaid >}}
flowchart LR
  subgraph External[Public Users]
    Vendor[Vendor<br/>Web/SSH]
    AppUser[App User<br/>Web]
  end
  subgraph Ops[Internal Ops]
    Admin[Admin<br/>SSH Direct]
  end
  subgraph Edge[Public Edge]
    Nginx[Nginx 443]
    Teleport[Teleport Proxy 3080]
    FW[DOCKER-USER Firewall]
    Logs[(Session Recording/Logs)]
    ExitNode[Tailscale Exit Node]
  end
  subgraph Intranet[GPU Cluster]
    GPU[GPU Nodes]
    AppUI[App UI 32000]
  end

  Vendor -- HTTPS/SSH --> Nginx --> FW --> Teleport --> GPU
  AppUser -- HTTPS --> Nginx --> FW --> Teleport --> AppUI
  Admin -- SSH 22 --> TSUser[Internal Tailscale Node]
  TSUser -- Tailscale Tunnel --> ExitNode --> GPU
  Teleport --> Logs
{{< /mermaid >}}

---

### First, collapse the ports

Teleport uses a range of ports by default, roughly 3022-3080. That is fine in a small test, but once Nginx, Docker, and cloud firewall rules join the party, it becomes annoying fast.

Multiplexing lets HTTPS, SSH, and tunnel traffic share port 3080:

```yaml
# teleport.yaml
auth_service:
  proxy_listener_mode: multiplex
```

It uses ALPN to distinguish traffic types. The practical win is boring but useful: only one public-facing port to reason about.

---

### Installing the Agent in an isolated network: put the proxy in the repo file

The GPU nodes cannot reach the internet directly, so installing the Teleport Agent needs a proxy. I first configured the system proxy and still got certificate errors from `yum`/`dnf`. The missing piece was setting the proxy explicitly in the repo file:

```ini
# /etc/yum.repos.d/teleport.repo
[teleport]
proxy=http://[Bastion_VIP]:8888
```

This is not a glamorous problem, but it eats time. The error looks like TLS trouble, while the real issue is that the package manager is not using the proxy path you think it is using.

---

### Web Terminal disconnects immediately? Check Nginx WebSocket handling

When Nginx reverse-proxied the Teleport Web Terminal, the page loaded but the terminal disconnected as soon as it opened. These settings ended up being the minimum stable set:

```nginx
proxy_pass https://127.0.0.1:3080;  # MUST use https
proxy_ssl_verify off;                # For self-signed certs
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

The `https` in `proxy_pass` is easy to overlook. The UI loading successfully does not mean the terminal channel is healthy.

---

### Docker mapped ports may skip the INPUT chain you trusted

This was the scary one. I had written restrictions in the `INPUT` chain and assumed 3080 was internal-only. Docker-published ports enter through `DOCKER-USER`, so those old rules were mostly useless. Port 3080 was still exposed to the public internet.

Note: `-F` below flushes the `DOCKER-USER` chain. Do not blindly paste this into production. Back it up first, or use `-I` to insert rules in the right place.

My fixed version looked like this:

```bash
iptables -F DOCKER-USER
# Allow only localhost and Tailscale network
iptables -A DOCKER-USER -s 127.0.0.1 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -s 100.64.0.0/10 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 3080 -j DROP
```

---

### Do not point Nginx at the VPN IP unless you enjoy circular failures

At first I set the Nginx upstream to the Tailscale VPN IP. It looked tidy, but it created a circular dependency: if the VPN blipped, the management page went down too.

Changing it to `127.0.0.1` fixed that. Even if Tailscale is down, the public management entry still works, which is exactly what you want when you need to repair Tailscale.

---

### Permission split

| Role | Access Method | Auditing |
|:---|:---|:---|
| Admin | SSH Port 22 + Ed25519 Key | None |
| Vendor | Web Terminal | Full recording, recordings hidden from vendor |

The RBAC trick is to remove `audit` from the vendor's `restricted-dev` role, so they cannot see recordings or log pages.

One caveat: removing `audit` only changes visibility of recordings/logs. It does not guarantee that every recording banner disappears. Teleport behavior depends on version and configuration, so test this yourself before relying on the word "silent".

Two extra constraints are worth adding:

1. Vendors access only through Teleport Web/SSH; they do not get Tailscale.
2. Vendor roles restrict login users and visible nodes, with labels for isolation.

```yaml
# Example: node labels (vendor name redacted)
labels:
  vendor: vendor-x
  env: prod
```

```yaml
# Example: role constraints (vendor login + visible nodes)
kind: role
spec:
  allow:
    logins: ["vendor-user"]
    node_labels:
      vendor: "vendor-x"
  deny:
    logins: ["root"]
```

---

### Core config snippets

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

### App Access came later

**Expose apps (example)**

```yaml
app_service:
  enabled: "yes"
  apps:
  - name: app-ui
    uri: http://10.120.0.0:32000/
    public_addr: app-ui.example.com
```

**Proxy environment causing 503**

If the node has `HTTP_PROXY`, Teleport may try to reach internal apps through that proxy and return 503. Adding `NO_PROXY` in systemd is safer:

```ini
# /etc/systemd/system/teleport.service
Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,100.64.0.0/10"
```

**Nginx Host passthrough header**

For multi-subdomain access, do not forget the Host header:

```nginx
proxy_set_header Host $host;
```

---

With this setup, vendors work through the Web UI, internal ops connect directly over Tailscale, session recordings are kept, and the GPU cluster does not need to sit on the public internet.

Not elegant, but steady enough. For this kind of temporary-but-sensitive remote support, steady matters more than pretty.

---

```js
NOTE: I am not responsible for any expired content.
Created at: 2026-01-03T03:58:20+08:00
Updated at: 2026-01-03T05:55:29+08:00
Origin issue: https://github.com/ferstar/blog/issues/95
```
