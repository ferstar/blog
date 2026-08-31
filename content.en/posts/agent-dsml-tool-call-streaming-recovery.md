---
title: "When Models Leak Tool Calls as Text: Stream Recovery with a Cross-Chunk DSML State Machine"
slug: "agent-dsml-tool-call-streaming-recovery"
date: "2026-08-31T23:38:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "Certain models occasionally leak tool invocations as raw full-width DSML text rather than structured payloads, breaking agent execution; design a provider-agnostic, cross-chunk streaming state machine with defensive protocol recovery; completely prevent text leakage while transparently restoring tool calls to active execution."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

When integrating diverse models for coding agents, transport quirks are bound to happen.

One recurring issue is when a model, instead of returning structured function calls via the standard `tool_calls` payload, dumps raw XML markup directly into the text stream (`content` or `output_text.delta`).

In certain reasoning models (such as DeepSeek derivatives or proxied gateways), it often looks like this:

```text
＜ＤＳＭＬ＜tool_calls＞
＜ＤＳＭＬ＜invoke name="read_file"＞
＜ＤＳＭＬ＜parameter name="path"＞"src/main.rs"＜／ＤＳＭＬ＜／parameter＞
＜／ＤＳＭＬ＜／invoke＞
＜／ＤＳＭＬ＜／tool_calls＞
```

If the transport layer simply passes these tokens through to the UI as plain text:
1. The agent loop receives zero `tool_call` events, stalling the task.
2. The user's screen gets littered with unparsed full-width XML tags.

To handle this cleanly in our runtime, we built a cross-chunk streaming DSML recovery state machine.

{{< mermaid >}}
flowchart TD
  subgraph Ingestion[Streaming Input Token Chunks]
    A[Chunk 1: Protocol Prefix] --> B[Chunk 2: invoke name=read_file]
    B --> C[Chunk 3: parameter name=path]
    C --> D[Chunk 4: Protocol Closing Tag]
  end

  subgraph StateMachine[DSML Streaming State Machine]
    S1[Detect Prefix: ＜ＤＳＭＬ＜] --> S2{Is Prompt Example?}
    S2 -->|Yes| S3[Disable Recovery / Stream as Text]
    S2 -->|No| S4[Capture Mode / Hold Text Output]
    S4 --> S5[Buffer Chunks & Assemble Tags]
    S5 --> S6{Is Markup Valid & Closed?}
    S6 -->|No or Over Limit| S7[Fail-Closed / Emit Safe Error]
    S6 -->|Yes| S8[Extract Tool Name & Parameter Pairs]
  end

  subgraph Dispatch[Protocol Conversion & Dispatch]
    S8 --> E1[Validate against Tool Schema & Deserialize]
    E1 --> E2[Synthesize ToolCall & ToolUse Events]
    E2 --> E3[Agent Loop Executes Real Tool]
  end

  Ingestion --> StateMachine
{{< /mermaid >}}

---

## 1. Where the Complexity Lies

If you receive a single, complete HTTP response body, extracting the tags via regex or an XML parser is straightforward. But agents require low-latency streaming text, which introduces several constraints:

1. **Chunk Fragmentation**: Output arrives token-by-token. A tag like `＜ＤＳＭＬ＜invoke` might arrive fragmented as `["＜", "ＤＳ", "ＭＬ＜in", "voke"]` across four separate network packets. Single-chunk regex matching is ineffective.
2. **Hold Buffers**: When receiving a partial prefix (like a standalone `＜`), we cannot stream it immediately to the client (in case it turns out to be markup). But we also cannot hold it indefinitely; normal text must flush immediately once verified.
3. **User Prompt Examples**: If a user is explicitly discussing DSML syntax (e.g., *"What does ＜ＤＳＭＬ＜ mean?"*), the state machine must recognize this and disable recovery, rather than attempting to execute quoted examples as real system commands.
4. **Native vs. DSML Conflicts**: If a model returns both native structured tool calls and raw DSML text in the same turn, we fail closed to prevent duplicate executions.

---

## 2. State Machine Design & Intermediate Representation

To support multiple providers (OpenAI-compatible endpoints, Responses APIs), the state machine operates on a decoupled Intermediate Representation:

```rust
pub enum DsmlOutcome {
    /// Confirmed user-visible text, released for frontend streaming
    Text(String),
    /// Successfully captured and parsed complete tool invocations
    ToolCalls(Vec<DsmlToolCall>),
}

pub struct DsmlToolCall {
    pub id: String,
    pub name: String,
    pub arguments: String, // Normalized standard JSON string
}
```

The provider passes incoming text chunks into the state machine:
- It maintains an internal `capture_buffer`.
- Once `＜ＤＳＭＬ＜` is detected, it switches to capture mode, pausing downstream `TextDelta` emissions.
- A `DSML_CAPTURE_LIMIT` (256KB) guards against memory exhaustion from malformed output.

---

## 3. Schema Validation & Event Synthesis

When closed tags are parsed, `<invoke>` and `<parameter>` nodes are extracted:
1. Verify the tool name exists in the current registry.
2. Parse non-string parameters into valid JSON values.
3. Validate against the tool's registered JSON Schema.
4. Synthesize native `ToolCallStart`, `ToolInputDelta`, and `ToolUse` events.

From the agent loop's perspective, this is indistinguishable from standard provider tool calls, routing directly into normal tool execution.

---

## 4. Takeaway

When building agent runtimes against varied model endpoints, output formatting anomalies are inevitable. Absorbing these quirks in the transport adapter layer keeps higher-level agent state machines clean and dependable.
