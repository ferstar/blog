---
title: "Dual DGX Sparks for Agent Workloads: Great Benchmarks, Crawling Reality"
slug: "dgx-spark-agent-inference"
date: "2026-09-27T08:25:00+08:00"
tags: ["dgx-spark","llm","inference","agent"]
description: "Benchmarking MiMo-V2.6-Flash on two DGX Sparks hits 173 tok/s aggregate with 6 concurrent short prompts. But throw 5 sub-agents at a real codebase, and single-stream speed plummets to 15–25 tok/s, taking over 6 minutes without completing a single task."
---

> I am not a native English speaker; this article was translated by AI.

Social media and YouTube are flooded with dual DGX Spark (GB10) benchmark videos, each title more hyped than the last: "170+ Tokens/sec!" and "Datacenter AI on Your Desk."

A few days ago, I wired up two DGX Sparks directly using QSFP copper DAC cables, grabbed the community recipe, and spun up `MiMo-V2.6-Flash` with Tensor Parallelism (TP=2). But I didn't set this up to benchmark `Hello World`. I only had one practical question: **Can this thing actually plug into my daily coding agent as the primary model?**

The short answer: **It’s totally fine for single-user turn-by-turn chat. But if you expect to run concurrent sub-agents or scan large codebases, forget it.**

---

{{< alert >}}
**2026-10 Update**: If you happen to have an RTX 4090 and plenty of system RAM (like 128 GB), take a look at the alternative: [running Qwen3.8-Flash-Next with Strata]({{< relref "qwen38-flash-next-strata-4090.md" >}}). It keeps most experts in system memory and hot caches in 4090 VRAM. Under the same real-world code scanning workloads, median decode breaks right past 100 tok/s with cold prefill near 2800 tok/s.

Brace for impact.
{{< /alert >}}

---

## 200G Ports and Memory Bandwidth

When people see two 200G ports on each machine, their immediate assumption is often that dual-rail aggregation reaches 400G and inter-node communication won't be a bottleneck.

Run `ethtool` and `lspci` once and the actual layout is clear:

1. **The physical inter-node bandwidth ceiling is ~200 Gb/s**: The two machines connect directly via dual QSFP DAC cables—no switch, and no inter-node NVLink. While `ethtool` reports `200000Mb/s` on both ports, the ConnectX-7 behind each port is only wired to PCIe Gen5 x4 (`32GT/s, Width x4`). The unidirectional theoretical max is only about 126 Gb/s:
   
   `32 × 4 × (128/130) ÷ 8 ≈ 15.8 GB/s ≈ 126 Gb/s`

   With `ib_write_bw`, a single cable saturates at ~99.7 Gb/s, and dual rails run at 97.9 + 97.9 ≈ 196 Gb/s aggregate.
2. **Memory bandwidth is the bottleneck**: DGX Spark uses unified memory with 128 GB LPDDR5X per node, delivering 273 GB/s of bandwidth.
   Compare that against mainstream hardware:
   - RTX 4090: 1008 GB/s (24 GB VRAM)
   - Mac Studio M4 Max: 410–546 GB/s
   - Mac Studio M3 Ultra: 819 GB/s

DGX Spark’s strength is large unified memory capacity, which lets you shard an oversized model across two nodes via TP=2. But decode speed remains limited by the 273 GB/s memory bandwidth.

---

## Short Prompt Benchmarks

Running standard benchmark scripts with fixed 128-token short prompts and `ignore_eos` enabled:

| Concurrency | Aggregate Throughput (tok/s) | Latency & Per-Stream Decode |
| :--- | :---: | :--- |
| **1** | 37.1 | Single-stream decode ~43.8 tok/s |
| **2** | 73.6 | Linear scaling |
| **4** | 127.4 | Decent multi-stream scaling |
| **6** | 172.7 | Peak aggregate throughput, batch finished in 4.5s |
| **8** | 79.8 | Wall time 12.8s, per-stream decode scattered from 10 to 47 tok/s |

