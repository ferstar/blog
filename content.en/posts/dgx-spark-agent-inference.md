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

## Don't Be Fooled by "200G" Ports and Synthetic Benchmarks

When people see two 200G ports on each machine, their immediate assumption is often: "Dual-rail 400G aggregated inter-node bandwidth!"

Run `ethtool` and `lspci` once and the illusion falls apart:

1. **The physical inter-node bandwidth ceiling is ~200 Gb/s**: The two machines connect directly via dual QSFP DAC cables—no switch, and no inter-node NVLink. While `ethtool` reports `200000Mb/s` on both ports, the ConnectX-7 behind each port is only wired to PCIe Gen5 x4 (`32GT/s, Width x4`). The unidirectional theoretical max is only about 126 Gb/s:
   
   `32 × 4 × (128/130) ÷ 8 ≈ 15.8 GB/s ≈ 126 Gb/s`

   With `ib_write_bw`, a single cable saturates at ~99.7 Gb/s, and dual rails run at 97.9 + 97.9 ≈ 196 Gb/s aggregate.
2. **Memory bandwidth is the real bottleneck**: DGX Spark uses unified memory with 128 GB LPDDR5X per node, delivering only **273 GB/s** of bandwidth.
   Compare that against mainstream hardware:
   - RTX 4090: **1008 GB/s** (24 GB VRAM)
   - Mac Studio M4 Max: **410–546 GB/s**
   - Mac Studio M3 Ultra: **819 GB/s**

DGX Spark’s selling point is **"massive unified memory capacity"**, not **"high memory bandwidth"**. A 200G link is plenty to shard an oversized model across two nodes via TP=2, but decode speed stays pinned by the 273 GB/s memory bandwidth anyway.

---

## Synthetic Benchmarks Look Fantastic: Short Prompts

Running typical benchmark scripts with fixed 128-token short prompts and `ignore_eos` enabled:

| Concurrency | Aggregate Throughput (tok/s) | Latency & Per-Stream Decode |
| :--- | :---: | :--- |
| **1** | 37.1 | Single-stream decode ~43.8 tok/s |
| **2** | 73.6 | Linear scaling |
| **4** | 127.4 | Decent multi-stream scaling |
| **6** | **172.7** | Peak aggregate throughput, batch finished in 4.5s |
| **8** | 79.8 | Wall time 12.8s, per-stream decode scattered from 10 to 47 tok/s |

Six-way concurrency is the peak, 172.7 tok/s aggregate. At eight streams the aggregate falls to 79.8 and the per-stream rates scatter. I did not see a scheduler error. Idle single-stream decode touches about 54 tok/s. A normal back-and-forth chat, with prefix-cache hits around 90%, stays around 35–45 tok/s.

It’s why benchmarks written up online love shouting "170+ tokens/sec!"—they’re measuring a few hundred idle bytes, each stream decoding in its own little bubble.

---

## Real Workloads: 5 Sub-Agents Scanning a Codebase Stall Out

Next, I hooked the setup into my daily Coding Agent environment and spawned 5 sub-agents to concurrently explore a medium-sized open-source repo.

The backend looked perfectly healthy: HTTP 200 everywhere, queue depth zero.

Then reality hit: **single-stream generation dropped to 15–25 tok/s. After 6 full minutes, not a single sub-agent summary had finished streaming.**

What that session actually recorded: HTTP 200, queue depth 0, 15–25 tok/s per stream, and no final answer after six minutes. A separate two-stream decode was about 65–75 tok/s aggregate, about 30–37 each. The 173 figure is a 128-token `ignore_eos` aggregate. It is not the same kind of input.

Long prefill is a different observation, not a log line from the five-stream run. Prefill of about 250K tokens can take minutes by itself and pulls generation speed down inside the same stats window. This run did not record each stream's input length or its prefix-cache hit rate. The ~90% hit rate is from single-user chat with a repeated system prompt. Sub-agents reading different files should hit less of that cache. That is an inference, not a measurement from this run.

---

## Other two-node logs sit in the same band

