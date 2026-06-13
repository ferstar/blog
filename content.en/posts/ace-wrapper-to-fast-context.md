---
title: "ACE Broke, So I Rewrote It: From ace-wrapper to fast-context"
slug: "ace-wrapper-to-fast-context"
date: "2026-06-01T10:35:09+08:00"
tags: ['Idea', 'AI']
description: "After ace-wrapper was written, ACE free tier became unreliable and relay services died one by one; so I reverse-engineered Windsurf's SWE-grep protocol, added local Semble cache as fallback, and built a hybrid retrieval tool called fast-context."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

In the [last post](/en/posts/ace-wrapper-semantic-search-ai-coding-harness/) I wrote about `ace-wrapper`: a shell command around ACE (Augment Context Engine) filesystem context search, so the agent could start with semantic retrieval when keywords were fuzzy, then decide which files to read.

Then ACE got flaky.

API keys expired in new ways. Free-tier quota became harder to rely on. And one by one, the relay services died.

I do not really blame anyone. It was a preview feature to begin with. The problem was that semantic search had already become part of my daily workflow: dozens of `ace` calls in one session. Take it away and the agent is back to guessing keywords.

So I switched approaches:

[ferstar/fast-context](https://github.com/ferstar/fast-context)

This time I skipped third-party APIs and talked directly to Windsurf's SWE-grep protocol — the same semantic search backend used by Codex CLI and Windsurf IDE — while layering a local Semble cache on top as fallback.

### The structural difference from ace-wrapper

ace-wrapper was pure remote: local only sent parameters, everything depended on the ACE service.

fast-context is local and remote working together.

{{< mermaid >}}
flowchart TB
  subgraph Input
    Q[User query]
  end

  subgraph Local
    S[Semble local prefetch<br/>cached index + chunk search]
    A[Lexical anchors<br/>filename / path / literal hits]
    R["Repo map<br/>(auto-shrink when too large)"]
  end

  subgraph Remote
    WS[Windsurf SWE-grep<br/>agentic verify + expand]
  end

  subgraph Output
    O["Candidate files<br/>line ranges<br/>follow-up terms<br/>(or local chunks when remote fails)"]
  end

  Q --> S
  Q --> A
  Q --> R
  S --> WS
  A --> WS
  R --> WS
  WS -- success --> O
  WS -- auth / rate-limit / timeout --> O
  S -- fallback path --> O
{{< /mermaid >}}

The flow:

1. **Run Semble locally first** — cached index + chunk search, sub-second
2. **Collect local lexical anchors** — exact filename, path segment, and literal content matches from the query
3. **Generate a repo map** — directory tree, auto-shrunk when it gets too large
4. **Feed all three to Windsurf** — Semble chunks as hints, lexical anchors as pinpoints, repo map as path context
5. **Windsurf verifies and expands** using rg/readfile/tree/ls/glob — agentic tool-call loop
6. **When the remote path fails, return local Semble results** — no empty hands, no blocked workflow

That "no empty hands" property matters more than it sounds. With ace-wrapper and ACE, once the service went down, that search was simply gone. Now, when the remote path fails, local cache still returns chunk-level candidates. Lower quality, yes, but the workflow does not just die there.

### Reverse-engineering SWE-grep

Windsurf's SWE-grep uses Connect-RPC + Protobuf, which is nothing like a normal REST API.

The trickiest part was the Connect framing. Every RPC frame has a 5-byte header (1 flag byte + 4 big-endian length bytes). On top of that, the protocol requires a Connect-Connect frame before the actual payload.

The Protobuf side was worse. Windsurf uses a custom proto schema with no public definition. The field numbers in core data structures had to be inferred from packet captures and known Wireshark decryption configs — call chains look like `{1: name, 2: args, 3: id}`, variable definitions like `{1: name, 2: type, 3: value}`. Guess wrong and the whole request fails, with no useful error message.

The encoder looks like this ([ProtobufEncoder](https://github.com/ferstar/fast-context/blob/main/src/core.py#L64)):

```python
class ProtobufEncoder:
    """Manual protobuf encoder, matching the Windsurf wire format exactly."""
    def __init__(self) -> None:
        self.buf = bytearray()

    def _varint(self, value: int) -> bytes:
        parts: list[int] = []
        while value > 0x7F:
            parts.append((value & 0x7F) | 0x80)
            value >>= 7
        parts.append(value & 0x7F)
        return bytes(parts)

    def _tag(self, field: int, wire: int) -> bytes:
        return self._varint((field << 3) | wire)
```

Decoding Windsurf's streaming response is the same story — split frames, read payloads, find the stream-end marker, reconstruct the result. It is much more work than calling a REST API, but the upside is clear: no intermediary dependency, just a direct path to Windsurf's backend.

### Why local Semble cache works

Before adding Semble I did wonder: does local indexing really help?

Once I ran the benchmark, there was no suspense left.

I ran 40 labeled queries across two repos (fastapi and axios):

| Backend | NDCG@10 | Recall@10 | Top-1 | Batch p50 |
|:---|---:|---:|---:|---:|
| local (Semble only) | 0.854 | 0.946 | 0.775 | 30 ms |
| remote (Windsurf only) | 0.453 | 0.467 | 0.450 | 24.4 s |
| hybrid (Semble + Windsurf) | 0.890 | 0.979 | 0.825 | 28.3 s |

Local Semble alone hit 94.6% recall with 30 ms p50 latency. Windsurf alone underperformed — only a 52.5% success rate, with the rest lost to throttling or `resource_exhausted`.

Hybrid mode puts Windsurf after Semble for verification and expansion. NDCG@10 jumped to 0.890, recall to 97.9%.

Two things became clear:

- **Local cache is not a backup; it is the first line of defense.** It handles most common searches in 30 ms. When the remote is down, it is a degradation path, not a dead end.
- **Windsurf's value is in verification, not first-pass search.** Asking it to search from scratch risks timeout and throttling. Give it Semble chunk candidates and exact keyword anchors, and it only has to confirm — which succeeds far more often.

### Credential handling got more involved

ace-wrapper just needed an API key. fast-context uses Windsurf's session token, stored in `state.vscdb` (a SQLite database).

The extraction logic lives in [extract_key.py](https://github.com/ferstar/fast-context/blob/main/src/extract_key.py):

```
Query ItemTable for key='windsurf.api_key'
→ if found, return it
→ if not, search for rows key containing 'devin-session-token'
→ either format works
→ can also override with WINDSURF_API_KEY env var
```

Why support two formats? Because Windsurf keeps changing. Earlier versions used standard API keys; newer ones moved to session-style credentials like `devin-session-token$...`. If the tool does not adapt, it breaks as soon as the user upgrades their IDE.

### The current workflow

During the ace-wrapper era, my AGENTS.md looked like this:

```
Use ace for semantic retrieval → read files → confirm evidence with rg
```

Now it reads:

```
Use fast-context search (default hybrid) for candidates + line ranges
If hybrid times out or returns nothing, try fast-context local-search
If a chunk candidate looks promising, use fast-context find-related
After reading files, confirm exact evidence with rg/ast-grep
```

There are more branches now, but each one has a clear fallback.

On the remote side, there is a model fallback chain too:

1. Default: `MODEL_SWE_1_6_FAST`
2. On `resource_exhausted` or rate-limit: auto-degrade to `MODEL_SWE_1_5`
3. Custom fallback order via `WS_FALLBACK_MODELS`

### Benchmark results

With the fair runner (completion-based cooldown, 40 queries):

- **Hybrid non-empty output rate: 100%** — all 40 queries returned useful results
- **Remote non-empty output rate: only 50%** — the other half timed out or got throttled
- **Local zero failures** — 100% non-empty, p50 latency 30 ms

If the workflow depended purely on remote semantic search, half the queries could get no answer during peak hours. With local Semble backing, the worst case is degraded local chunks, not an empty result.

### What I do not want to tear down and rebuild again

A few design choices that held up well:

1. **Always keep a degradation path.** Every remote dependency needs a local fallback. I already paid for ignoring that once.
2. **Pure Python is easier to maintain.** ace-wrapper was Python too, but this project grew from a few hundred lines to more than two thousand — protobuf encoder, Connect framing, Semble adapter, benchmark runner. Clear structure matters more than language choice. Python just happens to be what I work fastest in.
3. **Benchmarks should live with the code.** The [benchmarks/](https://github.com/ferstar/fast-context/tree/main/benchmarks/) directory with 40 labeled queries and a runner shows the real gap between backends on every run. Optimization without data is mostly guessing.
4. **Credential extraction should auto-adapt.** The `devin-session-token` format was unexpected, but the code structure made it easy — try another pattern when the first key is not found, without touching the main flow.

### Wrapping up

I still use ace-wrapper sometimes — ACE does come back to life once in a while. But I no longer want my workflow tied to it.

The core idea behind fast-context is simple: let local cache carry the baseline, and use the remote path for verification and expansion. Once the upstream gets shaky, a purely remote solution turns into a rope with no backup.

If you have hit the same wall, the code is here: [ferstar/fast-context](https://github.com/ferstar/fast-context)
