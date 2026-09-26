---
title: "做 RunSeal 的初衷：别再让本地 Agent 裸奔跑命令了"
slug: "local-first-agent-execution-boundary-runseal"
date: "2026-09-26T19:00:00+08:00"
tags: ["Security", "AI Coding", "Architecture", "Sandbox", "Open Source"]
series: ["AI Coding Security"]
description: "Coding Agent 长期在宿主裸奔与笨重 Docker 之间妥协，面临越界偷读凭证与未受控外发的结构性风险；介绍很早就已成型的 RunSeal 项目，通过 OS 原生策略、workspace containment、managed proxy 与 fail-closed 架构实现轻量防护；达成毫秒级拉起、全平台受控且免侵入的本地命令安全执行边界。"
---

[RunSeal](https://github.com/runseal-labs) 这个项目其实很早就成型了。

核心逻辑和测试早早跑通，当时就想顺手写篇博客记录一下，结果后来一直忙着各种业务搬砖和日常琐事，开源准备工作一拖就拖到了现在。最近看大家因为各种隐私和越界事故，又开始扎堆讨论 Agent 的本地安全，索性把这个项目当时的背景、踩过的坑以及技术实现从头理一遍。

---

## 每天在终端里敲回车时，心里真的踏实吗？

这几年 Coding Agent 早就成了很多人的主力工具。从早期的 Aider、Open Interpreter、AutoGPT，到后来天天挂在后台的 Cursor、Claude Code、Devin、Codex，大家早就习惯了在终端里把执行权交给 AI：改完代码顺手跑个测试、调个脚本、装个依赖，省心省力。

但用久了之后，只要你稍微去看一眼它跑出来的底层日志，心里很难不犯嘀咕：

1. **它本质上就是你机器上的一个普通子进程。** 你的终端有什么权限，它就有什么权限。它读写当前项目代码是正常的，但如果它随手读一下 `~/.ssh/id_rsa`、扫一眼 `~/.aws/credentials`，或者顺着目录翻翻你隔壁还没上线的商业代码，操作系统根本不会有任何拦截。
2. **那个 `[Y/n]` 确认框纯粹是心理安慰。** 真让 Agent 排查一个复杂 Bug，一轮任务动辄调用几十次终端命令。没有人能保持每隔五秒认真审计一行 Bash 命令的专注度。不出三轮交互，确认框就会沦为毫无意识的连续狂按回车（“审批疲劳”）。真要被恶意注入了，最后也是自己按出来的回车，出了事还得自己背锅。
3. **想做点防范，市面上的方案难用得要死。**
   - 扔进 Docker 跑？在 Mac 上试过的人都知道有多痛苦：通过虚拟机挂载本地目录，文件 I/O 慢得跟乌龟一样，`npm install` 能卡半天；本地配置好的 Python 虚拟环境、编译器缓存和系统依赖全废了；更讽刺的是，为了让它能下包查文档，你还得给容器开外网，真有恶意 prompt 注入，该往外发的凭证依然能顺着公网发走。
   - 依赖安全插件的正则黑名单？拦截 `rm -rf /` 或 `cat ~/.ssh` 看着挺唬人，但稍微用过终端的人都懂，随手用个字符串拼接、Base64 解码，或者写三行 Python 脚本间接执行，静态正则当场失灵。
   - 社区里一些开源小脚本？绝大多数只写了个 Linux 的 `bwrap` 或 `landlock` demo 就算完事。但现实里我们天天在 Mac 上敲代码，很多人办公用的是 Windows，一换平台直接两手一摊变裸奔。而且网络策略粗暴得很——要么彻底拔网线（连个依赖都下不来），要么全开（形同虚设）。

这种两极分化的现状特别别扭：**要么为了敏捷彻底裸奔，要么为了安全把开发体验彻底搞废。**

---

## RunSeal 的定位：不做大而全，只啃最硬的骨头

动手写 RunSeal 时，我就在 `AGENTS.md` 里把边界卡得很死，大意是：

> RunSeal 是一个 OS-native、受策略约束的本地命令安全执行环境——不是 AI Governance 平台，不是组织级审批流，不是策略仪表盘，也不是通用自动化框架。

我不打算搞什么花里胡哨的审批流或者 SaaS 控制台，核心目标就一个：**在不依赖虚拟机、不牺牲本地开发速度的前提下，在操作系统内核层把 Agent 的爪子按死在当前工作区里。**

{{< mermaid >}}
flowchart TD
    A[Agent 准备跑命令] --> B[RunSeal CLI / RPC]
    B --> C{检查宿主策略能力}
    C -->|能力不满足| D[Fail-Closed 立即退出报错<br/>绝不静默放行]
    C -->|策略校验通过| E[构建 OS 原生执行沙箱]
    
    subgraph OS[OS 原生内核边界]
        E --> F[文件系统: Workspace-Contained<br/>仅限当前目录 + 临时 Root]
        E --> G[网络受控: Managed Proxy<br/>阻断外部直连与未授权 loopback]
    end
    
    F & G --> H[执行命令并捕获退出状态]
    H --> I[写入本地 JSONL 审计日志]
    I --> J[结果返回 Agent]
{{< /mermaid >}}

整个设计就抓这几个关键点：

### 1. 毫秒级原生拉起，拒绝虚拟化

RunSeal 不启动 VM，也不用后台常驻 daemon。它直接调用操作系统底层的隔离原语：
* **Windows 作为一等公民（Reference Backend）**：绝大多数开源安全脚本最怕碰 Windows，而 RunSeal 从第一天起就把 Windows 当作参考实现，通过受限令牌（Restricted Token）、Job Objects 和专有 ACL 落地，策略到执行计划的映射统一走 `PlatformSandboxPlan` 契约；
* **macOS / Linux 功能对齐**：macOS 用 Seatbelt（`sandbox-exec`），Linux 用 Bubblewrap 加 Landlock，三级沙箱与三种网络模式全部原生执行，managed proxy 边界也已经在这两个平台落地（RFC-0019 / RFC-0020）。

因为是 OS 原生调用，没有虚拟机那层中转损耗，启动是毫秒级的，本地编译器缓存和工具链该怎么用还怎么用。

### 2. 工作区锁死（Workspace Containment）

在文件系统层面，RunSeal 规范了四个沙箱级别：`read-only`、`workspace-write`、`workspace-contained`，外加一个显式放弃沙箱保证的 `danger-full-access`。

最核心的就是 `workspace-contained`：
* 进程**只能看见当前的工作区目录（Workspace）、自己运行时的私有临时目录、显式声明的只读路径，以及系统必需的最小只读基线**；
* 宿主机上的其他任何位置（特别是 `~/.ssh`、`~/.aws`、`~/.config`，或者磁盘里其他项目的源码），在沙箱视图里直接不可见或直接报错；
* 哪怕 Agent 被 Prompt 注入带着去跑 `cat ~/.ssh/id_rsa`，或者用 `cd ../../` 试图往外溜达，内核都会直接拒绝这次访问（实测返回 `Operation not permitted`），从根子上断了翻看邻近项目和隐私凭证的念头。

### 3. `network.proxy`：受控出网，而不是粗暴拔网线

在真实开发里，Agent 完全不联网是不现实的，装依赖、调接口、查文档都需要网。但如果大开公网，任何外发都管不住。

RunSeal 专门设计了 `network.proxy` 模式：
* 严禁直连外部公网 IP/域名；
* 阻断未授权的本地 loopback 和宿主机 IPC 通信；
* **所有出网流量必须强制重定向到当前执行指定的 Managed Proxy 代理端点**。

这样一来，代理层可以从容做白名单路由、敏感凭证脱敏和流量审计。Agent 想在后台悄悄给第三方服务器传东西，连网络链路都建不起来。

### 4. 宁可报错中断，绝不偷偷降级（Fail-Closed）

做安全防御，最忌讳的就是“为了让流程跑通而假装安全”。

如果策略要求了 `workspace-contained` 和 `network.proxy`，但当前机器因为权限不够或系统版本太老无法完整提供这些隔离能力，**RunSeal 会直接 Fail-Closed 报错退出，绝不静默降级到裸奔环境去跑**。

同时我们写了完整的黑盒对抗测试套件（RFC-0016），把软链接穿透、父目录逃逸、环境变量污染、孤儿进程清理这些常见的逃逸手段全测了一遍，确保声明了 `supported` 的能力是经过机器验证的硬结果。

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
