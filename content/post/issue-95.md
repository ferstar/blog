---
title: "基于 Teleport + Tailscale 的 GPU 集群访问控制与审计实战"
date: "2026-01-03T03:58:20+08:00"
tags: ['Linux', 'Idea']
comments: true
---

## 0. 背景：高价值算力资源的访问挑战
在管理 **DGX H800** 等核心算力集群时，我们需要平衡三个关键维度：
- **物理连通性**：计算节点位于隔离的内网环境。
- **管理合规性**：外部供应商（Vendor）介入时，必须实现“静默审计”与全量录屏。
- **管理员效率**：核心运维人员需具备绕过堡垒机、直达底层的“特权通道”。

通过 **Teleport** 与 **Tailscale** 的结合，我们构建了一套零信任架构下的堡垒机方案，实现了对操作行为的闭环管理。

---

## 1. 架构逻辑：连通性与审计的分层
- **网络层（Tailscale）**：解决跨地域、跨内网的底层连接，隐藏物理拓扑。
- **协议审计层（Teleport）**：负责身份认证、指令过滤及会话录制。
- **统一接入层（Nginx）**：收口 443 端口，通过标准域名提供 HTTPS 管理门户。

---

## 2. 核心技术点：单端口多路复用 (Multiplexing)
在传统部署中，Teleport 需要开放 3022-3080 多个端口。为简化网络拓扑和安全策略，我们启用了 **Multiplexing** 模式。
- **原理**：Teleport Proxy 在单一端口（3080）上根据 ALPN 协议自动识别流量类型（HTTPS/SSH/Tunnel）。
- **优势**：防火墙只需监控一个入口，极大缩小了受攻击面。

---

## 3. 部署细节：突破内网孤岛

### 3.1 Agent 隧道接入
针对位于内网的 GPU 节点，我们通过 `HTTP_PROXY` 引导 Teleport Agent 建立反向隧道。针对包管理器在代理环境下的证书问题，需显式配置 Repo 代理：
```bash
# /etc/yum.repos.d/teleport.repo
[teleport]
proxy=http://[VIP_BASTION]:8888 
```

### 3.2 Nginx 代理调优
为确保 Web Terminal（WebSocket）稳定，Nginx 必须配置：
1. **协议一致性**：上游必须使用 `https` 协议。
2. **SSL 验证忽略**：`proxy_ssl_verify off`（处理容器内自签名证书）。
3. **长连接维持**：配置标准的 `Upgrade` 和 `Connection "upgrade"` 头部。

---

## 4. 权限加固：管理员与供应商的角色解耦

### 4.1 管理员：独立密钥与原生 Shell
管理员使用 Ed25519 密钥走 22 端口直接访问。
- **策略**：禁用所有 root 密码登录。
- **体验**：配置本地 SSH Config 别名，实现免感登录并保留原生 Bash 操作体验。

### 4.2 外部供应商：受限访问与静默审计
分配 `dev` 账号，仅限 Web 连接。
- **RBAC 定制**：创建 `restricted-dev` 角色，剥离所有审计日志与录屏的查看权限。
- **效果**：操作人员无感知录屏，管理员作为 `auditor` 拥有全局追溯权。

---

## 5. 安全防护：IPTables 手术刀式过滤
由于 Docker 映射端口会绕过常规防火墙，我们必须在 **`DOCKER-USER`** 链中进行精准防护。

### 5.1 规则逻辑
我们舍弃了模糊的网卡接口匹配，改为基于 **源 IP/网段** 的精准过滤：
1. **允许本地**：`127.0.0.1` 访问 3080 (支持 Nginx 转发)。
2. **允许 VPN**：`100.64.0.0/10` 访问 3080 (支持 GPU 节点接入)。
3. **默认拒绝**：公网或其他来源的一切 3080 访问请求。

这种“显式允许，默认拒绝”的策略确保了算力资源对公网的完全隐身。

---

## 6. 容灾：解除循环依赖
早期配置中 Nginx 指向了 VPN IP，导致 VPN 故障时管理门户瘫痪。最终我们将其优化为 **127.0.0.1 本地回环转发**，实现了即便 VPN 网络波动，公网域名管理入口依然固若金汤。

---

## 附录：核心配置文件（脱敏）

### A. Docker Compose (docker-compose.yml)
```yaml
services:
  teleport:
    ports:
      - '3080:3080'           # 全能业务端口
      - '127.0.0.1:3025:3025' # 管理 API，仅限本地
    volumes:
      - ./teleport.yaml:/etc/teleport/teleport.yaml
```

### B. IPTables 修正版指令
```bash
# 清空并重新构建 DOCKER-USER 链
iptables -F DOCKER-USER
# 3080 端口精准放行 127.0.0.1 和 Tailscale 网段
iptables -A DOCKER-USER -s 127.0.0.1 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -s 100.64.0.0/10 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 3080 -j DROP
```

### C. Teleport 核心配置 (teleport.yaml)
```yaml
auth_service:
  proxy_listener_mode: multiplex # 开启多路复用
proxy_service:
  # 同时声明域名与内部网关，确保握手兼容性
  public_addr: [teleport.example.com:443, 100.64.0.x:3080]
```



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2026-01-03T03:58:20+08:00
Updated at: 2026-01-03T04:13:24+08:00
Origin issue: https://github.com/ferstar/blog/issues/95
```
