---
title: "把语义检索放进 AI Coding Harness：ace-wrapper 开源小记"
slug: "ace-wrapper-semantic-search-ai-coding-harness"
date: "2026-05-09T14:38:00+08:00"
tags: ['Idea', 'AI']
description: "AI coding 长任务常卡在不知道该读哪里；用 ace-wrapper 把语义检索放进 Read -> Search -> Change -> Verify；让 agent 先找候选文件、再验证证据，减少盲改和上下文浪费。"
series: ['AI Coding']
---

[上一篇](/posts/ai-coding-harness-engineering-workflow/)写 Harness Engineering 时，我把 AI coding 的默认顺序压成了几步：

1. Read
2. Search
3. Change
4. Verify
5. Record

这里面最容易被低估的是 `Search`。

很多 agent 失败，第一步就错了：读错地方。用户说的是一个行为、一个 bug、一个跨层流程，代码里却不一定有同名函数。直接 `rg login`、`rg upload`、`rg session` 很快，但它只适合已知关键词。关键词都不知道时，快只会更快地跑偏。

所以我把最近常用的一小层工具开源了：

[ferstar/ace-wrapper](https://github.com/ferstar/ace-wrapper)

它做的事很窄：把 Augment Context Engine 的 filesystem context search 包成一个 `ace` 命令，让 coding agent 可以在 shell 里先做语义检索。

### 为什么需要这一层

我关心的点很具体：把搜索动作放进 harness。

以前我经常看到这种路径：

{{< mermaid >}}
flowchart LR
  A[User describes behavior] --> B[Agent guesses keywords]
  B --> C[Reads nearby files]
  C --> D[Edits plausible code]
  D --> E[Verification fails]
  E --> B
{{< /mermaid >}}

这个循环的问题是，失败后 agent 往往会继续围着同一批错误文件打转。它有修改能力，缺的是更好的候选文件入口。说白了，一开始摸错门，后面再努力也容易越走越偏。

`ace-wrapper` 想补的是这里：

{{< mermaid >}}
flowchart LR
  A[User describes behavior] --> B[ace semantic retrieval]
  B --> C[Candidate files]
  C --> D[Read returned files]
  D --> E[rg / tests confirm evidence]
  E --> F[Small patch]
  F --> G[Verify]
{{< /mermaid >}}

这里的关键是顺序：`ace` 只负责找候选文件。真正的证据仍然来自读文件、精确搜索和测试。它的定位很小，就是帮 agent 少走一点冤枉路。

### 用法很短

安装：

```bash
uv tool install ace-wrapper
```

本地开发版：

```bash
uv tool install /path/to/ace-wrapper
```

查一个不知道关键词的工作流：

```bash
timeout 60s ace "user uploads an unsupported file and should see skipped-file feedback" -w /repo
rg -n "unsupported|skipped|upload|file" /repo
```

第一条命令回答“可能在哪些文件”。第二条命令确认“代码里到底有没有这些标识、事件、文案或测试”。

我一般会把这段规则放进项目的 `AGENTS.md`：

```text
Use `timeout 60s ace "<query>" -w <repo-root>` for semantic codebase discovery.
Treat `ace` results as candidate files.
After it returns results, read the relevant files and use exact search before using them as evidence.
```

这几行比“多读上下文”更有用，因为它给了 agent 一个具体动作，也给了防止误判的边界。

### 它和 rg 怎么配合

`ace` 和 `rg` 更适合前后配合使用。

| 场景 | 先用什么 | 为什么 |
|:---|:---|:---|
| 不知道实现在哪里，只知道用户行为 | `ace` | 行为描述能跨文件、跨命名找到候选入口 |
| 知道函数名、事件名、错误文案 | `rg` | 精确、完整、可枚举 |
| 要做结构性重构 | `ast-grep` | 需要 AST 级别匹配，不能靠文本近似 |
| 要确认一个功能是否存在 | `ace` + 读文件 + `rg` | 语义命中不能证明功能存在 |

我特意在 README 里写了边界：ACE 只生成候选文件，证据还要从代码和测试里确认。这个边界很重要。

语义检索会返回“相近”的东西。你问一个不存在的功能，它也可能找出看起来相关的文件。如果 agent 把“有结果”理解成“功能存在”，后面就会开始编故事。只有读到实现、测试、路由、配置或调用点，结论才算站得住。

### 它在 Harness Engineering 里的位置

`ace-wrapper` 很小，也不该变成平台。它更像 harness 里的一个小齿轮：把“开放式找代码”这件事变成可重复、可约束的命令。

我现在更喜欢这样的项目规则：

```text
Read -> Search -> Change -> Verify
```

其中 `Search` 要按问题类型选工具：

- 开放式、行为式、跨层链路：先 `ace`
- 精确标识、报错、路由、配置：用 `rg`
- 结构性替换：用 `ast-grep`
- 外部策略和行业做法：用 web research
- 旧决策、历史踩坑：用 memory

这套分工能减少 agent 的随机性。它先用语义检索缩小读文件范围，再用确定性工具确认事实，最后才动代码。顺序看起来啰嗦一点，但比一上来改错文件省事太多。

### 对 agent 来说，最重要的是提示方式

好的 `ace` query 要把行为讲完整，不能只堆关键词：

```bash
timeout 60s ace "frontend sends requestId to backend and starts a processing job" -w /repo
timeout 60s ace "用户拖入不支持的文件后应该显示跳过文件提示" -w /repo
timeout 60s ace "how provider config is persisted and restored after app restart" -w /repo
```

我会尽量包含四类信息：

- 用户动作：点击、拖拽、上传、停止生成
- 运行边界：frontend to backend、CLI handler to core service
- 预期效果：persist config、abort loop、show skipped-file feedback
- 已知字段：`sessionId`、`requestId`、`files`、`workspace`

这比只搜 `upload` 或 `provider` 稳得多。它让检索系统按行为和数据流找入口，也提醒 agent：这一步还只是语义检索，不能直接当证据。

### 开源它的原因

`ace-wrapper` 的代码量很小，核心就是 `FileSystemContext.create(str(workspace))` 加 `context.search(args.query)`。我更想保存的是这几行 Python 周围的工作流约束：

1. 不知道关键词时，先语义检索
2. 一次 query 只问一个工作流
3. 把结果当候选文件
4. 读文件后再用 `rg` 确认精确证据
5. 没证据就不要下结论

这些规则放进工具 README、skill 和 agent prompt 后，才会稳定生效。否则每个会话都会重新靠人提醒一遍，提醒多了人也烦。

上一篇说 Harness Engineering 是给 AI 外面套工程轨道。`ace-wrapper` 就是其中一小段轨道：它不让 agent 更会写代码，只是让它更容易先读对地方。
