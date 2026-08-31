---
title: "Moving Context Compaction Off the Critical Path: Two-Pass Prefire and Recovery Hints for Long-Running Agents"
slug: "agent-context-compaction-two-pass-prefire"
date: "2026-08-31T23:20:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "In-flight context compaction causes noticeable UI pauses and drops execution details in long agent sessions; introduce Two-Pass Prefire background summarization with append-only JSONL recovery hints, alongside prune-first retries and terminal checkpoints; achieve near-zero perceived compaction latency while retaining full historical detail retrieval."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

When running long agent tasks, context grows fast.

Refactoring code, checking logs, running test suites—after dozens of turns, tokens quickly approach their limit. The simplest legacy approach was single-pass compaction: when limits are crossed, stop the main loop, send the entire message history to an LLM for a global summary, and swap out old messages.

In practice, several problems surfaced quickly:

1. **Main-loop pauses**: Sending tens of kilobytes of history for an LLM summary often takes seconds or tens of seconds. The client input box just sits in a loading state.
2. **Lost execution details**: Once condensed into prose, exact error line numbers, file paths, and stray arguments vanish. When subsequent steps need them, the model either re-queries from scratch or hallucinates.
3. **Broken KV caching**: Cramming the summary into the System Prompt mutates the prompt prefix on provider servers, busting Prompt Caching completely and driving up both TTFT and API costs.
4. **Wasted summaries when pruning would suffice**: Often, context blows up simply because a tool dumped a massive `git diff` or build log. Truncating old tool outputs reclaims tens of thousands of tokens without needing an LLM summary at all.

I overhauled our agent runtime's context management over the past three days. Here is what changed.

{{< mermaid >}}
flowchart TD
  subgraph Prefire[Phase 1: Pass 1 Background Prefire]
    A[Tokens hit 90% threshold] --> B[Slice 95% prefix history]
    B --> C[Async background LLM summary]
    C --> D[Cache NOTE1 note and fingerprint]
  end

  subgraph Foreground[Foreground Main Loop]
    U[Normal turns and tool calls] --> E[Generate new turns]
  end

  subgraph Compaction[Phase 2: Pass 2 Compaction]
    F[Tokens cross 100% threshold] --> G{Fingerprint matches?}
    G -->|Match| H[Merge NOTE1 with tail delta]
    G -->|Drift or Failure| I[Fallback to full single-pass summary]
    H --> J[Generate final summary]
    I --> J
    J --> K[Inject standalone summary turn & JSONL pointer]
  end

  Prefire -.->|Runs in background| Foreground
  Foreground --> F
{{< /mermaid >}}

---

## 1. Two-Pass Prefire: Moving Heavy Summaries to the Background

To keep the UI responsive, the heaviest work must happen in the background before the hard limit is hit.

### Phase 1: Prefix Prefire (Pass 1)

We added a safety margin (`prefire_margin_tokens`, defaulting to a 10% buffer).

When context usage reaches 90% of the threshold, the main loop keeps running while spawning a background task:
- **Slice the prefix**: Take the oldest 95% of messages. Slicing must strictly protect `tool_use` and `tool_result` boundaries without severing unclosed invocations.
- **Generate NOTE1**: The prefix is summarized into a structured note (`NOTE1`), and a hash fingerprint of that prefix is stored in cache.
- The foreground streams text normally without interruption.

### Phase 2: Incremental Compaction (Pass 2)

When subsequent turns push total tokens past the 100% threshold, formal compaction kicks in:
- Verify the fingerprint. If the prefix hasn't changed and the background task finished, grab the cached `NOTE1`.
- Instead of feeding the whole history to the model, we only send `NOTE1` plus the few tail messages produced after Pass 1.
- If the fingerprint drifted or Pass 1 failed, it cleanly falls back to standard single-pass compaction.

This cuts the tokens sent during active compaction by over 80%, dropping main-thread wait times to milliseconds.

---

## 2. Compaction Is Not Deletion: Recovery Hints Pointing to Local JSONL

Compacting history shouldn't mean destroying raw details.

1. **Local append-only source of truth**: All raw messages, arguments, and full outputs are continuously written to a local session JSONL file and are never deleted.
2. **Recovery pointers**: The `<compaction-summary>` block automatically includes a `<recovery_hint>` tag containing the session's absolute JSONL path:
   > History has been summarized. Full raw records remain in `session.jsonl`. If subsequent steps require exact line numbers, error traces, or command outputs, inspect this file directly with read tools.
3. **Leave the System Prompt alone**: Summaries are injected as standalone conversation turns. The System Prompt stays frozen, keeping server-side Prompt Caching hit rates high.

---

## 3. Prune First Before Calling an LLM Summary

Often, invoking an LLM for summarization is unnecessary.

Before running full compaction, we execute `trim_old_tool_results` to truncate verbose outputs from older turns into short previews. If pruning frees enough tokens, we set `context_changed = true` and retry immediately, saving an expensive summary call.

We also resolved an edge case: when a turn's final assistant reply (`EndTurn`) pushes context over the threshold, compaction used to wait until the user's next prompt. Now, the runtime compacts and persists checkpoints immediately between `MessageComplete` and `TurnEnd`, ensuring cold reboots wake up to clean context.

---

## 4. Real-World Telemetry

Testing over a continuous 47-hour session with 1,000 requests and 490 million input tokens yielded clear metrics:

| Metric | Pre-fix (964 turns) | Post-fix (36 turns) | Change |
| :--- | :--- | :--- | :--- |
| **Avg. Input / Turn** | 496,806 tokens | 299,625 tokens | **↓ 40%** |
| **Context Shape** | 1.75M full replay (inflated) | ~250K baseline / 280K steady | **Bounded** |
| **Prompt Cache Hit Rate** | 99.11% | 96.91% (includes cold restarts) | **99%+ sustained** |

Average per-turn tokens dropped by 40%, and context stabilized around 280K instead of ballooning uncontrollably. Beyond a minor ~20K cache miss right after compaction restarts, subsequent turns sustained 99% to 100% prompt cache hit rates.

Keeping long-running agents reliable comes down to getting these state transitions and caching boundaries right.
