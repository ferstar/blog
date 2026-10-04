---
title: "Why I Built RunSeal: Setting an Execution Boundary for Local Coding Agents"
slug: "local-first-agent-execution-boundary-runseal"
date: "2026-09-26T19:00:00+08:00"
tags: ["Security", "AI Coding", "Architecture", "Sandbox", "Open Source"]
series: ["AI Coding Security"]
description: "Coding agents have long compromised between running naked on host systems and suffering from bloated Docker setups, facing structural risks of credential theft and uncontrolled egress; introducing RunSeal, an OS-native project conceived and shaped early on that enforces lightweight boundaries via workspace containment, managed proxies, and fail-closed architecture; delivering a millisecond-launch, cross-platform, non-intrusive safe execution boundary for local commands."
---

> I am not a native English speaker; this article was translated by AI.

[RunSeal](https://github.com/runseal-labs) took shape quite a long time ago.

The core execution logic and test suites had been working for a while, and I originally intended to write a quick note on it. But daily engineering work kept piling up, and open-source preparations stayed on the back burner. Now that boundary escapes and privacy risks have brought agent security back into focus, it is a good time to walk through the background, design trade-offs, and technical implementation.

---

## The Trust Deficit in Local Command Execution

Coding agents have become daily drivers for many developers. From early tools like Aider and Open Interpreter to systems like Cursor, Claude Code, Devin, and Codex, running commands via AI has become routine: editing code, running test suites, executing build scripts, and installing dependencies.

Looking at raw execution logs, however, several concerns become apparent:

1. **The agent runs as a standard child process on your machine.** Whatever permissions your terminal holds, the agent inherits. Reading and writing within the project is expected; reading `~/.ssh/id_rsa`, scanning `~/.aws/credentials`, or inspecting neighboring codebases happens with zero kernel-level intervention.
2. **Interactive `[Y/n]` confirmations degrade quickly.** Complex debugging sessions often trigger dozens of commands per turn. Sustaining close review of every command every few seconds is unrealistic. After a few iterations, confirmation prompts turn into routine keystrokes of Enter.
3. **Existing containment options introduce significant friction.**
   - Docker containers: On macOS, bind mounts across VM boundaries introduce high I/O latency, making operations like `npm install` sluggish. Local virtual environments, compiler caches, and host utilities cannot be reused directly. Granting outbound network access to fetch packages means exfiltration paths remain open under adversarial prompt injection.
   - Regex command filters: Pattern-matching against strings like `rm -rf /` or `cat ~/.ssh` is fragile against simple string manipulation, Base64 decoding, or small wrapper scripts.
   - Minimal scripts: Many implementations focus solely on Linux primitives like `bwrap` or `landlock`, offering no equivalent on macOS or Windows. Network controls are often all-or-nothing: either disconnected entirely or left completely unrestricted.

Development often ends up caught between running unconfined for agility or accepting significant friction for security.

---

## RunSeal's Design Scope

When starting RunSeal, the operational boundary in `AGENTS.md` was explicitly defined:

> RunSeal is an OS-native, policy-governed local command execution environment—focused strictly on local command containment, without enterprise approval dashboards or general automation frameworks.

The objective is specific: confine command execution to the designated workspace at the OS kernel layer, without virtual machines or sacrificing local execution performance.

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

The implementation focuses on four main areas:

### 1. Millisecond Native Launch Without Virtualization

RunSeal starts no virtual machines and runs no background daemon, calling OS isolation primitives directly:
* **Windows Reference Implementation**: Implemented via Restricted Tokens, Job Objects, and specific ACLs, with policies mapped to execution plans through the `PlatformSandboxPlan` contract;
* **macOS and Linux Alignment**: macOS utilizes Seatbelt (`sandbox-exec`), while Linux combines Bubblewrap and Landlock. All three sandbox levels and network modes run natively, with managed proxy boundaries implemented across both platforms (RFC-0019 / RFC-0020).

Because execution is native, launch latencies remain sub-millisecond, preserving compiler caches and local toolchains.

### 2. Workspace Containment

Filesystem access is classified into four sandbox tiers: `read-only`, `workspace-write`, `workspace-contained`, and an explicit `danger-full-access` opt-out.

At `workspace-contained`:
* The process can only access the current workspace directory, an ephemeral runtime root, explicitly declared read-only paths, and minimal OS runtime baselines;
* Remaining filesystem locations (such as `~/.ssh`, `~/.aws`, `~/.config`, or neighboring directories) are either invisible or denied access;
* If prompt injection triggers access to `cat ~/.ssh/id_rsa` or path traversal, the kernel returns `Operation not permitted`.

### 3. Controlled Outbound Access (`network.proxy`)

Completely disabling network access prevents downloading packages or fetching documentation. Unrestricted outbound access, however, leaves egress unmonitored.

RunSeal's `network.proxy` mode:
* Restricts direct connections to external IP addresses or domains;
* Blocks unauthorized local loopback and host IPC;
* Directs outbound traffic through a designated Managed Proxy endpoint.

This allows the proxy layer to handle domain allowlists, credential redaction, and structured auditing.

### 4. Fail-Closed over Silent Degradation

If execution requests `workspace-contained` and `network.proxy`, but the host lacks sufficient permissions or kernel support, **RunSeal exits immediately with a Fail-Closed error rather than silently degrading to an unconfined state**.

Black-box test suites (RFC-0016) evaluate symlink traversal, directory escape, environment pollution, and process cleanup to ensure declared capabilities match actual system guarantees.

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