Six-way concurrency hits peak aggregate throughput. At eight streams the aggregate throughput drops, and per-stream rates scatter, though no scheduler error was reported. Idle single-stream decode touches about 54 tok/s. Normal pair-programming chat, with prefix-cache hits around 90%, stays around 35–45 tok/s.

Many online reviews measure these idle, short requests of a few hundred bytes, where each stream decodes independently without contention.

---

## Real Workloads: 5 Sub-Agents Scanning a Codebase

Next, I hooked the setup into my daily Coding Agent environment and spawned 5 sub-agents to concurrently explore a medium-sized open-source repo.

The backend monitoring looked completely healthy: HTTP 200 everywhere, queue depth zero.

Then checking actual progress in the terminal: single-stream generation dropped to 15–25 tok/s. After 6 full minutes, not a single sub-agent summary had finished streaming.

What that session recorded: HTTP 200, queue depth 0, 15–25 tok/s per stream, and no final answer after six minutes. A separate two-stream decode ran at about 65–75 tok/s aggregate, about 30–37 each. The benchmark peak was under 128-token prompts with `ignore_eos`, which is a different workload from real agent tasks.

Long prefill was observed in a separate run. A prefill of about 250K tokens can take minutes by itself, pulling down generation speed within that window. That specific run did not log input length or prefix hit rate per stream. In single-user chat, the ~90% hit rate comes from repeated system prompts; when sub-agents read different files, prefix hit rates drop significantly.

---

## Community Two-Node Benchmarks

Published GLM-5.3-Flash NVFP4 on two Sparks runs around 20–30 tok/s on a single stream, and around 36 on four. Raising the GPU clock from 1500 MHz to 2100 MHz adds about 4% decode (from the three-node post, distinct from the four-node 35.7 result). The post titled 43.4 reports a median of 21.8 in the body. Numbers in the sixties come from lower-bit EXL3 with structured output and short context. DeepSeek V4.1 Flash full weights are served in four-node setups; a two-node EXL3 directory exists and is marked unbenchmarked. Links are at the end.

---

## Considering Modded GPUs

Whether buying a modded GPU is worthwhile requires looking at the total platform cost:

- Modded RTX 4090 (48G): 1008 GB/s on one card, more than three times Spark's bandwidth. But a single card needs a motherboard, CPU, high-capacity RAM, a kilowatt PSU, and chassis cooling; DDR5 prices in 2026 are not trivial. If you already own an enthusiast desktop, the added cost is much lower.
- Modded RTX 5090 (96G): Suqiao's Alibaba listing was $3,888 for the bare card. Reports noted the product page listed GDDR6X at 14Gbps, which does not match 96GB, and the initial batch lacked independent teardown validation. [cnBeta](https://www.cnbeta.com.tw/articles/tech/1577618.htm), [Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/china-modified-nvidia-rtx-5090-with-massive-96gb-of-memory-appears-on-alibaba-for-less-than-usd4-000-3x-more-vram-at-65-percent-the-cost-of-the-original)
- Two Sparks: Turnkey systems. NVIDIA rates the system PSU at 240W and GB10 TDP at 140W with manufacturer warranty; 128 GB memory is included in the unit price.

The bandwidth difference is in the hardware specs. Total outlay depends on whether you build or buy turnkey, so no absolute cost judgment is made here.

---

## Practical Use Cases

With two DGX Sparks on hand, reasonable use cases look like:

- Suitable: Single-user interactive coding, turn by turn. With stable system prompts and high prefix-cache hit rates, 35–45 tok/s is usable, keeping data strictly local without relying on cloud APIs.
- Unsuitable: Backend for concurrent multi-agent swarms, repository-wide audits, or heavy concurrent tasks. LPDDR5X memory bandwidth and long-context prefill latency quickly become the primary bottleneck.

Adding more nodes solves fitting the model into memory, but does not alter the fact that single-stream decode is bound by memory bandwidth. Under real multi-agent workloads, the physical bandwidth remains the ceiling.

## Sources

Numbers from these two machines stay separate from numbers copied out of other people's posts.

