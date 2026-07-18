---
title: "Giving My Codex Workflow a Rear-View Mirror: Harness Governance and Observability"
slug: "codex-harness-observability-loop"
date: "2026-07-18T20:00:00+08:00"
tags: ['Idea', 'AI']
description: "A growing library of personal Codex skills made workflow quality hard to judge; govern skill boundaries with an authority state machine, use native session JSONL as the sole source of truth, and close the loop with scheduled AI audits and evals."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

A month ago, I wrote [Growing a Codex Workflow as a Living System: From Session Logs to Skills](/posts/codex-workflow-skills-feedback-loop/). The conclusion was simple: find recurring friction in real sessions, capture it as a small skill first, and write a script only after the action has proved mechanical.

That worked. But as the skill library grew, it introduced a new layer of complexity.

One task could trigger `agent-preflight`, `path-verify`, `gitlab-mr-context`, and `codex-ship-loop` together. After an MR was merged, there was no consistent meaning for whether its issue should close, stay open, or move to `to test`. When a long thread was handed off, the agent would re-check context that had already been established. Worse, I knew these problems existed but could not tell how often they happened or whether a change actually improved anything.

So this time I did not add another skill. I went back and governed the Harness itself.

## Audit the workflow, not the code

I sampled roughly 127 top-level Codex threads from June 18 to July 18, 2026. Multiple subagents independently reviewed project activity, workflow friction, skill routing, `AGENTS.md` rules, and thread lifecycles.

The main problem was not missing capability. It was governance debt in four forms:

1. **Skill stacking**: several skills performed repository preflight, GitLab context retrieval, or verification routing, leaving no clear workflow owner.
2. **Public and private boundaries were mixed**: reusable public methods contained company GitLab names, internal release flows, local SSH aliases, and absolute paths.
3. **Long threads lacked checkpoints**: handoffs replayed conversations because stable facts and drift-prone facts were not separated.
4. **Delivery had no terminal-state model**: commit, push, merge, deploy, issue state, and cleanup were joined into an implicit authority chain by vague words such as “continue” or “finish it.”

Another “manager skill” would not fix these problems. It would only become one more stacking entry point.

## Removing overlapping responsibility is harder than adding capability

I removed two redundant skills in this pass.

The useful parts of `gitlab-mr-context` moved into the `glab` references. Reading MRs, issues, pipelines, and discussions belongs to the GitLab CLI skill; it did not need a competing trigger.

I removed `path-verify` as well. Its useful principle—run the narrowest owning-module check for the changed scope—belongs in general verification guidance. Concrete commands belong in each project's `AGENTS.md` or README. Keeping it as a separate skill only added another routing layer to every implementation task.

The remaining workflow skills now have sharper boundaries:

- `agent-preflight` establishes repository, branch, dirty-state, and live-object facts at the start;
- `ci-first-failure` handles already-red CI and identifies the first actionable failure;
- `codex-ship-loop` advances already-scoped and verified changes into separately authorized delivery states;
- `release-deploy-preflight` resolves release and deployment targets, inputs, exact SHAs, and live verification;
- `artifact-verify` proves the contents, integrity, and provenance of an existing artifact without building or publishing it;
- `remote-health` diagnoses SSH, networking, PATH, services, and remote runtime conditions.

The important result is not two fewer directories. Trigger conditions are becoming mutually exclusive. Skill quality depends not only on activating when needed, but also on staying out of work it does not own.

## Turn natural-language authority into explicit state

Daily prompts should not become forms. I still prefer saying:

```text
看下这个 MR 还有什么问题。
```

Internally, however, the Harness should infer a minimal task contract from that short prompt:

```text
objective + evidence + scope + authority + terminal_state
```

The easiest fields to miss are `authority` and `terminal_state`.

“Review the MR” grants read-only access, not permission to edit code. “Push it” does not mean merge. Merge does not imply deploy, issue closure, or branch deletion. I now treat these actions as independent authorities:

```text
read-only | edit | push | merge | deploy | workflow-state | publish | cleanup
```

Long tasks move through a state machine whose stages may be skipped when irrelevant, but whose terminal state cannot be silently changed:

```text
DISCOVER -> DECIDE -> IMPLEMENT -> VERIFY -> SHIP -> DONE
```

{{< mermaid >}}
stateDiagram-v2
  [*] --> DISCOVER
  DISCOVER --> DECIDE
  DECIDE --> IMPLEMENT
  IMPLEMENT --> VERIFY
  VERIFY --> SHIP: separately authorized
  VERIFY --> DONE: no shipping requested
  SHIP --> DONE: final objects verified
  SHIP --> VERIFY: remote state drifted
{{< /mermaid >}}

`DONE` no longer means that a command finished. It means the requested terminal state has been read back and verified. For a deployment, a successful workflow is only intermediate evidence; the deployed SHA and live health still need verification. A merge must not close an issue as a side effect—if the requirement says “keep it open and move it to testing,” that is the terminal state.

