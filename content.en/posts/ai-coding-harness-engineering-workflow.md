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

For a while I kept looking at one question: can AI really take over most of the coding work?

The answer is mostly settled now. When the project context, quality gates, and verification flow are in place, AI-generated code can enter the engineering workflow reliably. Human time moves from “typing the code” to “holding the line”: breaking down requirements, judging architecture, arranging context, checking boundaries, and handling failures.

Recent practice pushed this one step further. The question is no longer how to make the prompt prettier. It is whether the whole workflow can survive long-running tasks. I have stepped on this rake a few times, especially when I open the laptop in the morning, see that the agent ran all night, and still cannot tell which diff should be kept.

### What changed

Early Vibe Coding solved the entry problem: describe the requirement clearly, put project rules into `AGENTS.md` / `CLAUDE.md`, and let tests, lint, and review catch the model output.

That setup is still useful, but it is closer to single-task engineering. Once a task gets longer, a few problems start showing up:

- Context keeps growing until the model loses the important part
- Repeated retries can push the fix further away from the real issue
- Without external references, strategy becomes guesswork
- After many rounds, it is hard to tell which changes should be kept
- User rejection, permission blocks, and empty output need explicit stop semantics

So I now prefer calling this layer Harness Engineering: put an engineering track around AI so tasks are executable, results are verifiable, and failures are recoverable. The name sounds a bit grand. In practice, it just means trusting “it will figure it out” a little less and adding a few guardrails.

{{< mermaid >}}
flowchart LR
  A[Task scope] --> B[Context route]
  B --> C[Agent loop]
  C --> D[Verification gate]
  D --> E[Recovery / memory]
  D -->|failed| F[Patch harness]
  F --> C
{{< /mermaid >}}

### The four things I manage first

The first thing is task boundaries.

Before a medium-sized task starts, I want at least `done when`, `out of scope`, the change surface, and the verification command. This does not need to be a long document. Five lines are often enough. The point is to let the executor know when to stop, instead of drifting into “while I am here” changes.

The second thing is context routing.

`AGENTS.md` should not become an encyclopedia. It works better as an index: project rules, entry points, verification commands, things that must not be touched, and where to read the next layer of docs. Long context should be opened on demand, not dumped into the session. When the context gets too full, the model behaves a bit like me with too many browser tabs open: it looks busy, but the focus is gone.

The third thing is the verification loop.

My default order is now:

1. Read: read README, AGENTS, older notes, and key implementation files
2. Search: use `ace`, `rg`, `ast-grep`, `nmem`, and Exa to find evidence
3. Change: apply a small patch and avoid drive-by refactors
4. Verify: run narrow checks first, then expand by risk
5. Record: write repeated lessons back into rules, tests, or memory

This order is boring in a good way. Reading and searching first reduce model guesswork. Narrow verification avoids one giant change where nobody knows which step broke.

The fourth thing is failure handling.

After a failure, I classify it first: stop, retry, patch the harness, or record it.

| Type | When to use it | Handling |
|:---|:---|:---|
| Stop | User rejection, permission block, side effect risk, repeated spinning | Break the loop and return control |
| Retry | Network jitter, fixable parameter, read failure without side effects | Retry in small steps and keep logs |
| Patch | Same class of error appears twice | Add tests, rules, scripts, or logs |
| Record | The case will likely happen again | Save trigger conditions, verification commands, and evidence entry points |

I used to treat many failures as “try again.” Now I am more careful: only retry failures that are actually retryable, and stop when the situation says stop. Letting an agent push forward from a wrong premise usually just creates more diff for a human to clean up.

### Where external research fits

In this workflow, Exa or similar web search tools also have a clearer place.

I usually do not search for broad trends. I search for concrete engineering questions:

- What timeout should be used?
- Should this failure be retried?
- How should the default strategy be split?
- What boundaries do mainstream tools provide?
- What failure samples show up in real issues?

I still do not copy external answers directly. External material gives me a reference frame, and the final decision has to fit the current repo. Useful conclusions should land in specs, project rules, tests, or scripts. Otherwise I will search for the same thing again next time, which is a very small but reliable way to waste time.

### Autoresearch and Ralph Loop

Autoresearch works best for long loops with a clear metric. Give the agent a goal, a guard, and a verification command first. Each round should allow only one rollback-friendly change. If it drifts, the damage is still contained.

I currently treat Ralph Loop as persistent single-owner execution. The same owner keeps driving the work. PRD and test spec come first, then the agent runs the long task. It cares more about preserving context, judgment, and verification clues than about adding more agents early. Fewer people in the loop can sometimes make ownership much clearer.

Both patterns share the same idea: define the track before letting the agent run. The track needs metrics, boundaries, verification, and rules for what to keep or discard.

### Three steps worth copying first

If this needs to move into a team workflow, I would not start with platform work. Three steps are enough to copy tomorrow:

1. Write `done when` and `out of scope` for every medium-sized task
2. Ask the agent to list files, evidence, and the change surface before allowing edits
3. After one failure, patch tests, rules, or scripts before letting the agent continue

Once these three steps are in place, AI coding moves a bit from “it can produce output” toward “it can be shipped.” Autoresearch, Ralph Loop, team workers, and memory become easier to reason about after that.