**Measured here in September 2026. No public log.** MiMo used [tonyd2wild's two-node recipe](https://github.com/tonyd2wild/MiMo-V2.6-Flash-DGX-Spark-Recipe), TP=2, model id `mimo-v2.6-flash`, `max_model_len` 300,000, `max_num_seqs` 8, served on port `:8888` of the head node. The short-prompt table is 128-token generations with `ignore_eos`, sent from my own machine. The five-sub-agent run is a real session on that same server: nothing queued, about 15–25 tok/s per stream, and no final answer after six minutes. `ethtool` reported `200000Mb/s`, Direct Attach Copper, on both live ports. `lspci` showed PCIe Gen5 x4 (`32GT/s, Width x4`) on both. The 126 Gb/s figure is `32 × 4 × (128/130) ÷ 8` from that link. `ib_write_bw` was about 99.7 Gb/s on one rail and about 97.9 + 97.9 with both rails active.

**Spec sheets:**

- DGX Spark memory bandwidth 273 GB/s, 128 GB LPDDR5X, 240W power supply, 140W GB10 TDP: [NVIDIA specifications](https://www.nvidia.com/en-us/support/dgx-spark.md)
- RTX 4090 memory bandwidth 1008 GB/s, 24 GB: [NVIDIA GeForce](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/). A 48 GB mod is a capacity mod. The bandwidth number is still the stock card's. There is no single spec sheet for the mod.
- Mac Studio: M4 Max 410 GB/s, 546 GB/s on the 40-core GPU; M3 Ultra 819 GB/s. [Apple technical specifications](https://www.apple.com/mac-studio/specs/)

**Community benches.** The ~4% clock gain is the three-node post. The four-node 35.7 is a different post.

- Two nodes, NVFP4: body median 21.8 tok/s, peak 22.7. The title says 43.4. The same post's four-node TP4 figure is 35.7. [NVIDIA forum](https://forums.developer.nvidia.com/t/glm-5-3-flash-on-2x-nvidia-dgx-spark-43-4-tok-s-peak-checkpoint/381429)
- Another two-node run: 24.7 tok/s code, 30.3 structured, 19.6 prose, 14.6 with speculative decoding off. Single stream, temperature 0. [Forum](https://forums.developer.nvidia.com/t/glm-5-3-flash-running-on-2x-dgx-spark-sm-121-day-0-24-7-30-3-tok-s-with-mtp-5-two-silent-gb10-gotchas-worth-knowing/381433), [recipe](https://github.com/kingjones30/GLM-5.3-Flash-2x-DGX-Spark)
- Three nodes, TP3: 35.2 tok/s at 1500 MHz, 36.8 at 2100 MHz. At about 160K tokens of context, 7.5 tok/s per stream at two-way and 6.1 at three-way. [NVIDIA forum](https://forums.developer.nvidia.com/t/glm-5-3-flash-nvfp4-on-3x-dgx-spark-tp-3-512k-context-35-tok-s/381534)
- Two nodes, EXL3 4bpw: 62.9 tok/s structured, prose median 26.9. [MiaAI](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks/blob/main/README.md)
- One node, EXL3 2.05bpw: about 64 structured, about 25 prose. Replies mention looping and quality. [Forum](https://forums.developer.nvidia.com/t/60-tok-s-glm-5-3-flash-on-a-single-dgx-spark/382140), [model card](https://huggingface.co/gitcommit90/GLM-5.3-Flash-EXL3-2.05-One-Spark)
- DeepSeek V4.1 Flash on a four-node ring: about 43–50 tok/s one stream. [Log](https://github.com/yunwei37/dgx-spark-4-ring-no-switch/blob/main/docs/deepseek-v41-flash.md). Another four-node post reports 23 tok/s prose. [Forum](https://forums.developer.nvidia.com/t/deepseek-v4-1-flash-552b-moe-on-4x-dgx-spark-tp4-77-2-tok-s-c1-on-peak-52-code-72-tok-s-on-a-warm-code-run-47-math-39-reasoning-23-prose/382897). Two-node EXL3 is marked not benchmarked; four-node EXL3 prose is 30.2 and code is 33.4. [Recipe](https://github.com/vcruz305/DeepSeek-V4.1-Flash-EXL3-DGX-Spark-recipe)
