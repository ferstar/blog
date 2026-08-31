---
title: "Beyond Brute-Force Aborts: Graded Loop Governance for Agents (Warn → Block → Halt)"
slug: "agent-graded-loop-guard-warn-block-halt"
date: "2026-08-31T23:39:00+08:00"
tags: ['AI', 'Agent', 'Rust']
description: "Agents tackling complex tasks often fall into repetitive tool-calling loops that inflate context and exhaust budgets; design a graded guardrail mechanism based on canonical argument hashing and side-effect classification; achieve an autonomous recovery loop spanning gentle steering, synthetic interception, and deterministic halt."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

When running complex tasks, one of the worst states an agent can enter is a repetitive execution loop.

For example, if a regex finds nothing, the model might dispatch the exact same `grep_search` three or four times in a row. Or if a file does not exist, it repeatedly calls `view_file` on the same path. Each call returns an identical empty result or error, yet the model stubbornly keeps trying.

Legacy approaches to handling loops are usually blunt:
1. **Let it run until max_turns exhausts**: Wasting dozens of API calls and crashing with a generic "maximum turns exceeded" error.
2. **Throw an exception immediately upon repetition**: Aborting the task right away. But all the accumulated investigation context and progress vanish with it.

Neither approach works well. We added a Graded Loop Guard to our runtime using a three-tier escalation ladder.

{{< mermaid >}}
flowchart TD
  subgraph Ingestion[Tool Call Ingestion]
    A[Receive Model Tool Call] --> B[Compute Canonical Args Hash]
    B --> C[Classify Side-Effects: Read-Only vs Mutating]
  end

  subgraph Ladder[Graded Escalation Ladder]
    C --> D{Sequential Duplicate Count}
    D -->|1st Duplicate Count=2| E[Warn: Execute Tool & Append Steering Guidance]
    D -->|2nd Duplicate Count=3| F[Block: Intercept Execution & Return Synthetic Error]
    D -->|3rd Duplicate Count=4| G[Halt: Abort Turn & Expose repeated_tool_calls]
  end

  subgraph Outcome[Outcome & Recovery]
    E --> H[Model Reads Hint & Self-Corrects]
    F --> I[Prevent Wasted IO & Force Strategy Shift]
    G --> J[Preserve Context & Provide Clear Diagnostics]
  end

  Ingestion --> Ladder
{{< /mermaid >}}

---

## 1. Why Brute-Force Aborts Fail

Determining whether a model is genuinely looping requires a few distinctions:

- **Read-Only vs. Mutating Tools**: Repeatedly inspecting the same file with read-only tools (`grep`, `view_file`) is often benign, so tolerance can be higher. But repeating mutating actions (`write_to_file` or running write commands) with identical arguments is dangerous.
- **Models Can Self-Correct**: Often, the model is simply stuck in a temporary rut. If you explicitly remind it in the tool result (*"You have run this exact query twice with zero results; please adjust your approach"*), modern reasoning models usually pivot autonomously in the next turn.

The guardrail's design logic is straightforward: **guide first, block physically second, halt last.**

---

## 2. The Three-Tier Escalation Ladder

The guard checks invocations in the `before_tool_call` phase of the main loop:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LoopGuardAction {
    /// Allow: Initial or normal execution
    Allow,
    /// Warn: Inject guidance into tool result, execute normally
    Warn,
    /// Block: Prevent physical execution, return synthetic error
    Block,
    /// Halt: Abort active turn
    Halt,
}
```

### Tier 1: Warn (Steering Guidance Injection)

When the same tool with identical normalized arguments appears for the second time in a task:
- The tool executes normally.
- When the tool finishes, the runtime appends an automated notice to the end of the `ToolResult`:
  > `[System Notice] You have executed this tool repeatedly with identical arguments without progress. Do not repeat identical calls. Adjust your search pattern, change the target path, or switch tools.`
- Most models immediately adjust their strategy on the next turn.

### Tier 2: Block (Synthetic Interception)

If the model ignores the warning and calls the exact same tool a third time:
- The guard short-circuits the call, skipping physical file I/O or command execution entirely.
- A structured error (`ToolResultContent::Error`) is synthesized at the protocol layer, informing the model that repeated execution was blocked.
- LLM protocols mandate that every `tool_use` must have an accompanying `tool_result`. Returning a synthetic error preserves protocol parity while preventing wasted computation.

### Tier 3: Halt (Safe Turn Abort)

If duplicate calls reach four (`HALT_AFTER = 4`), the model is stuck:
- The runtime ends the current turn and triggers `RepeatedToolCalls`.
- The UI and logs explicitly identify the offending tool name and arguments.
- Prior session history remains intact on disk, allowing the user to guide the agent with a follow-up prompt without re-running from scratch.

---

## 3. Canonical Argument Matching

To prevent false negatives from varying JSON key order, the guard sorts JSON object keys recursively before computing `canonical_args_hash`. This ensures `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` yield identical fingerprints.

Tools are also categorized as `ReadOnly` or `Mutating`, applying tighter thresholds to state-modifying actions.

---

## 4. Takeaway

In real workloads, most edge-case loops resolve autonomously during the `Warn` tier.

Replacing abrupt aborts with a progressive ladder of warnings, synthetic blocks, and clean halts preserves token budgets while meaningfully boosting task completion rates.
