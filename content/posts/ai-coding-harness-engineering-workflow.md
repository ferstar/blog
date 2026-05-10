---
title: "从 Vibe Coding 到 Harness Engineering：AI Coding 的工作流进化"
slug: "ai-coding-harness-engineering-workflow"
date: "2026-05-09T14:19:00+08:00"
tags: ['Idea', 'AI']
description: "AI coding 能生成代码但长期交付容易失控；用 Harness Engineering 管住任务、上下文、验证和恢复；让 AI 输出进入可执行、可验证、可复盘的工程流程。"
series: ['AI Coding']
---

这篇是一次组内分享的文字版，slides 在这里：

[从 Vibe Coding 到 Harness Engineering](/slides/harness-engineering-ai-coding/)

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:1.5rem 0 2rem;border:1px solid rgba(127,127,127,.25);overflow:hidden;">
  <iframe src="/slides/harness-engineering-ai-coding/" title="从 Vibe Coding 到 Harness Engineering" style="position:absolute;inset:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>

前阵子我一直在看一件事：AI 到底能不能承担大部分编码工作。

现在答案基本不悬了。项目上下文、质量门禁、验证流程都跟得上时，AI 生成的代码可以稳定进入工程流程。人的时间会从“手写代码”慢慢挪到“把关”：拆需求、判断架构、整理上下文、验边界、处理失败。

最近这轮实践又往前走了一点。问题从 prompt 怎么写得更漂亮，变成了整个工作流能不能扛住长任务。这个坑我也踩了不少，尤其是早上打开电脑发现 agent 跑了一夜，但很难判断哪些改动该留的时候。

### 变化在哪里

早期的 Vibe Coding 解决的是入口问题：把需求说清楚，把项目规则写进 `AGENTS.md` / `CLAUDE.md`，再用测试、lint、review 接住模型输出。

这套方法仍然好用，只是更偏单次任务。任务一长，毛病就开始冒头：

- 上下文越塞越多，模型反而抓不到重点
- 失败后继续重试，容易把问题越修越偏
- 外部资料没查清，策略靠感觉拍脑袋
- 跑了很多轮，人醒来不知道哪些变化该保留
- 用户拒绝、权限阻断、空输出这类状态没有明确停止语义

所以我现在更愿意把这层东西叫做 Harness Engineering：给 AI 外面套一段工程轨道，让任务可执行、结果可验证、失败可恢复。名字听起来有点大，其实就是少相信一点“它会自己搞定”，多给几根护栏。

{{< mermaid >}}
flowchart LR
  A[Task scope] --> B[Context route]
  B --> C[Agent loop]
  C --> D[Verification gate]
  D --> E[Recovery / memory]
  D -->|failed| F[Patch harness]
  F --> C
{{< /mermaid >}}

### 我会先管这四件事

第一件事是任务边界。

中型任务开始前，至少写清楚 `done when`、`out of scope`、改动面和验证命令。不需要长文档，很多时候 5 行就够。重点是让执行侧知道什么时候该停，少一点“顺手再优化一下”。

第二件事是上下文路由。

`AGENTS.md` 不适合写成百科全书。它更适合当索引：项目规则是什么，入口在哪里，验证命令是什么，哪些东西不能碰，下一层文档去哪读。真正的长上下文按需打开，不要整包塞回会话里。塞太满以后，模型会像我开太多浏览器标签页一样，看起来很努力，实际已经找不到重点。

第三件事是验证闭环。

我现在默认按这个顺序推进：

1. Read：读 README、AGENTS、旧文、关键实现
2. Search：用 `ace`、`rg`、`ast-grep`、`nmem`、Exa 找证据
3. Change：小范围 patch，少做顺手重构
4. Verify：先跑窄测试，再按风险扩大
5. Record：把反复踩坑写回规则、测试或 memory

这个顺序很朴素，但能压住很多失控场景。先读和先查，可以少一点模型脑补；先窄测，可以避免一口气改太大，最后谁也不知道哪一步坏了。

第四件事是失败处理。

失败后先分类型：停、重试、补 harness，还是沉淀记忆。

| 类型 | 什么时候用 | 处理方式 |
|:---|:---|:---|
| 停 | 用户拒绝、权限阻断、有副作用、重复空转 | 断开 loop，交还控制权 |
| 重试 | 网络抖动、参数可修、读取失败且无副作用 | 小步重试，保留日志 |
| 补 | 同类错误第二次出现 | 补测试、规则、脚本或日志 |
| 记 | 以后还会遇到 | 留触发条件、验证命令和证据入口 |

我以前会把很多失败都当成“再试一次”。现在会谨慎一点：能重试的问题才重试，该停的问题就得停。让 agent 带着错的前提硬冲，通常只会生成更多需要人收拾的 diff。

### 外部资料怎么进来

这轮工作流里，Exa 或类似 web search 工具的位置也更清楚了。

我一般不查宏观趋势，更常查具体工程问题：

- 超时应该设多少
- 失败要不要重试
- 默认策略怎么拆
- 主流工具给了哪些边界
- 真实 issue 里暴露了哪些失败样本

查完也不照搬。外部资料只给参照系，最后还要回到当前 repo 的约束里取舍。真正有用的结论，要落到 spec、项目规则、测试或脚本里。不然下次遇到同类问题，还是会再查一遍，等于把时间花两次。

### Autoresearch 和 Ralph Loop

Autoresearch 更适合有明确指标的长循环。先给 agent 一个目标、一个 guard、一个验证命令，每轮只允许一个可回滚变化。这样它跑偏时，损失还能控制住。

Ralph Loop 我现在理解成“持久单负责人执行”。同一个 owner 负责推进，先有 PRD 和 test spec，再让 agent 跑长任务。它更关心长任务里的上下文、判断和验证线索，不急着把更多 agent 同时拉进来。人少一点，有时反而更容易知道责任在哪里。

这两种做法的共同点是：先定义轨道，再让 agent 跑。轨道里必须有指标、边界、验证，以及哪些改动保留、哪些改动丢弃的规则。

### 先抄三步就够

如果要把这套方法挪到团队里，我建议先别急着平台化。明天就能抄三步：

1. 每个中型任务写清 `done when` 和 `out of scope`
2. 让 agent 先列文件、证据和改动面，确认后再允许修改
3. 失败一次后先补测试、规则或脚本，再继续让 agent 跑

这三步做完，AI coding 的体验会从“能产出”往“能交付”挪一点。后面再谈 autoresearch、Ralph Loop、team worker、memory，心里也会更有底。
