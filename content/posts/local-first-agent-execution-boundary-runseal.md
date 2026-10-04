---
title: "做 RunSeal 的初衷：给本地 Agent 设一道命令执行边界"
slug: "local-first-agent-execution-boundary-runseal"
date: "2026-09-26T19:00:00+08:00"
tags: ["Security", "AI Coding", "Architecture", "Sandbox", "Open Source"]
series: ["AI Coding Security"]
description: "Coding Agent 长期在宿主裸奔与笨重 Docker 之间妥协，面临越界偷读凭证与未受控外发的结构性风险；介绍很早就已成型的 RunSeal 项目，通过 OS 原生策略、workspace containment、managed proxy 与 fail-closed 架构实现轻量防护；达成毫秒级拉起、全平台受控且免侵入的本地命令安全执行边界。"
---

[RunSeal](https://github.com/runseal-labs) 这个项目其实很早就成型了。

核心逻辑和测试早早跑通，当时想顺手写篇记录，结果后来忙着各种业务搬砖，开源整理一拖就拖到了现在。最近大家因为隐私和越界行为，又开始讨论 Agent 的本地安全，索性把这个项目当时的背景、踩过的坑以及技术实现理一遍。

---

## 本地命令执行的信任缺口

这几年 Coding Agent 成了很多人的主力工具。从早期的 Aider、Open Interpreter，到后来天天挂在后台的 Cursor、Claude Code、Devin、Codex，大家习惯了在终端里把执行权交给 AI：改完代码顺手跑个测试、调个脚本、装个依赖。

但只要去看一眼它跑出来的底层日志，问题很明显：

1. **它就是你机器上的一个普通子进程。** 你的终端有什么权限，它就有什么权限。读写当前项目代码是正常的，但如果顺手读一下 `~/.ssh/id_rsa`、扫一眼 `~/.aws/credentials`，或者翻翻旁边其他项目的代码，操作系统根本不会拦截。
2. **`[Y/n]` 确认框容易变成心理安慰。** 真让 Agent 排查一个复杂 Bug，一轮任务动辄调用几十次终端命令。没有人能每隔几秒认真看一行 Bash。连续按回车变成机械动作后，一旦被注入恶意指令，最后也是自己按下去的。
3. **已有的防护方式不够趁手。**
   - 扔进 Docker 跑：在 Mac 上通过虚拟机挂载本地目录，文件 I/O 很慢，`npm install` 能卡半天；本地配好的虚拟环境、编译器缓存和系统依赖用不上；为了下包查文档往往还得开外网，真有恶意 prompt 注入，该往外发的依然能发出去。
   - 正则黑名单：拦截 `rm -rf /` 或 `cat ~/.ssh` 看着直接，但稍微用点字符串拼接、Base64 或简单脚本间接执行，静态正则就绕过去了。
   - 社区小脚本：多是 Linux 上的 demo，依赖 `bwrap` 或 `landlock`。在 Mac 或 Windows 上用不上，网络策略通常也是二选一：要么拔网线，要么全开。

两边的体验很分裂：要么图省事直接跑，要么为了安全把开发体验搞得很别扭。

---

## RunSeal 的设计范围

动手写 RunSeal 时，我在 `AGENTS.md` 里明确了边界：

> RunSeal 是一个 OS-native、受策略约束的本地命令安全执行环境——专注在本地命令隔离，不承接审批流、策略仪表盘或通用自动化框架。

核心目标很明确：在不依赖虚拟机、不牺牲本地开发速度的前提下，在操作系统内核层把 Agent 的执行范围限定在当前工作区内。

{{< mermaid >}}
flowchart TD
    A[Agent 准备跑命令] --> B[RunSeal CLI / RPC]
    B --> C{检查宿主策略能力}
    C -->|能力不满足| D[Fail-Closed 立即退出报错<br/>不静默放行]
    C -->|策略校验通过| E[构建 OS 原生执行沙箱]
    
    subgraph OS[OS 原生内核边界]
        E --> F[文件系统: Workspace-Contained<br/>仅限当前目录 + 临时 Root]
        E --> G[网络受控: Managed Proxy<br/>阻断外部直连与未授权 loopback]
    end
    
    F & G --> H[执行命令并捕获退出状态]
    H --> I[写入本地 JSONL 审计日志]
    I --> J[结果返回 Agent]
{{< /mermaid >}}

设计主要围绕这几个方面：

### 1. 毫秒级原生拉起，不依赖虚拟化

RunSeal 不启动 VM，也不用后台常驻 daemon。它直接调用操作系统底层的隔离原语：
* **Windows 作为参考实现**：通过受限令牌（Restricted Token）、Job Objects 和专有 ACL 落地，策略到执行计划的映射统一走 `PlatformSandboxPlan` 契约；
* **macOS / Linux 功能对齐**：macOS 用 Seatbelt（`sandbox-exec`），Linux 用 Bubblewrap 加 Landlock，三级沙箱与三种网络模式全部原生执行，managed proxy 边界也已在两个平台落地（RFC-0019 / RFC-0020）。

因为是系统原生调用，没有虚拟机中转损耗，启动是毫秒级的，本地编译器缓存和工具链照常使用。

### 2. 工作区隔离（Workspace Containment）

在文件系统层面，RunSeal 规范了四个沙箱级别：`read-only`、`workspace-write`、`workspace-contained`，外加显式放弃保证的 `danger-full-access`。

核心是 `workspace-contained`：
* 进程只能看见当前的工作区目录、运行时的私有临时目录、显式声明的只读路径，以及系统必需的最小只读基线；
* 宿主机上的其他位置（如 `~/.ssh`、`~/.aws`、`~/.config`，或其他目录的源码），在沙箱里不可见或直接报错；
* 哪怕 Agent 遇到 Prompt 注入去执行 `cat ~/.ssh/id_rsa`，或者试图通过路径穿越往外翻，内核都会直接拒绝（实测返回 `Operation not permitted`）。

### 3. 受控出网（`network.proxy`）

开发时完全断网并不现实，装依赖和查文档都需要网络。但直接放开公网，外发行为就不可控。

RunSeal 增加了 `network.proxy` 模式：
* 限制直连外部公网 IP 或域名；
* 阻断未授权的本地 loopback 和宿主机 IPC 通信；
* 所有出网流量强制重定向到指定的 Managed Proxy 端点。

这样代理层可以统一处理白名单路由、凭证过滤和流量审计。

### 4. 无法满足策略时直接报错（Fail-Closed）

做安全隔离，最怕为了让命令跑通而默默放开限制。

如果策略指定了 `workspace-contained` 和 `network.proxy`，但当前系统权限不够或版本不支持，**RunSeal 会直接 Fail-Closed 报错退出，不会静默降级为未受限环境执行**。

项目里配合了黑盒对抗测试套件（RFC-0016），覆盖软链接穿透、父目录逃逸、环境变量污染、孤儿进程清理等常见路径，确保标明 `supported` 的能力经过了实际验证。

---

## 怎么用起来？

RunSeal 的 CLI 刻意做得很简单：参数就那么几个，很容易嵌进各种 Agent 自动化脚本或框架里。

### 1. 查一下当前机器支持什么能力

```bash
runseal capabilities
```

输出一段 JSON，告诉你当前机器能保证什么（节选，完整输出还包含 `features`、`capability_probes` 等字段）：

```json
{
  "platform": "macos",
  "sandbox_levels": {
    "read-only": "supported",
    "workspace-write": "supported",
    "workspace-contained": "supported",
    "danger-full-access": "supported"
  },
  "network_modes": {
    "unmanaged": "supported",
    "disabled": "supported",
    "proxy": "supported"
  }
}
```

协议与策略版本号则由 `runseal version --json` 单独给出。

### 2. 跑一条受限命令

把要执行的命令限定在当前工作区，同时彻底断网：

```bash
runseal exec \
  --policy workspace-contained \
  --network disabled \
  --cwd /Users/ferstar/myprojects/demo \
  -- python3 test_pipeline.py
```

如果命令里试图越界读取 `~/.ssh`，内核会直接拒绝这次读取。默认模式下终端不会回显任何报错——但命令已经被拦死了，加 `--json` 就能看到完整结果（节选）：

```bash
runseal exec --json \
  --policy workspace-contained \
  --network disabled \
  --cwd /Users/ferstar/myprojects/demo \
  -- cat ~/.ssh/id_rsa
```

```json
{
  "exit_code": 1,
  "stderr": "cat: /Users/ferstar/.ssh/id_rsa: Operation not permitted",
  "sandbox": {"enforced": true, "level": "workspace-contained"}
}
```

注意 `runseal exec` 自身的退出码目前固定为 0，子进程的真实退出状态以 JSON 结果和审计日志为准；如果要把结果接进自动化流程，`--json` 输出结构化结果，`--events` 则按行流式吐出执行事件。

### 3. 本地结构化审计

每次执行到底用了什么策略、对应的 Canonical Policy Hash 是多少、网络做没做阻断，都会实时落盘成 JSONL 审计记录（节选，每条事件还带有 `execution_id`、`session_id`、`policy_epoch` 等字段）：

```json
{"type":"policy.resolved","policy_id":"workspace-contained","policy_hash":"sha256:7cb64a73...","sandbox_level":"workspace-contained","network":{"mode":"disabled","routes":[]},"time":"2026-09-26T11:21:26.967279Z"}
{"type":"execution.finished","exit_code":1,"status":"finished","time":"2026-09-26T11:21:26.971042Z"}
```

---

## 一点想法

前阵子 ZCode 那个静默上传代码仓的事情闹得沸沸扬扬，其实那只是把“本地 Agent 权限裸奔”这个隐患，以最戏剧化的一种方式曝光在大众面前而已。

AI 编程工具迭代得太快了。模型越来越聪明，自主执行的链路也越来越长。但我们不能一边享受着几倍的代码产出速度，一边把主机的“万能钥匙”全押在服务商的道德自觉或者一份不可证伪的用户协议上。

平时在开发机上干活，没必要天天跟防贼一样提心吊胆，但也别等哪天真的被端了底裤才想起来穿衣服。

把不可逾越的物理边界稳稳卡在操作系统内核层，该放行的放行，该掐死的掐死——这才是让 Agent 能够放手跑下去的长久之计。

*(RunSeal 的 RFC 规范和代码都在 GitHub 上公开维护，感兴趣的可以来看看：[github.com/runseal-labs](https://github.com/runseal-labs))*
