---
title: "When Models Leak Tool Calls as Text: Stream Recovery with a Cross-Chunk DSML State Machine"
slug: "agent-dsml-tool-call-streaming-recovery"
date: "2026-08-31T23:38:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "Certain models occasionally leak tool invocations as raw full-width DSML text rather than structured payloads, breaking agent execution; design a provider-agnostic, cross-chunk streaming state machine with defensive protocol recovery; completely prevent text leakage while transparently restoring tool calls to active execution."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

When integrating heterogeneous large language models into agent runtimes—especially open-source or custom fine-tuned reasoning models—the underlying transport protocol is often fraught with unexpected edge cases.

One of the most persistent and frustrating issues is when **a model bypasses standard structured function/tool call payloads and instead streams raw tool call protocols directly into the conversational text body.**

In certain model families (such as DeepSeek derivatives or proxied inference gateways), tool invocations are sometimes formatted using XML-style full-width markup known as DSML (DeepSeek Markup Language):

```text
＜ＤＳＭＬ＜tool_calls＞
＜ＤＳＭＬ＜invoke name="read_file"＞
＜ＤＳＭＬ＜parameter name="path"＞"src/main.rs"＜／ＤＳＭＬ＜／parameter＞
＜／ＤＳＭＬ＜／invoke＞
＜／ＤＳＭＬ＜／tool_calls＞
```

When the transport layer (such as OpenAI Chat Completions or Responses API) blindly relays these tokens as standard text deltas (`content` or `output_text.delta`), it triggers a double failure:
1. **Broken Tool Execution**: The agent's event loop receives zero structured `tool_call` events, stalling the ongoing task.
2. **Degraded User Experience**: Hundreds of lines of unparsed, full-width XML markup stream directly onto the user's chat screen like a runaway typewriter.

To insulate our agent runtime from these format anomalies, we designed a **cross-chunk streaming DSML recovery state machine**.

{{< mermaid >}}
flowchart TD
  subgraph Ingestion[Streaming Input Token Chunks]
    A[Chunk 1: Protocol Prefix] --> B[Chunk 2: invoke name=read_file]
    B --> C[Chunk 3: parameter name=path]
    C --> D[Chunk 4: Protocol Closing Tag]
  end

  subgraph StateMachine[DSML Streaming State Machine]
    S1[Detect Protocol Marker] --> S2{Is Prompt Example?}
    S2 -->|Yes| S3[Disable Recovery / Pass as Text]
    S2 -->|No| S4[Capture Mode / Hold Text Output]
    S4 --> S5[Cross-Chunk Buffering & Tag Assembly]
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

## 1. Why Streaming Recovery Is Harder Than It Looks

If you receive the complete HTTP response body all at once, extracting content with regular expressions or XML parsers is trivial. However, modern agent systems demand an **instantaneous, low-latency streaming experience**. Performing in-flight protocol recovery introduces stringent constraints:

1. **Token Fragmentation Across Chunks**: LLM output arrives token-by-token. A tag like `＜ＤＳＭＬ＜invoke` might arrive fragmented as `["＜", "ＤＳ", "ＭＬ＜in", "voke"]` across four distinct network packets. Single-chunk pattern matching completely breaks.
2. **Hold Buffers and Deferred Emission**: When receiving the beginning of a potential protocol marker (e.g., a single full-width `＜`), the transport layer cannot immediately emit it to the client (otherwise, if it proves to be protocol markup, the screen has already been polluted). Conversely, it cannot buffer indefinitely; it must flush immediately once confirmed to be regular text.
3. **User Prompt Example Protection**: If a user explicitly asks the agent, *"Can you explain what DSML is, such as ＜ＤＳＭＬ＜..."*, the state machine must recognize this and **disable recovery**, avoiding accidental execution of user-quoted text as real system commands.
4. **Native vs. DSML Conflict Resolution**: If a model emits both native structured tool calls and in-stream DSML markup in the same turn, the runtime must adopt a defensive fail-closed posture to prevent duplicate or conflicting invocations.

---

## 2. State Machine Architecture: Provider-Agnostic IR

To enable seamless reuse across disparate transports (OpenAI-compatible endpoints, Responses APIs, and Anthropic protocols), we decoupled the parser into a standalone module producing a structured Intermediate Representation (IR):

```rust
pub enum DsmlOutcome {
    /// Confirmed user-visible text, released for frontend streaming
    Text(String),
    /// Successfully parsed and validated complete tool invocations
    ToolCalls(Vec<DsmlToolCall>),
}

pub struct DsmlToolCall {
    pub id: String,
    pub name: String,
    pub arguments: String, // Normalized standard JSON string
}
```

Transport adapters feed incoming `output_text.delta` streams into the `DsmlStreamParser` state machine, decoupling higher-level agent logic from protocol rescue mechanics.

---

## 3. Handling Critical Edge Cases

### Cross-Chunk Tag Aggregation and Buffer Bounds

The state machine maintains an internal sliding buffer (`capture_buffer`).
- It continuously scans for the full-width marker prefix `＜ＤＳＭＬ＜`.
- Once detected, it transitions to `Buffering` state, holding back downstream `TextDelta` emissions.
- To prevent unbounded memory consumption from malformed model output, a hard capture limit is enforced (`DSML_CAPTURE_LIMIT = 256KB`). Exceeding this boundary triggers a safe `BufferLimit` error.

### Parameter Extraction and Schema Validation

Inside DSML blocks, invocations are defined by `<invoke name="...">` and nested `<parameter name="...">` elements. Parameters can be simple primitives or complex nested JSON objects.

Upon capturing closed parameter tags:
1. The tool name is verified against currently registered runtime tools;
2. Non-string parameters undergo strict JSON deserialization;
3. Arguments are validated against the tool's JSON Schema for type safety and required fields;
4. The arguments are normalized into a standard JSON string: `{"path": "src/main.rs"}`.

### Seamless Native Event Synthesis

When the state machine yields a valid `DsmlOutcome::ToolCalls`, the transport adapter immediately translates it into the runtime's native event stream:
- Emits `ToolCallStart` (with a sequentially generated unique tool ID);
- Emits `ToolInputDelta`;
- Emits `ToolUseStart` / `ToolUse`.

To the main Agent Loop, this synthetic event stream is indistinguishable from a native provider function call, cleanly routing the turn into tool execution.

---

## 4. Engineering Takeaways

Integrating in-flight DSML recovery yielded immediate reliability benefits:

1. **Zero Protocol Leakage**: Full-width XML markers are intercepted entirely at the transport boundary, preserving clean UI rendering.
2. **Zero Dropped Invocations**: Tasks that previously stalled due to syntax quirks are recovered seamlessly and executed without user intervention.
3. **Architectural Isolation**: Vendor-specific output quirks are normalized at the lowest transport adapter layer, keeping higher-level agent state machines clean and unpolluted.

Building resilient agent systems is rarely about adding superficial capabilities; it is about establishing robust **defensive pipelines** that absorb the inherent messiness and non-determinism of model outputs.
