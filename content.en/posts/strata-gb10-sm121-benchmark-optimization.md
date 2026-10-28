---
title: "Strata 0.2.7.1 on GB10 Benchmark and SPEC_COST Ablation"
slug: "strata-gb10-sm121-benchmark-optimization"
date: "2026-10-28T21:15:00+08:00"
tags: ["strata", "gb10", "sm_121", "arm64", "llm", "inference", "benchmark"]
description: "Upgraded to Strata 0.2.7.1 on GB10 to evaluate prefill and decode performance, using ABBA ablation testing to verify the actual latency impact of the SPEC_COST switch."
---

> I am not a native English speaker; this article was translated by AI.

Previously, I ran Strata on the [DGX Spark]({{< relref "dgx-spark-agent-inference.md" >}}). The machine features an ARM64-based GB10 with CUDA compute capability `sm_121`. To get Strata running on ARM64, I submitted [PR #3622](https://github.com/Niko1221/Strata/pull/3622). In the merge commit, the maintainer noted that without physical ARM hardware on hand, the memory ordering was derived logically (*"Memory ordering on ARM is reasoned, not run"*). Testing on actual silicon, I verified the multi-threaded speculative verification with `dmb ishld` memory barriers across `--spec 2` and `--spec 4` windows, confirming byte-identical output consistency.

The maintainer quickly followed up with `v0.2.7.1`, bringing the underlying engine to a newer release. This tag directly provided official Linux ARM64 prebuilt archives (`strata-engine-linux-aarch64-cuda-cuda13.tar.gz`), added `docs/DGX_SPARK_LINUX.md`, and enabled four optimizations by default for `sm_121`:

- `STRATA_PF_FUSED`: Operator fusion during prefill
- `STRATA_PREFILL_NVFP4`: NVFP4 prefill targeting Blackwell architectures
- `STRATA_HC_UPMIX`: Mixed-precision channel up-mixing
- `STRATA_SPEC_COST`: Dynamic adjustment of speculative verification windows based on runtime cost and acceptance rate

The upstream release notes mentioned roughly a 1.20x–1.24x prefill speedup on the Spark. With the package published, I pulled it onto the machine to run an A/B benchmark.

## Benchmark Setup

The runtime configuration remained identical: 262K context, INT8 KV cache, MTP, spec4, mmap experts, with all 24,576 experts resident in unified memory and no prompt cache.

To avoid cold-start discrepancies skewing the results, the tests followed a cross-validation sequence:

Legacy → Intermediate → New engine (with sm_121 optimizations disabled) → New engine with defaults → restart and reverse order.

Short requests used two warmups followed by three formal requests, confirming token output consistency. Long prompts were evaluated at 4K (4,099 tokens actual) and 16K (16,387 tokens actual).

| Version and Config | Short Decode Median | 4K Prompt Median | 16K Prompt Median |
|---|---:|---:|---:|
| 0.1.47 | 8260 ms | 2924 ms | 12474 ms |
| 0.1.52 | 8130 ms | 2873 ms | 12451 ms |
| 0.1.53, `STRATA_SM121_PERF=0` | 8179 ms | 2822 ms | 10190 ms |
| 0.1.53, defaults enabled | 8736 ms | 2364 ms | 10192 ms |

The actual results showed two trends:

First, prefill was noticeably faster. Latency on 4K prompts dropped by nearly 20%, matching the 1.20x claim. At 16K, toggling hardware optimizations inside the new engine made little difference, but it was still over two seconds faster than the older builds.

Second, decode showed the opposite trend: short decode under default settings on the new engine ran a few hundred milliseconds slower than with optimizations disabled.

## Testing SPEC_COST with ABBA

The decode slowdown naturally draws attention to `STRATA_SPEC_COST`, as it directly manages speculative window adjustment. Looking at a single benchmark run, it is easy to assume that the extra overhead slowed down generation.

On real hardware, however, variance across process starts can be considerable. To determine whether this switch caused the regression, I kept the identical binary and memory layout, toggling only `STRATA_SPEC_COST=0` across four independent processes in an **ABBA sequence (Default → Off → Off → Default)**:

| Process | Config | Short Decode Median | 4K Prompt | 16K Prompt | Speculative Windows |
|---|---|---:|---:|---:|---|
| Process 1 | Default (on) | 8359.9 ms | 2381 ms | 10309 ms | 201–202 |
| Process 2 | Cost-off (off) | 8567.1 ms | 2322 ms | 8605 ms | 205 (fixed) |
| Process 3 | Cost-off (off) | 8124.7 ms | 2296 ms | 8367 ms | 205 (fixed) |
| Process 4 | Default (on) | 8356.4 ms | 2279 ms | 8333 ms | 192–197 |

Log inspection confirmed that the parameter was effective: with cost off, verification windows stayed fixed; with cost on, windows fluctuated dynamically within a range, evaluating more draft candidates.

Looking at decode time, however:
- From Process 1 to Process 2, disabling cost was about 2.5% slower;
- From Process 3 to Process 4, re-enabling cost was also about 2.8% slower.

{{< alert >}}
The direction reversed across both pairs. This shows that natural variance across individual process starts (around 200–300 ms) outweighs the effect of the switch itself. The decode slowdown cannot be attributed to `SPEC_COST`.
{{< /alert >}}

This test eliminated a false hypothesis, preventing an inaccurate upstream report claiming that disabling `SPEC_COST` fixes decode latency.

## Current Status

Having ready-made prebuilt packages and documentation for the Spark is very convenient, and all hardware-specific flags can be toggled off via environment variables, making testing straightforward.

The machine continues running the new version. The short decode gap is relatively minor for now, and I will isolate the impact of `STRATA_HC_UPMIX` and `STRATA_PF_FUSED` when time permits.
