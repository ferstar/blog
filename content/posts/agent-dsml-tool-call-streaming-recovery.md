---
title: "大模型把工具调用吐成了文本？跨 Chunk 流式状态机的 DSML 抢救实录"
slug: "agent-dsml-tool-call-streaming-recovery"
date: "2026-08-31T23:38:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "部分大模型在流式输出时会将工具调用作为全角 DSML 文本泄漏导致调用失效；设计 Provider 无关的跨 Chunk 流式状态机与协议拦截恢复器；实现文本泄漏完全阻断且工具调用零损耗恢复执行。"
series: ['AI Coding']
---

在接入多种异构大模型（尤其是各类开源或具备特定训练背景的推理模型）构建 Agent 时，底层协议适配往往充满意想不到的“深水坑”。

最经典且棘手的一个问题就是：**模型偶尔不走标准 API 的结构化工具调用（Function / Tool Calls）字段，而是把整套工具调用指令直接作为正文文本流式吐了出来。**

在某些特定模型（例如 DeepSeek 系模型或经过反代转换的推理网关）中，工具调用常被包裹在一种基于 XML 的全角标记语言（DSML，DeepSeek Markup Language）中：

```text
＜ＤＳＭＬ＜tool_calls＞
＜ＤＳＭＬ＜invoke name="read_file"＞
＜ＤＳＭＬ＜parameter name="path"＞"src/main.rs"＜／ＤＳＭＬ＜／parameter＞
＜／ＤＳＭＬ＜／invoke＞
＜／ＤＳＭＬ＜／tool_calls＞
```

当传输层（如 OpenAI Chat Completions 或 Responses API）直接按普通文本（`content` / `output_text.delta`）把这些 token 推给前端时，会引发两重灾难：
1. **工具调用彻底丢失**：Agent 的主事件循环没有收到任何 `tool_call` 事件，任务停滞；
2. **严重的用户体验灾难**：几百行晦涩难懂的全角 XML 标签像打字机一样直接糊在用户的聊天界面上。

为了彻底抹平异构模型的输出不确定性，我们在 Agent 运行时中设计了一套**跨 Chunk 流式 DSML 恢复状态机**。

{{< mermaid >}}
flowchart TD
  subgraph Ingestion[流式输入 Token Chunks]
    A[分片 1: 协议前缀片段] --> B[分片 2: invoke name=read_file]
    B --> C[分片 3: parameter name=path]
    C --> D[分片 4: 协议闭标签]
  end

  subgraph StateMachine[DSML 流式状态机]
    S1[探测协议标记] --> S2{是否为 Prompt 示例?}
    S2 -->|是| S3[禁用恢复 / 原样透传文本]
    S2 -->|否| S4[捕获模式 / 阻断文本泄漏]
    S4 --> S5[跨分片缓冲与标签聚合]
    S5 --> S6{协议是否合法闭合?}
    S6 -->|否或超限| S7[Fail-Closed / 安全报错]
    S6 -->|是| S8[提取工具名称与参数键值对]
  end

  subgraph Dispatch[协议转换与分发]
    S8 --> E1[按 Tool Schema 校验并反序列化]
    E1 --> E2[合成底层 ToolCall 与 ToolUse 事件]
    E2 --> E3[Agent Loop 执行实体工具]
  end

  Ingestion --> StateMachine
{{< /mermaid >}}

---

## 1. 为什么流式恢复比想象中复杂？

如果是一次性拿到了完整的 HTTP 响应文本，用正则表达式或 XML 解析器提取内容并不难。但 Agent 必须保持极致的**低延迟流式打字体验**，在流式场景下做抢救面临几个苛刻挑战：

