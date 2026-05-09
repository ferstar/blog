---
title: "From Vibe Coding to Harness Engineering: How My AI Coding Workflow Changed"
slug: "ai-coding-harness-engineering-workflow"
date: "2026-05-09T14:19:00+08:00"
tags: ['Idea', 'AI']
description: "AI coding can generate code but long-running delivery drifts easily; use Harness Engineering to control tasks, context, verification, and recovery; turn AI output into an executable, verifiable, reviewable engineering workflow."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

This is the written version of an internal team sharing session. The slides are here:

[From Vibe Coding to Harness Engineering](/slides/harness-engineering-ai-coding/)

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:1.5rem 0 2rem;border:1px solid rgba(127,127,127,.25);overflow:hidden;">
  <iframe src="/slides/harness-engineering-ai-coding/" title="From Vibe Coding to Harness Engineering" style="position:absolute;inset:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>

In the previous phase, I cared about one question: can AI take over most coding work?

The answer is now fairly clear. If project context, quality gates, and verification workflows are in place, AI-generated code can enter the engineering workflow reliably. Human time gradually moves from “writing” to “verifying”: requirement breakdown, architecture judgment, context organization, boundary checks, and failure handling.

Recent practice moved one step further. The problem is no longer just “how to write prompts.” The real question is whether the whole workflow can support long-running tasks.

### What Changed

Early Vibe Coding solved the entry problem: explain the requirement clearly, put project rules into `AGENTS.md` / `CLAUDE.md`, and let tests, lint, and review catch model output.

That still works, but it is closer to single-task engineering. Once a task runs longer, new problems show up:

- Context keeps growing until the model loses the important part.
- Repeated retries can push the fix further away from the actual problem.
- Without external references, strategy turns into guesswork.
- After many rounds, it becomes hard to tell which changes should be kept.
- User rejection, permission blocks, and empty output need explicit stop semantics.

So I now prefer calling this layer **Harness Engineering**. The focus is to put an engineering track around AI so that tasks are executable, results are verifiable, and failures are recoverable.

{{< mermaid >}}
flowchart LR
  A[Task scope] --> B[Context route]
  B --> C[Agent loop]
  C --> D[Verification gate]
  D --> E[Recovery / memory]
  D -->|failed| F[Patch harness]
  F --> C
{{< /mermaid >}}

### The Four Things I Manage First

The first thing is task boundaries.

Before a medium-sized task starts, I want at least `done when`, `out of scope`, the change surface, and the verification command. This does not need to be a long document. Five lines are often enough. The key is to let the executor know when to stop.

The second thing is context routing.

`AGENTS.md` should not become an encyclopedia. It works better as an index: what the project rules are, where the entry points are, what command verifies the change, what must not be touched, and where the next layer of docs lives. Long context should be read on demand instead of being dumped into the session.

The third thing is the verification loop.

My default order is now:

1. Read: read README, AGENTS, older notes, and key implementation files
2. Search: use `ace`, `rg`, `ast-grep`, `nmem`, and Exa to find evidence
3. Change: apply a small patch and avoid drive-by refactors
4. Verify: run narrow checks first, then expand by risk
5. Record: write repeated lessons back into rules, tests, or memory

This order looks ordinary, but it prevents many runaway cases. Reading and searching first reduce model guesswork. Narrow verification avoids a large change where nobody knows which step broke.

The fourth thing is failure handling.

After a failure, I classify it first: stop, retry, patch the harness, or record it.

| Type | When to Use It | Handling |
|:---|:---|:---|
| Stop | User rejection, permission block, side effect risk, repeated spinning | Break the loop and return control |
| Retry | Network jitter, fixable parameter, read failure without side effects | Retry in small steps and keep logs |
| Patch | Same class of error appears twice | Add tests, rules, scripts, or logs |
| Record | The case will likely happen again | Save trigger conditions, verification commands, and evidence entry points |

I used to treat many failures as “try again.” Now I am more careful. Retry only the failures that are actually retryable. Stop conditions must stop.

### Where External Research Fits

In this workflow, Exa or similar web search tools have a clearer role.

I usually do not search for broad trends. I search for concrete engineering questions:

- What timeout should be used?
- Should this failure be retried?
- How should the default strategy be split?
- What boundaries do mainstream tools provide?
- What failure samples show up in real issues?

I do not copy the external solution directly. External material gives me a reference frame, and the final decision still has to fit the current repo. Useful conclusions should land in specs, project rules, tests, or scripts. Otherwise I will have to search again next time.

### Autoresearch and Ralph Loop

Autoresearch works best for long loops with a clear metric. Give the agent a goal, a guard, and a verification command first. Each round should allow only one rollback-friendly change.

I currently treat Ralph Loop as persistent single-owner execution. The same owner keeps driving the work. PRD and test spec come first, then the agent runs the long task. The point is to preserve context, judgment, and verification clues during long-running work before bringing in more agents.

Both patterns share the same idea: define the track before letting the agent run. The track needs metrics, boundaries, verification, and keep/discard rules.

### Three Steps Worth Copying First

If this needs to move into a team workflow, I would not start with platform work. Three steps are enough to copy tomorrow:

1. Write `done when` and `out of scope` for every medium-sized task.
2. Ask the agent to list files, evidence, and the change surface before allowing edits.
3. After one failure, patch tests, rules, or scripts before letting the agent continue.

Once these three steps are in place, AI coding moves a bit from “it can produce output” toward “it can be shipped.” Autoresearch, Ralph Loop, team workers, and memory become much easier to reason about after that.
