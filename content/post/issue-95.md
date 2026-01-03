---
title: "基于 Teleport + Tailscale 的 GPU 集群访问控制与审计实战"
date: "2026-01-03T03:58:20+08:00"
tags: ['Linux', 'Idea']
comments: true
---

## 0. 背景：高价值资产的访问瓶颈
在管理 **DGX H800** 等核心算力资源时，运维团队面临着极其复杂的情况：
- **物理隔离**：计算节点位于严格受限的私有云内网。
- **跨境访问**：管理终端与服务器分布在不同地域。
- **合规审计**：外部供应商（Vendor）介入安装平台软件时，必须实现全程可追溯。

为了平衡“接入便利性”与“安全审计强度”，我们通过 **Teleport** 与 **Tailscale** 落地了一套零信任架构下的堡垒机方案。
---

## 附录：生产级配置文件参考（脱敏）

### A. Docker Compose 配置 (docker-compose.yml)
为实现“内外解耦”，监听地址保持为 `0.0.0.0`。安全策略由宿主机 `iptables` (DOCKER-USER 链) 统一管控。

```yaml
services:
  teleport:
    image: public.ecr.aws/gravitational/teleport-distroless:18.6.0
    container_name: teleport
    restart: always
    ports:
      - '3080:3080' # Web UI / Proxy
      - '3023:3023' # SSH Proxy
      - '3024:3024' # Reverse Tunnel
      - '3025:3025' # Auth API
    volumes:
      - ./data:/var/lib/teleport
      - ./teleport.yaml:/etc/teleport/teleport.yaml
    networks:
      - teleport-net
```

### B. IPTables 安全加固 (DOCKER-USER)
这是拦截公网探测同时保证内网连通性的核心指令。

```bash
# 1. 允许本地回环 (Nginx -> Teleport)
iptables -I DOCKER-USER -i lo -p tcp --dport 3022:3080 -j ACCEPT

# 2. 允许 Tailscale 网段 (GPU Nodes -> Teleport)
iptables -I DOCKER-USER -i tailscale0 -p tcp --dport 3022:3080 -j ACCEPT

# 3. 拦截公网接口入站请求 (ens3)
iptables -A DOCKER-USER -i ens3 -p tcp --dport 3022:3080 -j DROP
```

### C. Teleport 核心配置 (teleport.yaml)
```yaml
version: v3
teleport:
  nodename: bastion-host
auth_service:
  enabled: yes
  cluster_name: prod-cluster
  proxy_listener_mode: multiplex
proxy_service:
  enabled: yes
  # 关键：同时声明域名地址与内网管理地址
  public_addr: [teleport.example.com:443, 100.64.0.x:3080]
ssh_service:
  enabled: "no" # 禁用堡垒机自身的 SSH 接口
```



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2026-01-03T03:58:20+08:00
Updated at: 2026-01-03T04:02:25+08:00
Origin issue: https://github.com/ferstar/blog/issues/95
```