1. **Token 碎片化（Chunk Fragmentation）**：大模型的输出是逐 token 吐出的，`＜ＤＳＭＬ＜invoke` 这样的标签可能被随意切碎成 `["＜", "ＤＳ", "ＭＬ＜in", "voke"]` 分散在连续 4 个网络 chunk 中。任何基于单 chunk 的正则匹配都会失效。
2. **前缀暂扣与延迟决策（Hold Buffer）**：当收到半个疑似标签时（例如仅仅一个全角 `＜`），系统不能立即将其发给前端（否则一旦后续确认是 DSML 协议，用户界面已经泄漏了字符）；但又不能无限制缓冲，必须在确定是普通文本时立即把暂扣的内容释放出来。
3. **用户 Prompt 示例防混淆（User Example Protection）**：如果用户是在向 Agent 请教“*请解释什么是 DSML，比如 ＜ＤＳＭＬ＜...*”，状态机必须精准识别并**禁用恢复**，防止把用户的讨论误当成真实的系统工具调用执行。
4. **原生与 DSML 冲突检测（Native vs DSML Conflict）**：若模型在同一轮次中同时返回了原生结构化工具调用和正文 DSML 文本，系统必须采取防御性的 Fail-Closed 策略，严禁产生重复或混乱的调用执行。

---

## 2. 状态机核心架构：Provider 无关的中间表示

为了让同一套抢救逻辑能够无缝复用到各种不同的传输协议（OpenAI 兼容接口、Responses API、Anthropic 协议等），我们将状态机抽象为独立的公共模块，产出结构化的中间表示（Intermediate Representation）：

```rust
pub enum DsmlOutcome {
    /// 确认是普通文本，放行给前端渲染
    Text(String),
    /// 成功从文本流中捕获并闭合出完整的工具调用
    ToolCalls(Vec<DsmlToolCall>),
}

pub struct DsmlToolCall {
    pub id: String,
    pub name: String,
    pub arguments: String, // 规范化后的标准 JSON 字符串
}
```

各 Provider 传输层（如 `responses.rs`）接收到上游模型的 `output_text.delta` 文本流时，统一喂给 `DsmlStreamParser` 状态机。

---

## 3. 关键边缘场景的处理策略

### 跨 Chunk 的流式标签聚合与截断保护

状态机内部维护了一个滑动捕获缓冲区（`capture_buffer`）。
- 状态机时刻监听全角前缀 `＜ＤＳＭＬ＜`。
- 一旦探测到潜在协议头，状态机立即进入 `Buffering` 状态，阻断下游的 `TextDelta` 发送。
- 为防止恶意或失控模型输出超大非法文本撑爆内存，设置了严格的硬上限（如 `DSML_CAPTURE_LIMIT = 256KB`）。一旦超限未闭合，立即判定为 `BufferLimit` 错误并阻断。

### 参数解析与 Schema 强校验

全角 DSML 的内部结构由 `<invoke name="...">` 与 `<parameter name="...">` 标签组成。参数内容可能是简单标量，也可能是复杂的 JSON 数组或对象。

状态机在提取出各个 `<parameter>` 后：
1. 校验工具名称是否属于当前运行时已注册的工具集；
2. 对非纯字符串参数尝试 JSON 反序列化解析；
3. 按照注册工具的 JSON Schema 进行校验，确保参数类型与必填项完全合法；
4. 将其序列化为干净、标准的 JSON 字符串 `{"path": "src/main.rs"}`。

### 优雅合成原生事件流

当状态机解析出合法的 `DsmlOutcome::ToolCalls` 时，传输层将即时把这些结构体转化为 Agent 运行时底层的标准事件：
- 发送 `ToolCallStart`（携带唯一生成的递增 Tool ID）；
- 发送 `ToolInputDelta`；
- 发送 `ToolUseStart` / `ToolUse`。

在 Agent Loop 看来，这与模型原生返回的 Function Call 没有任何区别，驱动主流程无缝进入工具执行阶段。

---

## 4. 收益与工程启示

引入 DSML 流式恢复机制后，我们彻底解决了偶发性协议泄漏问题：

1. **协议零泄漏**：全角 XML 协议标记被 100% 拦截在底层传输层，前端用户界面干净清爽；
2. **任务零失败**：原本会因为格式错乱导致中断的 Agent 任务，全部被无缝救回并正确执行；
3. **架构内聚**：将异构模型协议抹平在最底层的 Transport 转换层，上层业务状态机与 Tool 调度逻辑无需感知任何模型厂商的特化怪癖。

构建坚固的 Agent 运行时，往往不在于接入了多少新能力，而在于底层是否有足够多的**防御性管道（Defensive Pipelines）**，去兜住模型输出一切不可控的边缘情况。
