---
title: "给 Codex 工作流装上后视镜：我的 Harness 治理与可观测闭环"
slug: "codex-harness-observability-loop"
date: "2026-07-18T20:00:00+08:00"
tags: ['Idea', 'AI']
description: "个人 Codex skills 越积越多，却难以判断工作流是否真的变好；用权限状态机治理 skill 边界，以原生 session JSONL 为唯一事实来源，再用定时 AI 审计和 eval 建立可观测闭环。"
series: ['AI Coding']
---

一个月前，我写了篇[《把 Codex 工作流养成活系统：从会话扫描到 Skills》](/posts/codex-workflow-skills-feedback-loop/)。当时的结论很朴素：从真实会话里找重复摩擦，先沉淀成小 skill，确定是机械动作后再写脚本。

这套办法确实有用。问题是，skill 多起来以后，新的复杂度也跟着来了。

开一个任务，`agent-preflight`、`path-verify`、`gitlab-mr-context`、`codex-ship-loop` 可能一起触发；MR 合并了，Issue 到底该关闭、保持 open，还是进入 `to test`，没有统一语义；长线程中途接力时，agent 又会把已经确认过的背景重新查一遍。更麻烦的是，我知道这些问题存在，却不知道它们出现得多不多、改完是否真的变好了。

所以这次没有继续加 skill。我先回头治理 Harness 本身。

## 先审计工作流，不审计代码

我抽取了 2026-06-18 到 2026-07-18 的约 127 个顶层 Codex 线程，让多个子代理分别看项目活跃度、流程摩擦、skill 触发、`AGENTS.md` 路由和线程生命周期。

最后暴露出来的主要问题并不是“能力不够”，而是四类治理债务：

1. **skill 叠栈**：多个 skill 都在做仓库预检、GitLab 上下文读取或验证路由，agent 很难知道谁拥有流程。
2. **公共与私有边界混在一起**：可公开的通用方法里夹着公司 GitLab、内部发布流程、本机 SSH alias 和绝对路径。
3. **长线程没有 checkpoint**：接力只能回放对话，稳定事实和可能漂移的事实没有分开。
4. **交付没有终态模型**：commit、push、merge、deploy、Issue 状态和 cleanup 被口语里的“继续”“搞定”串成了一条隐式授权链。

这些问题靠再写一个“总管 skill”解决不了。总管只会成为新的叠栈入口。

## 删掉重叠职责，比增加能力更难

这一轮我删除了两个冗余 skill。

`gitlab-mr-context` 的有效内容并入了 `glab` 的 reference。读取 MR、Issue、pipeline 和 discussion，本来就是 GitLab CLI 的职责，不需要再用一个 skill 抢入口。

`path-verify` 也被删除。它真正有价值的原则——按改动范围先跑最窄的 owning-module 检查——应该成为通用验证规则；具体命令则属于项目自己的 `AGENTS.md` 或 README。单独保留它，只会让每个实现任务多触发一层路由。

保留下来的 workflow skills 都有清楚的边界：

- `agent-preflight` 只建立开工时的 repo、branch、dirty state 和线上对象事实；
- `ci-first-failure` 只处理已经变红的 CI，先找第一个可行动失败；
- `codex-ship-loop` 只把已经定界、已经验证的改动推进到经授权的交付状态；
- `release-deploy-preflight` 只处理 release / deploy 的目标、输入、exact SHA 和线上验证；
- `artifact-verify` 只证明已有产物的内容、完整性和来源，不负责构建或发布；
- `remote-health` 只诊断 SSH、网络、PATH、服务和远端运行环境。

这里最重要的变化不是目录少了两个，而是触发条件开始互斥。skill 的质量不只取决于“该用时能触发”，也取决于“不该用时不会抢活”。

## 把自然语言授权变成显式状态

日常 prompt 不应该变成表单。我仍然习惯直接说：

```text
看下这个 MR 还有什么问题。
```

但 Harness 内部需要把短 prompt 还原成一个最小任务契约：

```text
objective + evidence + scope + authority + terminal_state
```

其中最容易被忽略的是 `authority` 和 `terminal_state`。

“看下 MR”只有 read-only 权限，不等于可以改代码；“push 一下”不等于 merge；merge 也不等于 deploy、关闭 Issue 或删除分支。现在我把这些动作拆成互不传递的授权：

```text
read-only | edit | push | merge | deploy | workflow-state | publish | cleanup
```

长任务则沿着一个可跳过阶段、但不能偷换终态的状态机推进：

```text
DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE
```

{{< mermaid >}}
stateDiagram-v2
  [*] --> DISCOVER
  DISCOVER --> DECIDE
  DECIDE --> IMPLEMENT
  IMPLEMENT --> VERIFY
  VERIFY --> SHIP: separately authorized
  VERIFY --> DONE: no shipping requested
  SHIP --> DONE: final objects verified
  SHIP --> VERIFY: remote state drifted
{{< /mermaid >}}

`DONE` 也不再表示“命令执行完了”，而是请求的终态已经被回读。例如一次 deploy，workflow 成功只是中间证据；还要确认部署的是预期 SHA，并且线上健康检查通过。一次 merge 也不能顺手关闭 Issue——如果需求是“保持 open，进入测试”，那才是终态。