Published GLM-5.3-Flash NVFP4 on two Sparks is about 20–30 tok/s on one stream, and about 36 on four. Raising the GPU clock from 1500 MHz to 2100 MHz adds about 4% decode. That clock result is the three-node post, not the four-node 35.7. The post titled 43.4 reports a median of 21.8 in the body. Figures in the sixties come from lower-bit EXL3, structured output, and a short context. DeepSeek V4.1 Flash full weights are served in four-node recipes. A two-node EXL3 folder exists and is marked not benchmarked. Links are at the end.

---

## Epilogue: Switching to a Modded Card—Does the Math Add Up?

Someone's bound to ask: same budget, why not just buy a modded card? Don't reach for the wallet yet—a bare card is only the opening line; the real bill comes after:

- **48G-modded RTX 4090**: 1008 GB/s on one card, more than three times the Spark's bandwidth. But a card is not a machine. Board, CPU, RAM, a kilowatt PSU, case and cooling all cost extra, and everyone knows what memory prices did in 2026. It also assumes you already own a desktop to plug it into—if you do, sure, that's free performance.
- **96G-modded RTX 5090**: Suqiao's Alibaba listing was $3,888 for the bare card. The same reports point out that the product page calls the memory GDDR6X at 14Gbps, which does not add up to 96GB, and no independent teardown covers the first batch. [cnBeta](https://www.cnbeta.com.tw/articles/tech/1577618.htm), [Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/china-modified-nvidia-rtx-5090-with-massive-96gb-of-memory-appears-on-alibaba-for-less-than-usd4-000-3x-more-vram-at-65-percent-the-cost-of-the-original)
- **Two Sparks**: no assembly. NVIDIA lists a 240W power supply and a 140W GB10 TDP, with the vendor warranty. The 128 GB is inside the system price.

The bandwidth gap is on the spec sheets. I did not price a full host against two Sparks, so this section does not say which bill is smaller.

---

## Takeaways: What Is This Setup Actually Good For?

If you have a dual DGX Spark cluster:

- **Barely acceptable fit**: Single-user, turn-by-turn pair programming. With a stable system prompt and high prefix cache hit rates, 35–45 tok/s is just about usable without depending on cloud APIs—provided your code and data are too sensitive to ever leave your machine; otherwise the performance penalty simply isn't worth it.
- **Natural fit**: An expensive flex / desktop toy for tech influencers and sponsored reviewers. It looks sleek on a desk, screams "cutting-edge geek", and recording short-prompt benchmarks produces delightfully inflated charts.
- **Unrealistic fit**: Acting as the backend for concurrent multi-agent swarms, repository-wide audits, or heavy long-context workloads. LPDDR5X memory bandwidth and long-context prefill latency will humble you instantly.

Piling on more nodes only solves **"can we fit the model in memory"**; it does nothing to change the physical reality that **"single-stream decoding stays slow"**. Don't fool yourself with short-prompt benchmarks: under real agent workloads, physical bottlenecks never lie.

## Sources

Numbers from these two machines stay separate from numbers copied out of other people's posts.

**Measured here in September 2026. No public log.** MiMo used [tonyd2wild's two-node recipe](https://github.com/tonyd2wild/MiMo-V2.6-Flash-DGX-Spark-Recipe), TP=2, model id `mimo-v2.6-flash`, `max_model_len` 300,000, `max_num_seqs` 8, served on port `:8888` of the head node. The short-prompt table is 128-token generations with `ignore_eos`, sent from my own machine. The five-sub-agent run is a real session on that same server: nothing queued, about 15–25 tok/s per stream, and no final answer after six minutes. `ethtool` reported `200000Mb/s`, Direct Attach Copper, on both live ports. `lspci` showed PCIe Gen5 x4 (`32GT/s, Width x4`) on both. The 126 Gb/s figure is `32 × 4 × (128/130) ÷ 8` from that link. `ib_write_bw` was about 99.7 Gb/s on one rail and about 97.9 + 97.9 with both rails active.

**Spec sheets, not measured token rates.**

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
