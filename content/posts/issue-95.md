---
title: "基于 Teleport + Tailscale 的 GPU 集群访问控制与审计实战"
slug: "teleport-tailscale-gpu-access"
date: "2026-01-03T03:58:20+08:00"
tags: ['Linux', 'Idea']
comments: true
description: "供应商需远程接入但审计必须静默；用 Teleport + Tailscale 的复用与绕过通道方案；实现安全且低摩擦的 GPU 集群访问。"
---

内网里有几台 DGX H800，平时不对外，但偶尔又得让供应商远程上来排障。需求听起来简单，真落到网络和审计上就开始别扭：

1. 供应商得能连上机器，把问题处理掉
2. 会话要完整录屏留痕，但尽量别把审计入口暴露给对方
3. 我们自己人还得保留一条直连通道，不能每次都绕堡垒机

最后拼出来的方案是：Teleport 做堡垒机和审计，Tailscale 负责内网互通，以及给内部运维留一条旁路。下面记录几个当时卡住的点，免得以后又把坑踩一遍。

---

### 架构大概长这样

{{< mermaid >}}
flowchart LR
  subgraph External[公网用户]
    Vendor[供应商<br/>Web/SSH]
    AppUser[应用访问者<br/>Web]
  end
  subgraph Ops[内部运维]
    Admin[管理员<br/>SSH 直连]
  end
  subgraph Edge[公网接入层]
    Nginx[Nginx 443]
    Teleport[Teleport Proxy 3080]
    FW[DOCKER-USER 防火墙]
    Logs[(会话录屏/日志)]
    ExitNode[Tailscale Exit Node]
  end
  subgraph Intranet[内网 GPU 集群]
    GPU[GPU 节点]
    AppUI[App UI 32000]
  end

  Vendor -- HTTPS/SSH --> Nginx --> FW --> Teleport --> GPU
  AppUser -- HTTPS --> Nginx --> FW --> Teleport --> AppUI
  Admin -- SSH 22 --> TSUser[内部 Tailscale 节点]
  TSUser -- Tailscale 隧道 --> ExitNode --> GPU
  Teleport --> Logs
{{< /mermaid >}}

---

### 端口先收敛，不然防火墙会很烦

Teleport 默认会用到 3022-3080 这一串端口。放在单机测试还好，一旦前面有 Nginx、Docker、云防火墙，规则很快就乱成一锅粥。

还好它支持 Multiplexing，开了之后可以把 HTTPS、SSH、Tunnel 都收进 3080：

```yaml
# teleport.yaml
auth_service:
  proxy_listener_mode: multiplex
```

背后靠 ALPN 区分流量类型。对我来说最大的好处很朴素：公网侧只盯一个端口，排查时少掉一半精神内耗。

---

### 隔离内网里装 Agent，代理要写到 repo 里

GPU 节点不能直接出网，安装 Teleport Agent 得走代理。我一开始只配了系统代理，结果 `yum`/`dnf` 还是各种证书错误，绕了一圈才发现 repo 文件里也要显式写代理：

```ini
# /etc/yum.repos.d/teleport.repo
[teleport]
proxy=http://[堡垒机VIP]:8888
```

这类问题很不像“高级故障”，但最耗时间。报错看着像证书，根因其实是包管理器根本没按你以为的方式走代理。

---

### Web Terminal 秒断，通常是 Nginx 少了 WebSocket 配置

Nginx 反代 Teleport Web Terminal 时，页面能打开，终端一连就断。最后固定下来这几项，少一项都容易抽风：

```nginx
proxy_pass https://127.0.0.1:3080;  # 必须 https
proxy_ssl_verify off;                # 自签名证书
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

尤其是 `proxy_pass` 这里要用 `https`。我当时看到页面能开，还以为协议没问题，结果终端通道根本不是一回事。

---

### Docker 映射端口会绕开你熟悉的 INPUT 链

这个是最吓人的一个。我原本在 `INPUT` 链里写了限制，自以为 3080 已经只对内开放。实际 Docker 映射的端口会先进 `DOCKER-USER`，之前那套规则基本等于没写，3080 还在公网裸着。

注意：下面的 `-F` 会清空 `DOCKER-USER` 规则，生产环境别直接照抄。至少先备份，或者改用 `-I` 插入到合适位置。

我这边修成这样：

```bash
iptables -F DOCKER-USER
# 只允许本地和 Tailscale 网段
iptables -A DOCKER-USER -s 127.0.0.1 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -s 100.64.0.0/10 -p tcp --dport 3080 -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 3080 -j DROP
```

---

### Nginx 别指向 VPN IP，容易把自己绕进去

早期我把 Nginx upstream 写成了 Tailscale VPN IP。看着统一，实际是给自己挖坑：VPN 一抖，管理页也跟着不可用。

后来改成 `127.0.0.1` 本地回环。这样 Tailscale 挂了，公网管理入口还在，不至于连修 VPN 的入口都没了。

---

### 权限怎么拆

| 角色 | 登录方式 | 审计 |
|:---|:---|:---|
| 管理员 | SSH 22 端口 + Ed25519 密钥 | 无 |
| 供应商 | Web Terminal | 全程录屏，自己看不到录像 |

RBAC 的关键是给供应商的 `restricted-dev` 角色去掉 `audit` 权限，让他看不到录像和日志入口。

这里补一句：去掉 `audit` 只影响录像/日志的可见性，不保证隐藏所有录制提示。Teleport 不同版本、不同配置可能表现不一样，上线前最好自己测一遍，别把“静默”当成天然成立。

另外两个限制也建议顺手做掉：

1. 供应商只通过 Teleport Web/SSH 进来，不给 Tailscale
2. 供应商角色限制登录账号和可见节点，用标签隔离

```yaml
# 示例：节点打标（供应商名称已脱敏）
labels:
  vendor: vendor-x
  env: prod
```

```yaml
# 示例：角色限制（供应商账号与可见节点）
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

### 核心配置摘几段

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

### App Access 后面也补上了

**应用暴露示例**

```yaml
app_service:
  enabled: "yes"
  apps:
  - name: app-ui
    uri: http://10.120.0.0:32000/
    public_addr: app-ui.example.com
```

**代理环境变量导致 503**

节点上如果有 `HTTP_PROXY`，Teleport 访问内网应用时可能也被带去走代理，最后返回 503。Systemd 里加 `NO_PROXY` 更稳：

```ini
# /etc/systemd/system/teleport.service
Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,100.64.0.0/10"
```

**Nginx 透传 Host 头**

多子域访问时，Host 头别漏：

```nginx
proxy_set_header Host $host;
```

---

这套跑下来，供应商从 Web 里干活，内部运维用 Tailscale 直连；审计录像能留，GPU 集群也不用直接暴露到公网。

不算优雅，但够稳。对这种临时又敏感的远程支持场景，稳比好看重要。

---

```js
NOTE: I am not responsible for any expired content.
Created at: 2026-01-03T03:58:20+08:00
Updated at: 2026-01-03T05:55:29+08:00
Origin issue: https://github.com/ferstar/blog/issues/95
```