为了让长线程能接力，我给 `agent-preflight` 和 `codex-ship-loop` 加了统一 checkpoint。稳定证据继续复用，只刷新 branch head、dirty state、CI、mergeability、权限、workflow 输入、部署健康和远端 SHA 这些容易漂移的事实。这样 resume 不再等于从头考古。

## 我一度选错了观测入口

治理规则写完后，下一个问题自然是：怎么知道它真的有效？

我最初做了一套 Codex hooks。每个 turn 开始、结束时写一条 `events.jsonl`，再从事件流生成报告。它看起来很像标准的 observability：有事件、有 schema、有 collector，也能算完成率。

实际跑起来，很快暴露出三个问题。

第一，事件太薄。`turn_started` 和 `turn_completed` 能说明流程走完，却不能说明结果正确、skill 是否用对、Issue 是否停在正确状态。为了得到语义，最后还是要回看原始 session。

第二，它制造了第二份事实来源。Codex 原生 session JSONL 本来已经记录 lifecycle、token、tool call、模型和权限策略；hooks 再抄一份低保真事件，只会带来路径、迁移和一致性问题。

第三，hook 位于每次交互的关键路径。一次脚本重构后，旧 hook 还指向已经删除的 `codex_hook.py`，于是每次停止任务都报错。观测系统反过来污染了被观测系统。

这次踩坑很值钱：不是所有“自动采集”都值得放进 hooks。只有必须在事件发生时拦截或补充、且原生数据没有的信息，才适合进入关键路径。离线质量审计不属于这一类。

## 原生 JSONL 做唯一事实来源

最终方案简单了很多：删掉 hooks 和自建事件库，只读 `$CODEX_HOME/sessions/**/*.jsonl`。

{{< mermaid >}}
flowchart TD
  A[Native Codex session JSONL<br/>single source of truth] --> B[Deterministic scanner]
  B --> C[Content-free metrics<br/>completion / latency / tokens / tools]
  C --> D[Scheduled AI audit]
  D -->|no signal| E[Short health report]
  D -->|repeated high-signal anomaly| F[Minimal source-session review]
  F --> G[Sanitized eval candidate]
  G --> H[Baseline]
  H --> I[Harness change]
  I --> J[Regression trials]
{{< /mermaid >}}

第一层是确定性 scanner，只产出不含正文的聚合指标：完成率、耗时和 TTFT 的中位数/P95、输入输出 token、每 turn 的工具调用量、工具/模型/权限策略分布，以及无法完成的 opaque session/turn 引用。prompt、回复、命令、路径、URL、tool 参数和结果都不会进入派生报告。

第二层是定时 AI 审计。它不把所有会话重新总结一遍，只在持续未完成、延迟或成本明显回退、重复 workflow 失败等高信号出现时，最小化回看源 session，确认真实原因、权限处理和终态。没有可行动信号时，只发一条简短健康结果。

这里刻意没有“自动修改 skill”。观测可以提出五种处置：继续观察、提升为 eval、修改 skill、修改确定性工具、修复观测；但 edit、commit、push、merge、deploy 和 publish 仍要独立授权。自主进化不该等于自主扩权。

## 指标不是结论，eval 才是改动依据

完成率从 90% 变成 95%，并不能证明 Harness 更聪明。它可能只是最近的任务更简单。工具调用变少，也可能是 agent 少做了必要验证。

因此我把指标当成筛选器，不当裁判。真正推动 Harness 修改的，是从重复失败里提炼出来的脱敏、可复现 eval。

目前覆盖的用例包括：

- review-only 不得顺手编辑；
- push 后必须停止在 merge 之前；
- merge 后 Issue 保持 open / `to test`；
- deploy 必须绑定 exact SHA，并验证线上 provenance 与 health；
- 红 CI 先定位 first failure；
- 软链接必须是 install 指向 source；
- artifact 验证必须检查内容，而不只是“下载成功”。

这些 eval 同时测试正向触发和负向路由。比如普通 README typo 不应该触发 `harness-observe`，应用服务的 OpenTelemetry 也不是个人 Codex Harness 的职责。

我的改进循环现在是：

```text
real sessions -> aggregate signals -> minimal semantic review -> sanitized eval
              -> baseline -> Harness change -> regression -> observe again
```

## 这套系统现在是什么水平

它还不是一个能自动给自己改 prompt 的“自进化 Agent 平台”。我反而觉得，不做这一步是对的。

目前最有价值的是三件事：

1. **工作流有边界**：skill 不再越多越好，公共方法、项目事实和本机私有配置各有位置。
2. **交付有终态**：MR、merge、deploy、Issue 和 cleanup 不再靠含糊动词串联。
3. **改进有证据**：原生 session 是事实，指标负责发现异常，AI 负责有限语义判断，eval 负责验证修改。

下一步不是收集更多数据，而是积累跨时间可比较的 baseline，把高风险流程的 deterministic grader 做扎实，再观察哪些 skill 真的降低了返工和错误授权。

整套实现已经放在公开仓库 [ferstar/my-agent-skills](https://github.com/ferstar/my-agent-skills)。上一篇解决的是“如何把重复经验变成 skill”，这一篇解决的是后半程：**skill 多起来以后，怎样避免它们变成新的技术债，又怎样知道自己的工作流是否真的在进化。**
