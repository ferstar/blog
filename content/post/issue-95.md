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

## 1. 架构逻辑：连通性与审计的分层解耦
我们将安全防线分为两层：
- **网络层（Tailscale）**：利用 Overlay 网络打通私有网段，隐藏物理拓扑。
- **协议层（Teleport）**：通过 SSH 证书化、指令级记录和会话录屏，实现对操作行为的闭环管理。
- **接入层（Nginx）**：收口到 443 端口，通过域名提供标准的 HTTPS 管理门户。

---

## 2. 部署实战：突破内网孤岛的连接
由于 GPU 节点无法直连中转节点，Agent 必须通过代理发起反向隧道请求。

### 2.1 强制代理环境下的 Agent 部署
在计算节点利用 `HTTP_PROXY` 指向中转节点的隧道端口。针对包管理器在代理环境下的证书或 403 权限问题，采用了显式 Repo Proxy 配置：
```bash
# /etc/yum.repos.d/teleport.repo
[teleport]
# ... 
proxy=http://[VIP_BASTION]:8888  # 确保包管理器的网络路径独立可控
```

### 2.2 公共地址映射（Public Addr）
为了解决登录后的域名/IP 跳转冲突，我们在中转机配置了多公共地址，同时兼顾了用户的域名访问与 Agent 的私网心跳：
```yaml
proxy_service:
  # 域名用于 Web 访问，IP 用于节点心跳
  public_addr: [teleport.example.com:443, 100.64.0.x:3080]
```

---

## 3. 安全模型：管理员与供应商的权限切割

### 3.1 管理员：高性能、免干预接入
管理员通过 **Ed25519 专用密钥** 走 22 端口直接访问。
- **零信任改造**：彻底禁用 root 密码，改为仅限证书/密钥验证。
- **体验优化**：利用 `~/.ssh/config` 别名配置，实现秒级免感登录，绕过堡垒机包装层以获取原生 Bash 性能。

### 3.2 外部供应商：强制收口、全量审计
外部人员统一分配 `dev` 账号，仅能通过 Web 端操作。
- **RBAC 定制**：创建 `restricted-dev` 角色，剥离审计日志查看权限。
- **效果**：操作人员仅能操作其授权范围内的节点，而管理员可作为 `auditor` 实时监控并回放所有历史会话。

---

## 4. 深度调优：Nginx 与防火墙的联动

### 4.1 Nginx 全流量转发
在 1Panel/OpenResty 环境下，Nginx 必须解决 WebTerminal 的长连接稳定性：
1. **SSL 协议透传**：`proxy_pass https://`（Teleport 强制加密）并开启 `proxy_ssl_verify off`。
2. **WebSocket 优化**：显式指定 `Upgrade` 和 `Connection` 头部，防止 Web Shell 意外断连。

### 4.2 IPTables 隐身术
针对 Docker 映射端口绕过普通防火墙的问题，我们在 **`DOCKER-USER`** 链执行了精准封锁：
```bash
# 仅允许本地 lo (Nginx) 和虚拟网卡 tailscale0 进入容器
iptables -I DOCKER-USER -i lo -p tcp --dport 3022:3080 -j ACCEPT
iptables -I DOCKER-USER -i tailscale0 -p tcp --dport 3022:3080 -j ACCEPT
# 拦截来自公网物理网卡 ens3 的所有入站尝试
iptables -A DOCKER-USER -i ens3 -p tcp --dport 3022:3080 -j DROP
```

---

## 5. 容灾设计：解除“循环依赖”
在早期配置中，Nginx 曾指向 Tailscale IP。为防止 VPN 服务自身异常导致管理入口全线崩溃，我们最终将转发目标改为 `127.0.0.1` 本地回环。

这种设计实现了**即便 Tailscale 网络波动，只要公网 443 畅通，管理员依然能进入堡垒机管理集群**的健壮架构。

---

## 结语
安全运维的本质并非堆砌工具，而是通过合理的架构设计，在不牺牲核心人员效率的前提下，建立起一套**透明且不可篡改的操作审计线**。

通过 Teleport 与 Tailscale 的结合，我们不仅实现了 GPU 集群的公网“隐身”，更让每一次操作都拥有了确定的追溯依据。

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
Updated at: 2026-01-03T04:03:44+08:00
Origin issue: https://github.com/ferstar/blog/issues/95
```