I also added a shared checkpoint contract to `agent-preflight` and `codex-ship-loop` for long threads. Stable evidence is reused, while branch heads, dirty state, CI, mergeability, permissions, workflow inputs, deployment health, and remote SHAs are refreshed because they can drift. Resuming work no longer means repeating the entire investigation.

## I initially chose the wrong observation point

Once the governance rules existed, the next question was obvious: how could I tell whether they worked?

My first attempt used Codex hooks. Every turn start and completion wrote an event to `events.jsonl`, and reports were generated from that event stream. It looked like normal observability: events, a schema, a collector, and a completion rate.

Real use exposed three problems quickly.

First, the events were too thin. `turn_started` and `turn_completed` show that a flow ran, but not that the result was correct, that the right skill was used, or that an issue ended in the requested state. Semantic judgment still required the original session.

Second, the hooks created a second source of truth. Native Codex session JSONL already records lifecycle, tokens, tool calls, models, and permission policy. Copying part of that into a lower-fidelity event stream introduced path, migration, and consistency problems.

Third, a hook sits on the critical path of every interaction. After one script refactor, the old hook still pointed to a deleted `codex_hook.py`, so every task stop produced an error. The observation system had begun polluting the system it was supposed to observe.

That failure taught me something useful: not every form of “automatic collection” belongs in hooks. The critical path is appropriate only for information that must be intercepted at event time and does not already exist in native data. Offline quality auditing is not such a case.

## Native JSONL as the sole source of truth

The final design became much smaller: remove the hooks and custom event database, and read `$CODEX_HOME/sessions/**/*.jsonl` directly.

{{< mermaid >}}
flowchart TD
  A[Native Codex session JSONL<br/>single source of truth] --> B[Deterministic scanner]
  B --> C[Content-free metrics<br/>completion / latency / tokens / tools]
  C --> D[Scheduled AI audit]
  D -->|no signal| E[Short health report]
  D -->|repeated high-signal anomaly| F[Minimal source-session review]
  F --> G[Sanitized eval candidate]
  G --> H[Baseline]
  H --> I[Harness change]
  I --> J[Regression trials]
{{< /mermaid >}}

The first layer is a deterministic scanner. It emits content-free aggregates: completion rate, median/P95 duration and time to first token, input/output tokens, tool calls per turn, tool/model/permission-policy distributions, and opaque session/turn references for incomplete work. Prompts, responses, commands, paths, URLs, tool arguments, and tool results never enter the derived report.

The second layer is a scheduled AI audit. It does not summarize every session again. It minimally inspects source sessions only when there is a high-signal condition such as persistent incompletion, a meaningful latency or cost regression, or a recurring workflow failure. With no actionable signal, it sends only a short health result.

There is deliberately no “automatically edit the skill” step. Observation can recommend one of five dispositions: keep observing, promote to an eval, change a skill, change deterministic tooling, or fix instrumentation. Edit, commit, push, merge, deploy, and publish still require independent authority. Autonomous improvement should not mean autonomous privilege expansion.

## Metrics are not conclusions; evals justify changes

A completion rate rising from 90% to 95% does not prove that the Harness became smarter. The recent tasks may simply have been easier. Fewer tool calls may mean greater efficiency, or it may mean that the agent skipped necessary verification.

I therefore use metrics as a filter, not a judge. What should drive a Harness change is a sanitized, reproducible eval distilled from repeated failures.

The current cases include:

- review-only work must not edit anything;
- a push request must stop before merge;
- after merge, an issue may need to remain open in `to test`;
- deployment must bind to an exact SHA and verify live provenance and health;
- red CI must be reduced to its first actionable failure;
- skill installation links must point from install to source;
- artifact verification must inspect contents, not merely report a successful download.

These evals test both positive triggers and negative routing. A normal README typo should not activate `harness-observe`, and application OpenTelemetry is not the responsibility of a personal Codex Harness.

My improvement loop now looks like this:

```text
real sessions -> aggregate signals -> minimal semantic review -> sanitized eval
              -> baseline -> Harness change -> regression -> observe again
```

## Where the system stands now

This is not a “self-evolving agent platform” that automatically rewrites its own prompts. I think stopping short of that is the right choice.

The current system delivers three more practical properties:

1. **Workflow boundaries**: more skills are not automatically better, and public methods, project facts, and private machine configuration each have a proper home.
2. **Terminal delivery states**: MRs, merges, deployments, issues, and cleanup are no longer connected by vague verbs.
3. **Evidence-based improvement**: native sessions provide facts, metrics surface anomalies, AI performs bounded semantic review, and evals verify changes.

The next step is not collecting more data. It is building comparable baselines over time, strengthening deterministic graders for high-risk flows, and measuring which skills actually reduce rework and authority mistakes.

The complete implementation is public in [ferstar/my-agent-skills](https://github.com/ferstar/my-agent-skills). The previous article covered how recurring experience becomes a skill. This one covers the second half: **once the skill library grows, how to keep it from becoming another form of technical debt—and how to know whether the workflow is actually improving.**
