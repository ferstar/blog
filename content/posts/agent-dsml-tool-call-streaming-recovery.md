---
title: "大模型把工具调用吐成了文本？跨 Chunk 流式状态机的 DSML 抢救实录"
slug: "agent-dsml-tool-call-streaming-recovery"
date: "2026-08-31T23:38:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "部分大模型在流式输出时会将工具调用作为全角 DSML 文本泄漏导致调用失效；设计 Provider 无关的跨 Chunk 流式状态机与协议拦截恢复器；实现文本泄漏完全阻断且工具调用零损耗恢复执行。"
series: ['AI Coding']
---

接不同模型跑 Agent 时，最怕遇到底层协议的不讲道理。

最常见的一个坑是：模型明明应该走标准的 `tool_calls` 结构体字段返回工具调用，结果偶发把一整段全角 XML 标记当成普通文本，直接塞进 `content` 或 `output_text.delta` 里流式吐了出来。

典型格式长这样（DeepSeek 系或部分转换网关常见）：

```text
＜ＤＳＭＬ＜tool_calls＞
＜ＤＳＭＬ＜invoke name="read_file"＞
＜ＤＳＭＬ＜parameter name="path"＞"src/main.rs"＜／ＤＳＭＬ＜／parameter＞
＜／ＤＳＭＬ＜／invoke＞
＜／ＤＳＭＬ＜／tool_calls＞
```

如果传输层老老实实当普通文本发给前端，后果很直接：
1. Agent 主循环没收到任何 `tool_call` 事件，任务卡死在原地；
2. 用户屏幕上开始一行行打印这些晦涩的全角 XML 代码。

为了在底层抹平这种输出异常，我们在运行时里加了一套跨 Chunk 的流式 DSML 恢复状态机。

{{< mermaid >}}
flowchart TD
  subgraph Ingestion[流式分片输入]
    A[分片 1: 协议前缀片段] --> B[分片 2: invoke name=read_file]
    B --> C[分片 3: parameter name=path]
    C --> D[分片 4: 协议闭标签]
  end

  subgraph StateMachine[DSML 流式状态机]
    S1[探测前缀: ＜ＤＳＭＬ＜] --> S2{是否为用户 Prompt 示例?}
    S2 -->|是| S3[禁用恢复 / 原样透传文本]
    S2 -->|否| S4[进入捕获模式 / 暂扣文本]
    S4 --> S5[跨分片缓冲与标签拼接]
    S5 --> S6{协议是否闭合?}
    S6 -->|否或超限| S7[Fail-Closed 报错退出]
    S6 -->|是| S8[提取工具名称与参数]
  end

  subgraph Dispatch[事件转换与分发]
    S8 --> E1[按 Tool Schema 校验并解析 JSON]
    E1 --> E2[合成 ToolCallStart / ToolUse 事件]
    E2 --> E3[Agent 主循环正常执行工具]
  end

  Ingestion --> StateMachine
{{< /mermaid >}}

---

## 1. 难点在哪？

如果是一次性拿到的完整 HTTP Response，写两行正则或用 XML 解析器把内容捞出来并不难。但 Agent 要保持实时的流式打字输出，问题就变复杂了：

1. **分片切割（Chunk Fragmentation）**：大模型的输出是一小截一小截来的。`＜ＤＳＭＬ＜invoke` 可能会被切碎成 `["＜", "ＤＳ", "ＭＬ＜in", "voke"]` 分在好几个网络包里。单包做正则匹配根本靠不住。
2. **文本暂扣（Hold Buffer）**：收到半个前缀（比如只有一个全角 `＜`）时，不能急着推给前端，否则一旦后面跟的是 DSML 标签，屏幕上就已经印出脏字符了；但也不能无限期憋着，确认是普通文本后必须马上补发。
3. **用户 Prompt 包含示例时防误判**：如果用户正好在问“*请解释什么是 DSML，比如 ＜ＤＳＭＬ＜...*”，状态机必须认出来并关掉恢复逻辑，不能把用户举的例子当成真工具去调。
4. **原生与 DSML 冲突**：如果模型在同一轮里既给了原生 `tool_calls` 又在正文里吐 DSML，必须走 Fail-Closed 判定，不能重复执行。

---

## 2. 状态机设计与中间表示

为了在不同协议（OpenAI 格式、Responses API 等）间复用，状态机被抽成了独立模块，只产出中间表示：

```rust
pub enum DsmlOutcome {
    /// 确认是正常文本，放行给前端渲染
    Text(String),
    /// 从流式文本里完整捞出了工具调用
    ToolCalls(Vec<DsmlToolCall>),
}

pub struct DsmlToolCall {
    pub id: String,
    pub name: String,
    pub arguments: String, // 规范化后的标准 JSON 字符串
}
```

底层 Provider 收到文本增量后喂给状态机：
- 状态机内部维护一段 `capture_buffer`，平时处于透明直通状态。
- 一旦碰到 `＜ＤＳＭＬ＜`，立刻切到暂扣模式，暂停向下游派发 `TextDelta`。
- 加了 `DSML_CAPTURE_LIMIT`（256KB）上限，防止异常输出无限吃内存。

---

## 3. 参数校验与事件合成

状态机捕获到完整的闭合标签后，逐个提取 `<invoke>` 和 `<parameter>`：
1. 查当前的 Tool Registry，确认工具名存在；
2. 把非字符串参数转成合法的 JSON 结构；
3. 对照工具注册的 JSON Schema 做校验；
4. 校验通过后，在 Transport 层就地合成原生的 `ToolCallStart`、`ToolInputDelta` 和 `ToolUse` 事件。

对上层的 Agent 主循环来说，完全不知道底层发生过文本抢救，直接按标准事件流程去调度工具执行。

---

## 4. 总结

做 Agent 接入异构模型，不能假设模型的格式永远 100% 规整。把这种边缘怪癖收拢在底层的 Transport 转换层，上层的任务状态机和工具逻辑才能保持干净。
