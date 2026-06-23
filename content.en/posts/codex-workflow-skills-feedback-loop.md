---
title: "Growing a Codex Workflow as a Living System: From Session Logs to Skills"
slug: "codex-workflow-skills-feedback-loop"
date: "2026-06-22T12:00:00+08:00"
tags: ['Idea', 'AI']
description: "Long-term Codex usage accumulates repeated debugging and delivery chores; scan local sessions, identify recurring friction, then turn it into skills, scripts, and cross-machine sync; make the workflow lighter over time."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

A few days ago I did something boring but useful: scanned the Codex sessions in `~/.codex`.

Not for nostalgia, not for a dashboard. I just wanted to see where I was wasting time on repeat.

No surprise. The expensive part was rarely one hard code change. It was the small glue work I had to do every single day:

- `git status`, `git diff`, `glab api`, `glab mr`
- finding the first failed CI job
- checking remote SSH, PATH, Tailscale, permissions
- deciding which tests to run for a given change
- confirming SHA, workflow, artifact before release or deploy
- resuming a session and re-sorting the issue, branch, MR

These things are too small. Small enough that you never bother to fix them. But because they are small, they keep getting ignored. In the end, you spend your day swimming in manual glue.

The original prompt was short:

```text
Based on my recent Codex projects and threads, suggest ways to simplify project workflows and improve efficiency. Use subagents to analyze in parallel.
```

The first result was still too biased toward a few recent projects, so I added one more instruction:

```text
Not just these projects. Scan all possible sessions under ~/.codex, dispatch multiple subagents to analyze them separately, then summarize.
```

The point was not “ask the model for optimization ideas.” It was changing the source of truth from my memory of recent work to the repeated actions inside real session logs.

### Do not write tools too early

I used to do this too — see repetition, reach for a script. Later I realized that is often too early.

Most repetition is not about repeated commands. It is about a repeated decision process. When CI fails, the reusable part is not some random `gh run view`. It is:

1. confirm the run and head SHA
2. find the first failed job
3. extract the useful error
4. then figure out: workflow, dependency, test, or code

Turning this straight into a big tool welds your wrong assumptions in place. The lighter move is to write a skill first: when to use it, minimum steps, what not to do, what to output.

A skill is not an encyclopedia. It is a sticky note — so the agent skips one dead end.

{{< mermaid >}}
flowchart LR
  A[Session history] --> B[Repeated friction]
  B --> C[Small skill]
  C --> D[Run on real tasks]
  D --> E[Script only when repeated]
  E --> C
{{< /mermaid >}}

I ended up keeping only these:

- `agent-preflight`: read the real repo state before starting, no assumptions
- `gitlab-mr-context`: use `glab api` for issues, MRs, pipelines, notes — much more reliable
- `ci-first-failure`: find the first real failure before touching code
- `path-verify`: pick the smallest check from the changed files
- `release-deploy-preflight`: confirm full SHA, workflow, artifact, health check before deploy
- `remote-health`: check SSH, PATH, services, locks, and Tailscale on remote hosts first

The names are not cool. That is exactly why you know when to use them.

### Skills first, scripts later

Another lesson: do not give every skill a scripts directory on day one.

Most workflows only need a `SKILL.md`. `path-verify` is not there to run your tests. It reminds the agent to pick the smallest check based on what files changed. Let it run with the agent on a few real tasks first. Automate later, once the pattern is confirmed.

Scripts are for one kind of thing: stuff that is definitely repeated, mechanical, and low risk.

This time I only added one — linking repo skills into the user skill directory:

```bash
scripts/link-user-skills.sh
```

And a PowerShell version for Windows:

```powershell
.\scripts\link-user-skills.ps1
```

I tripped on one thing: symlink direction.

The correct direction is: real files in the repo, links in the user directory.

```text
~/.agents/skills/glab -> /path/to/repo/skills/glab
```

That way the repo has real content, and local Codex can use it. Get it backwards and it is a mess — the repo only has a link to `~/.agents`, GitHub gets nothing, and Git thinks the original files were deleted.

### Make it work across machines

I switch between macOS, Windows, and remote hosts constantly. If a skill only works on one machine, its value gets cut in half.

So after the local setup, I synced the repo to `my-win` and ran the same maintenance flow on Windows. The PowerShell script uses directory junctions, not symlinks — creating symlinks on Windows often fights with permissions, and junctions are enough for directories.

Tedious step. But without it, workflow refinement turns back into a one-machine trick.

### How I think about it now

After this round, a few thoughts hardened.

Find repetition in sessions, not in your imagination. If `git status`, `glab api`, `ssh`, and `pnpm test` are actually frequent, start there. Do not invent a workflow governance framework nobody asked for.

Keep skills short. One blocks one gap. The only job is to make the agent ask less, search less, guess less. Do not turn it into an encyclopedia.

Scripts do mechanical work — linking skills, collecting CI logs, checking remote health. Product judgment, risk boundaries, deployment decisions still need human confirmation, or at least explicit preflight.

Mistakes need to feed back. I got the symlink direction wrong at first. After fixing it, the lesson cannot just stay in the chat window. It goes into the script and the README. Otherwise I will step on the same rake again.

### What remained

Not much:

- a few short skills
- one Bash linking script
- one PowerShell linking script
- one Windows sync check
- one rule: real skills in the repo, links in the user directory

Good enough.

The more I use AI coding, the more I think the workflow is not about building a big platform. It is about removing the most annoying five minutes, over and over. Each pass makes the system a little lighter. When enough of these small rules pile up, the agent starts working in a real engineering environment — not opening a new trail from scratch every time.
