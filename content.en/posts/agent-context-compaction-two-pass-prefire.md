---
title: "Moving Context Compaction Off the Critical Path: Two-Pass Prefire and Recovery Hints for Long-Running Agents"
slug: "agent-context-compaction-two-pass-prefire"
date: "2026-08-31T23:20:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "In-flight context compaction causes noticeable UI pauses and drops execution details in long agent sessions; introduce Two-Pass Prefire background summarization with append-only JSONL recovery hints, alongside prune-first retries and terminal checkpoints; achieve near-zero perceived compaction latency while retaining full historical detail retrieval."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

When building autonomous agents designed for long-running, complex tasks, the context window remains an ever-present sword of Damocles.

As a session stretches across dozens of turns and hundreds of tool invocations (reading files, searching codebases, running test suites, analyzing build logs), context tokens inevitably approach their ceiling. Historically, the standard approach was synchronous, single-pass compaction: packaging all past messages into a massive payload, dispatching it to an LLM for a global summary, and replacing older turns wholesale.

In practice, this brute-force approach introduces several painful problems:

1. **Severe Frontend Latency**: When compaction triggers, the main agent loop must freeze to wait for a heavyweight LLM summarization request. To the user, the input box locks up or the agent appears frozen for several seconds or even tens of seconds.
2. **Irreversible Loss of Detail**: Once distilled into generic prose, specific stack trace line numbers, scattered environment parameters, or intermediate test outputs vanish. If subsequent steps require these details, the model must re-run exploratory tools from scratch or hallucinate.
3. **KV Cache Invalidation**: Injecting the generated summary directly into the System Prompt mutates the prompt prefix on the model provider's servers. This invalidates prefix prompt caching, significantly increasing time-to-first-token (TTFT) and API costs for all subsequent turns.
4. **Wasted Full Summarization**: Frequently, context spikes simply because a few tool invocations produced massive payloads (such as huge `git diff` or `cargo check` outputs). Pruning these tool outputs alone would free sufficient tokens, yet the runtime still pays the full cost of an expensive LLM summary.

Over the past three days, we completed an in-depth overhaul of the context management system in our agent runtime harness. Our goal was clear: **move heavy compaction off the critical path, keep history retrievable, and make the state machine deterministic at critical boundaries.**

{{< mermaid >}}
flowchart TD
  subgraph Prefire["Phase 1: Pass 1 Prefire (Tokens >= 90%)"]
    A[Reach 90% threshold margin] --> B["Slice 95% prefix history<br/>(Preserve tool_use/result pairs)"]
    B --> C["Async background LLM summary"]
    C --> D["Generate NOTE1 summary<br/>+ Cache prefix fingerprint"]
  end

  subgraph Ongoing["Foreground Execution"]
    U[User turns / Multiple tool calls] --> E[Stream new messages normally]
  end

  subgraph Compaction["Phase 2: Pass 2 Compaction (Tokens >= 100%)"]
    F[Reach 100% compaction threshold] --> G{Fingerprint matches?}
    G -- Yes --> H["Combine NOTE1 + tail delta"]
    G -- No / Failed --> I["Fallback to full single-pass summary"]
    H --> J[Generate final summary]
    I --> J
    J --> K["Inject standalone summary<br/>+ Attach recovery_hint path pointer"]
  end

  Prefire -. Async background .-> Ongoing
  Ongoing --> F
{{< /mermaid >}}

---

## 1. Two-Pass Prefire: Moving Heavy Compaction Off the Critical Path

The most effective way to eliminate perceived UI stutter is to perform the heaviest work asynchronously before the hard limit is reached. Inspired by production-grade agent architectures, we implemented a **Two-Pass Prefire** compaction mechanism.

### Phase 1: Prefix Prefire (Pass 1)

We introduced a safety buffer into the configuration (`prefire_margin_tokens`, e.g., reserving a 10% margin).

When context usage reaches 90% of the threshold, the agent does not interrupt the active turn. Instead, it dispatches an asynchronous Pass 1 task in the background:
- **Prefix Splitting**: It slices the oldest 95% (`prefire_prefix_fraction`) of the message history. The slice boundary strictly respects `tool_use` and `tool_result` pairings, ensuring no unclosed tool execution is severed.
- **Intermediate Artifact Extraction**: The prefix history is sent to a background LLM request to generate a structured prefix note (`NOTE1`), accompanied by a lightweight cryptographic fingerprint of the input history.
- **Non-Blocking Cache**: Pass 1 runs entirely inside an isolated, non-blocking Tokio task while the frontend continues streaming user and agent turns normally.

### Phase 2: Incremental Compaction (Pass 2)

When subsequent turns push total tokens beyond the 100% threshold, the main loop enters formal compaction:
- It verifies the Pass 1 prefix fingerprint. If the prefix history has not drifted and the background task finished successfully, the cached `NOTE1` is retrieved immediately.
- The LLM no longer needs to read tens of kilobytes of raw history. It only needs to combine the compact `NOTE1` with the few tail messages produced after Pass 1 to synthesize the final summary.
- **Graceful Fallback**: If the history drifted or Pass 1 failed, the runtime cleanly falls back to standard single-pass compaction, ensuring correctness.

This shrinks the LLM input payload during active compaction by over 80%, reducing main-loop latency down to milliseconds.

---

