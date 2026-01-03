---
title: "基于 Teleport + Tailscale 的 GPU 集群访问控制与审计实战"
date: "2026-01-03T03:58:20+08:00"
tags: ['Linux', 'Idea']
comments: true
---

## GPU 集群堡垒机方案：Teleport + Tailscale 一把梭

手头有几台 DGX H800，内网环境，但偶尔要让供应商远程上来调试。需求很简单：

1. 供应商能连上机器干活
2. 全程录屏审计，但别让他知道在录（"静默"）
3. 我们自己人要有特权通道，绕过堡垒机直连

放狗搜了一圈，最后选了 **Teleport** 做堡垒机 + **Tailscale** 打通内网隧道。让 Gemini 帮忙查文档、生成配置，个把小时就搞定了。踩的坑不少，记录一下。

---

### 架构一句话

```
公网用户 → Nginx(443) → Teleport Proxy(3080) → GPU 节点
                                    ↑
                        Tailscale 隧道打通内网
```

---

### 踩坑 1：端口太多

Teleport 默认要开 3022-3080 好几个端口，防火墙规则写到吐。后来发现有个 **Multiplexing** 模式，单端口搞定：

```yaml
# teleport.yaml
auth_service:
  proxy_listener_mode: multiplex
```

原理是 ALPN 协议自动识别流量类型，HTTPS/SSH/Tunnel 全走 3080。防火墙只管一个口，舒服。

---

### 踩坑 2：内网节点装 Agent 装不上

GPU 节点在隔离内网，装 Teleport Agent 需要走代理。yum 死活装不上，证书报错。最后发现要在 repo 文件里显式配代理：

```ini
# /etc/yum.repos.d/teleport.repo
[teleport]
proxy=http://[堡垒机VIP]:8888
```

---

### 踩坑 3：WebSocket 断连

Nginx 反代 Teleport Web Terminal，页面能打开但终端秒断。查了半天，三个配置缺一不可：

```nginx
proxy_pass https://127.0.0.1:3080;  # 必须 https
proxy_ssl_verify off;                # 自签名证书
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

---

### 踩坑 4：Docker 端口绕过 iptables

这个最坑。Docker 映射的端口会绕过 `INPUT` 链，直接走 `DOCKER-USER`。之前写的规则形同虚设，3080 对公网敞开着。

修复版：

```bash
iptables -F DOCKER-USER
# 只允许本地和 Tailscale 网段
iptables -A DOCKER-USER -s 127.0.0.1 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -s 100.64.0.0/10 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 3080 -j DROP
```

---

### 踩坑 5：Nginx 指向 VPN IP 导致循环依赖

早期 Nginx 配的是 Tailscale VPN IP，结果 VPN 一抖，管理页面直接挂。

改成 `127.0.0.1` 本地回环，VPN 挂了照样能从公网进管理台。

---

### 权限设计

| 角色 | 登录方式 | 审计 |
|:---|:---|:---|
| 管理员 | SSH 22 端口 + Ed25519 密钥 | 无 |
| 供应商 | Web Terminal | 全程录屏，自己看不到录像 |

RBAC 配置要点：给供应商的 `restricted-dev` 角色剥离 `audit` 权限，实现"静默审计"。

---

### 核心配置

**docker-compose.yml**

```yaml
services:
  teleport:
    ports:
      - '3080:3080'
      - '127.0.0.1:3025:3025'  # 管理 API 只本地
```

**teleport.yaml**

```yaml
proxy_service:
  public_addr: [teleport.example.com:443, 100.64.0.x:3080]
```

---

折腾完这套，供应商老老实实走 Web 干活，我们照常 SSH 直连。录像审计随时调取，公网完全隐身。

挺好。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2026-01-03T03:58:20+08:00
Updated at: 2026-01-03T05:54:12+08:00
Origin issue: https://github.com/ferstar/blog/issues/95
```
