---
title: "Why I Built RunSeal: Stop Letting Local Coding Agents Run Naked"
slug: "local-first-agent-execution-boundary-runseal"
date: "2026-09-26T19:00:00+08:00"
tags: ["Security", "AI Coding", "Architecture", "Sandbox", "Open Source"]
series: ["AI Coding Security"]
description: "Coding agents have long compromised between running naked on host systems and suffering from bloated Docker setups, facing structural risks of credential theft and uncontrolled egress; introducing RunSeal, an OS-native project conceived and shaped early on that enforces lightweight boundaries via workspace containment, managed proxies, and fail-closed architecture; delivering a millisecond-launch, cross-platform, non-intrusive safe execution boundary for local commands."
---

> I am not a native English speaker; this article was translated by AI.

Truth be told, [RunSeal](https://github.com/runseal-labs) took shape quite a long time ago.

The core execution logic and test suites had been working for a while, and I originally intended to write a quick blog post to document the design rationale. But real-world engineering work piled up, I got caught up running daily agent loops, and open-source preparations kept getting pushed to the back burner. Now that recent privacy leaks and boundary breaches have everyone talking about agent security again, it seems like the right time to lay out the full story: the background, the trade-offs we wrestled with, and how RunSeal actually works under the hood.

---

## Are We Really Comfortable Hitting Enter Every Day?

Coding agents have quietly become daily drivers for many of us. From early pioneers like Aider, Open Interpreter, and AutoGPT, to modern setups like Cursor, Claude Code, Devin, and Codex, we have all grown comfortable delegating terminal execution to AI: write code, run tests, execute scripts, install dependencies. It saves time and mental energy.

But once you spend an afternoon inspecting raw low-level execution logs, it is hard not to feel uneasy:

1. **It is literally just an unprivileged child process on your machine.** Whatever your terminal user can do, the agent can do. Reading and writing files in the current repository is expected. But if it casually reads `~/.ssh/id_rsa`, inspects `~/.aws/credentials`, or traverses directories to peek at neighboring proprietary codebases, the operating system will not raise a single eyebrow.
2. **That `[Y/n]` confirmation prompt is pure security theater.** Ask an agent to troubleshoot a complex bug, and a single turn can trigger dozens of shell commands. No human has the cognitive bandwidth to audit lines of shell code every five seconds. Within three iterations, interactive prompts inevitably degrade into rapid, mindless keystrokes of Enter ("approval fatigue"). When an injection attack strikes, you will be the one who approved it, and you will be the one holding the bag.
3. **Existing containment options are excruciatingly painful to use.**
   - Put it in Docker? Anyone who has tried bind-mounting local code on macOS knows how awful it feels: cross-VM filesystem I/O crawls like a snail, and `npm install` takes forever. Your carefully configured local Python virtual environments, compiler caches, and host utilities are locked outside. Worse, to let the agent fetch packages and docs, you must open outbound network access. An adversarial prompt injection can still exfiltrate credentials over the public Internet.
   - Rely on regex-based command blocklists? Blocking `rm -rf /` or `cat ~/.ssh` looks reassuring on slides, but anyone familiar with the terminal knows that simple `$IFS` tricks, string concatenation, Base64 decoding, or three lines of Python easily slip right past static regex matching.
   - Grab ad-hoc open-source scripts? Most are quick demos wrapping Linux `landlock` or `bwrap`. But many of us write code on macOS, and lots of enterprise teams run Windows. On non-Linux platforms, these tools simply throw up their hands and run unconfined. Furthermore, their network policies are strictly binary: either sever the connection completely (breaking dependency downloads) or leave it wide open (rendering the sandbox pointless).

We have been stuck in an awkward dilemma: **either run completely unconfined for agility, or endure a miserable developer experience for safety.**

---

## RunSeal's Scope: Keep It Lean and Tackle the Hard Problems

When I started writing RunSeal, I deliberately drew a strict line in `AGENTS.md`, which essentially boils down to:

> RunSeal is an OS-native, policy-governed local command execution environment—not an AI governance platform, not an enterprise-wide approval workflow, not a policy dashboard, and not a general automation framework.

I had no desire to build complex approval dashboards or SaaS control planes. The goal was singular: **lock the agent's reach strictly to the current workspace at the OS kernel level, without booting a VM and without sacrificing local execution speed.**

{{< mermaid >}}
flowchart TD
    A[Agent Requests Command Execution] --> B[RunSeal CLI / RPC]
    B --> C{Check Host Capability}
    C -->|Capability Mismatch| D[Fail-Closed Immediate Error<br/>Never Silently Degrade]
    C -->|Policy Validated| E[Construct OS-Native Sandbox]
    
    subgraph OS[OS Kernel Boundary]
        E --> F[Filesystem: Workspace-Contained<br/>Confined to Workspace + Ephemeral Root]
        E --> G[Network Guard: Managed Proxy<br/>Block Raw Egress & Unauthorized Loopback]
    end
    
    F & G --> H[Execute Command & Capture Exit Status]
    H --> I[Append Immutable JSONL Audit Log]
    I --> J[Return Results to Agent]
{{< /mermaid >}}

The architecture centers on four practical pillars:

### 1. Millisecond Native Launch Without Virtualization

RunSeal boots no virtual machines and runs no persistent background daemon. It invokes operating system primitives directly:
* **Windows Treated as a First-Class Citizen (Reference Backend)**: Most open-source security scripts avoid Windows entirely. RunSeal made Windows its reference implementation from day one, implemented via Restricted Tokens, Job Objects, and custom ACLs, mapping policies to execution plans through the unified `PlatformSandboxPlan` contract;
* **macOS / Linux Feature Alignment**: macOS leverages Seatbelt (`sandbox-exec`), while Linux combines Bubblewrap and Landlock. All three sandbox levels and three network modes execute natively, with managed proxy boundaries landed on both platforms (RFC-0019 / RFC-0020).

Because execution happens natively at the OS layer without virtualization overhead, launch latencies are sub-millisecond. Compiler caches, virtual environments, and local toolchains work seamlessly.

### 2. Workspace Containment

At the filesystem layer, RunSeal normalizes access into four sandbox levels: `read-only`, `workspace-write`, `workspace-contained`, plus an explicit opt-out via `danger-full-access`.

The core level is `workspace-contained`:
* The process can **only see the current workspace directory, a private ephemeral runtime root, explicitly declared read-only paths, and minimal system baseline utilities**;
* Everywhere else on the host (especially `~/.ssh`, `~/.aws`, `~/.config`, or neighboring repositories on disk) is either invisible or denied access;
* Even if an agent is tricked by a malicious injection into running `cat ~/.ssh/id_rsa` or attempting `cd ../../`, the operating system kernel immediately denies access (returning `Operation not permitted` in actual practice), cutting off reconnaissance at the kernel level.

### 3. `network.proxy`: Controlled Outbound Access

In everyday software engineering, completely severing an agent's network connection is impractical. Agents need to download packages, query documentation, and call APIs. But opening unrestricted outbound traffic defeats containment.

RunSeal introduces a dedicated `network.proxy` mode:
* Direct connections to external public IPs and domains are forbidden;
* Unauthorized local loopback and host IPC are blocked;
* **All outbound traffic is forcibly routed through a designated Managed Proxy endpoint**.

This architecture allows the proxy to enforce domain allowlists, redact leaked API credentials, and produce structured audit records. An agent cannot silently dial out to an external C2 server.

### 4. Fail-Closed Over Silent Degradation

In security engineering, the worst failure mode is pretending to be secure to keep a job running.

If a caller requests `workspace-contained` and `network.proxy`, but the host environment lacks the privileges or kernel support to guarantee that boundary, **RunSeal fails closed immediately, exiting with an explicit error rather than silently falling back to unconfined execution**.

We backed this with an adversarial black-box test harness (RFC-0016), evaluating symlink traversals, parent path escapes, environment pollution, and orphan process cleanup, verifying that every capability marked as `supported` is mechanically proven.

---

## How It Looks in Practice

RunSeal's CLI is kept deliberately minimal: just a handful of parameters, making it effortless to integrate into agent automation harnesses or frameworks.

### 1. Probe Host Capabilities

```bash
runseal capabilities
```

Outputs a JSON payload detailing what the current machine can strictly guarantee (excerpt; full output includes `features`, `capability_probes`, etc.):

```json
{
  "platform": "macos",
  "sandbox_levels": {
    "read-only": "supported",
    "workspace-write": "supported",
    "workspace-contained": "supported",
    "danger-full-access": "supported"
  },
  "network_modes": {
    "unmanaged": "supported",
    "disabled": "supported",
    "proxy": "supported"
  }
}
```

Protocol and policy versions are reported separately via `runseal version --json`.

### 2. Run a Confined Command

Confine a command to the current workspace with network disabled:

```bash
runseal exec \
  --policy workspace-contained \
  --network disabled \
  --cwd /Users/ferstar/myprojects/demo \
  -- python3 test_pipeline.py
```

If a command attempts to read outside the workspace, the kernel rejects the read directly. Under default mode, the terminal echoes no errors—the command is blocked silently—but passing `--json` exposes the full result (excerpt):

```bash
runseal exec --json \
  --policy workspace-contained \
  --network disabled \
  --cwd /Users/ferstar/myprojects/demo \
  -- cat ~/.ssh/id_rsa
```

```json
{
  "exit_code": 1,
  "stderr": "cat: /Users/ferstar/.ssh/id_rsa: Operation not permitted",
  "sandbox": {"enforced": true, "level": "workspace-contained"}
}
```

Note that the exit code of `runseal exec` itself is currently fixed at 0; the true exit status of the child process is reflected in the JSON result and audit logs. For automated pipelines, `--json` yields structured outputs, while `--events` streams newline-delimited lifecycle events.

### 3. Local Structured Auditing

Every invocation logs its policy parameters, Canonical Policy Hash, network decisions, and exit statuses to an immutable local JSONL audit trail (excerpt; each event also includes `execution_id`, `session_id`, `policy_epoch`, etc.):

```json
{"type":"policy.resolved","policy_id":"workspace-contained","policy_hash":"sha256:7cb64a73...","sandbox_level":"workspace-contained","network":{"mode":"disabled","routes":[]},"time":"2026-09-26T11:21:26.967279Z"}
{"type":"execution.finished","exit_code":1,"status":"finished","time":"2026-09-26T11:21:26.971042Z"}
```

---

## Final Thoughts

The recent ZCode snapshot upload incident simply thrust the long-standing risk of unconfined local agent execution into the public spotlight.

AI coding tools are evolving at breakneck speed. Models are getting sharper, and their autonomous execution loops are getting longer. But we cannot enjoy 5x code output while handing over the master keys to our machines on the assumption that vendors will always practice good hygiene or adhere to ambiguous privacy policies.

Day to day, we shouldn't have to treat our own machines like hostile territory, but we also shouldn't wait until our credentials are exposed before taking containment seriously.

Locking boundaries down at the OS kernel layer—allowing what should run and blocking what shouldn't—is the only way to let local agents do real work safely.

*(RunSeal's RFC specifications and implementation are open source. Feel free to explore and contribute: [github.com/runseal-labs](https://github.com/runseal-labs))*