## 2. Recovery Hints: Compaction Is Not Deletion

Many agent runtimes permanently purge old messages from memory and disk after compaction. This causes the agent to develop severe amnesia in the later stages of long tasks.

In our design:
1. **Append-Only Single Source of Truth**: All raw messages, tool calls, and complete inputs/outputs are continuously appended to the underlying session JSONL file and are never physically deleted.
2. **Recovery Pointer Injection**: Following the generated `<compaction-summary>`, the system automatically appends a `<recovery_hint>` tag, explicitly informing the model:
   - The current conversational history has been summarized;
   - The full, verbatim transcript is preserved in the local JSONL file;
   - If subsequent steps require precise file paths, exact stack trace lines, or raw command outputs, the agent can directly query this file using read tools (such as `view_file` or `grep_search`).
3. **Preserving Frozen System Prompts**: Summaries are injected as standalone conversation turns rather than mutating the System Prompt. This preserves provider-side prefix prompt caching, lowering API costs and first-token latency.

---

## 3. Prune-First Retries and Terminal Checkpoints

Beyond two-pass summarization and recovery pointers, we closed two critical state-machine gaps:

### Prune-Only Retries

The first line of defense in compaction is pruning (`trim_old_tool_results`). Often, a single verbose command (such as `find` or inspecting an enormous file) inflates context. Truncating stale tool outputs into compact previews can instantly reclaim tens of thousands of tokens.

Previously, if pruning alone succeeded without requiring an LLM summary, the state machine would mistakenly report that the context had not changed and throw an overflow error. We now explicitly track `tool_results_trimmed`. When tool outputs are pruned, `context_changed = true` is set, authorizing an immediate overflow retry without invoking an unnecessary LLM summary call.

### Terminal Turn Checkpoints

Compaction used to trigger only passively right before dispatching the next model request. If an agent's concluding reply (receiving `EndTurn`) happened to push context over the threshold, suspending the session would leave an oversized snapshot on disk.

We refined terminal state handling: when a completed turn crosses the threshold, the runtime immediately executes compaction and persists the checkpoint between `MessageComplete` and `TurnEnd`. When the user next wakes the session, it starts cleanly with a compact context.

---

## 4. Coordinated Defense: Graded Loop Guard

A primary cause of rapid context exhaustion is an agent spinning in a repetitive tool loop (e.g., executing the exact same `grep` or `read_file` 3 times in a row).

To stop wasteful context growth at the source, we integrated a Graded Loop Guard:
- **Tool Classification**: Tools are categorized into idempotent (read-only) and mutating operations.
- **Three-Tier Escalation**:
  1. **Warn**: On the first detected repetition, guidance text is appended to the tool result, prompting the model to adjust its approach;
  2. **Block**: On the second repetition, the underlying tool execution is blocked and a synthetic error is returned, stopping wasted computation while preserving `tool_use`/`tool_result` protocol parity;
  3. **Halt**: After sustained failures, the turn halts completely and delivers an explicit `repeated_tool_calls` status to the frontend, replacing vague "maximum turns reached" notices.

---

## 5. Empirical Results: 40% Token Reduction and 99%+ Cache Hit Rate

In an intensive real-world session benchmark spanning 47 consecutive hours, 1,000 requests, and 490 million input tokens, this holistic context governance architecture delivered dramatic performance gains:

| Key Metrics | Pre-Optimization (964 turns) | Post-Optimization (36 turns) | Change |
| :--- | :--- | :--- | :--- |
| **Avg. Input / Turn** | 496,806 tokens | 299,625 tokens | **↓ 40%** |
| **Context Shape** | 1.75M tokens full replay | ~250K baseline / 280K steady | **Healthy & bounded** |
| **Prompt Cache Hit Rate** | 99.11% | 96.91% (includes cold restarts) | **Stable (99%+ sustained)** |

### Key Performance Metrics

1. **40% Reduction in Average Input Tokens Per Turn**:
   - Pre-optimization average input tokens per turn reached **496,806 tokens**;
   - Post-optimization average input tokens dropped to **299,625 tokens**, achieving a **40% net reduction** in per-turn payload sizes.
2. **Deterministic and Bounded Context Growth**:
   - Pre-optimization sessions suffered unbounded inflation, at worst replaying **1.75 million tokens** on every interaction;
   - Post-optimization sessions initialize smoothly at **~250K tokens** following incremental compaction, scaling predictably around a 280K token equilibrium.
3. **Sustained 99%+ Prompt Cache Hit Rate**:
   - Across the entire 490M input token lifecycle, the cumulative cache hit rate reached **99.06%**.
   - Among 36 measured post-optimization turns, **33 turns maintained a 99%~100% cache hit rate**. Only the initial turn following compaction or interruption experienced a minor reconstruction miss (~20K–23K tokens, maintaining a 92%~95% hit rate), after which subsequent continuous turns instantly rebounded to 99%+.

---

## Summary

This optimized context management pipeline transforms unpredictable, stutter-prone single-pass compaction into a system that is **proactive (Prefire), traceable (Recovery Hints), cost-efficient (Prune-First), and defensive (Loop Guards)**.

Empirical telemetry proves that keeping long-running agents resilient depends not only on the model's intrinsic reasoning capabilities, but also on how smoothly and deterministically the runtime Harness governs context lifecycles.
