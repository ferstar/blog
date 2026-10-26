---
title: "RTX 4090 D Tensor Unlock: What Can Quantized MoE Inference Gain?"
slug: "tensor-unlock-quantized-moe"
date: "2026-10-26T16:16:00+08:00"
tags: ["gpu", "nvidia", "llm", "inference", "strata", "moe"]
description: "The 4090 D unlock doubles floating-point Tensor throughput, but quantized MoE inference gains almost nothing. PTX assembly and benchmarks explain why removing floating-point limits cannot solve integer and bandwidth bottlenecks."
draft: false
---

> I am not a native English speaker; this article was translated by AI.

In [the previous post]({{< relref "rtx4090d-gpu-unlock-strata-benchmark.md" >}}), I unlocked the RTX 4090 D and measured nearly doubled throughput on certain Tensor GEMM workloads. [After sharing the results on X](https://x.com/ferstar_org/status/2114172808305762327?s=20), a friend noted: "This probably does little to nothing for quantized MoE inference."

This card mainly runs Strata with an IQ3_S-quantized Qwen3.8-Flash-Next model. Checking the source and logs against actual compute paths confirms that assessment.

{{< alert icon="lightbulb" cardColor="#e0f2fe" iconColor="#0284c7" textColor="#0369a1" >}}
**TL;DR**: **Virtually zero gain (fluctuations stay within measurement noise).**
The 4090 D unlock only restores floating-point Tensor rates (FP16/BF16/TF32). Low-bit quantized MoE inference runs predominantly on **INT8/INT32 integer instructions**, where real-world bottlenecks lie in **memory bandwidth, PCIe transfers, and CPU offloading**, rather than floating-point compute.
{{< /alert >}}

## Why Doubled FP Throughput Does Nothing for Quantized MoE

### Floating-Point Rates Grew, but Integer Stayed Flat
First, the controlled benchmark (multiplying square matrices of side 8192 under the same 425 W power limit):

| GEMM Mode | Stock TFLOPS | Unlocked TFLOPS | Throughput Gain |
|---|---:|---:|---:|
| FP16 → FP32 | 152.83 | 195.96 | **+28.22%** |
| BF16 → FP32 | 153.81 | 250.97 | **+63.16%** |
| TF32 | 76.49 | 145.55 | **+90.28%** |
| Regular FP32 Control | 54.27 | 54.71 | +0.80% |

Compute paths taking FP16/BF16 inputs with FP32 accumulation improved significantly. **However: INT8, INT4, and dp4a instruction throughput remained completely identical.**

### Strata Expert Kernels Run Pure Integer Instructions
Despite the large parameter count of MoE models, what instructions actually run when serving an IQ3_S-quantized model?

Examining Strata 0.1.48's [quantized-expert prefill kernel](https://github.com/Niko1221/Strata/blob/5c8dd322528cc84f68f461ad54a506b9da8fa8d4/src/prefill/moe_fused_iq.cu#L163) source code reveals the direct PTX instruction:

```text
mma.sync.aligned.m16n8k32.row.col.s32.s8.s8.s32
```

Here, `s8` represents signed INT8 inputs, and `s32` represents INT32 accumulation. This instruction belongs entirely to the **integer execution path that received zero speedup**. While secondary routines (e.g. attention and minor cuBLAS calls) use some BF16 operations, the critical path is dominated by integer arithmetic and dequantization/data unpacking.

### The Bottleneck is Memory Bandwidth and Offloading, Not Compute
The unlock does not grant the 4090 D a single additional byte of memory bandwidth or PCIe bandwidth. Strata keeps a subset of experts in VRAM while offloading the rest to host RAM via CPU computation in an overlapping pipeline. The system is fundamentally bounded by memory bandwidth and data transfers. By Amdahl's Law, speeding up an operation that occupies a negligible portion of the runtime yields no noticeable overall improvement.

## Benchmark Verification: Does Unlocking Make It Faster?

### Community Results: Controlled 48GB 4090 Benchmark (0.98x - 0.99x)
A researcher evaluated this scenario on a hardware-modded 48 GB RTX 4090 running Strata 0.1.47 with IQ3_S under a [controlled test](https://github.com/JustAResearcher/gpu-unlock-ada/blob/d28c485418c3d9d034cd4bac19200bc33dd3453b/docs/evidence/rtx4090-48g-modded/serving-workload.md):

| Prefill Scenario | Stock tokens/s | Unlocked tokens/s | Unlocked / Stock Ratio |
|---|---:|---:|---:|
| 8K Input | 3518.8 | 3457.8 | **0.983×** |
| 32K Input | 3916.6 | 3890.3 | **0.993×** |

The data is unmistakable: under long-input prefill, performance showed no gain and even fell slightly within noise margins. Generation (decode) throughput similarly fluctuated without measurable advantage.

### Local Serving Window Observation
In my local Strata 0.1.48 deployment, monitor snapshots across long operating windows showed comparable patterns:

| Metric | Unlocked Window (82 reqs) | Stock Window (39 reqs) |
|---|---:|---:|
| Generated Tokens | 60,707 | 25,163 |
| Weighted Generation Rate (tokens/s) | 126.34 | 141.14 |
| Median Generation Rate (tokens/s) | 130.6 | 142.2 |
| Weighted Prefill Rate (tokens/s) | 1775.79 | 2170.54 |
| Prefix Reuse Ratio | 94.02% | 82.87% |
| MTP Draft Acceptance Ratio | 68.05% | 72.58% |

{{< alert icon="triangle-exclamation" cardColor="#fef3c7" iconColor="#d97706" textColor="#b45309" >}}
Request lengths and cache hit rates vary in natural workloads, so this is not a strictly controlled A/B test. However, it confirms that **the stock-rate setup fully matches or exceeds the unlocked performance level in practice; unlocking delivers no palpable difference.**
{{< /alert >}}

## Which Workloads Actually Benefit from Unlocking?

If quantized MoE inference gains almost nothing, where does the unlocked Tensor power actually pay off?

1. **Full / Half-Precision Fine-Tuning and Training (LoRA / SFT)**: Heavy matrix multiplication paths utilizing FP16/BF16 inputs with FP32 accumulation see immediate, significant acceleration.
2. **Diffusion Models for Image/Video Generation (Stable Diffusion / Flux / CogVideoX)**: Denoising backbones rely heavily on dense floating-point GEMM residing entirely within VRAM.
3. **Dense LLM Inference with Native Precision (e.g., BF16) and Large Batches**: Compute-bound rather than memory-bandwidth-bound regimes reap clear rewards.

## Stability and Data Archiving

During prolonged operation, the card encountered an `Xid 79: GPU has fallen off the bus` event. It also recurred once after reverting to stock rates, indicating the incident was not strictly tied to the unlock state itself, but rather related to power transients, drivers, or custom kernel settings (`7.3.0-ros2go-btf`). The card is currently running in stable daily service at stock rates.

A dedicated replay script with fixed prompts and aligned cache states has been prepared for future controlled tests. Sanitized raw CSVs and verification scripts are available:
- [Sanitized Request-Timing CSV](/downloads/tensor-unlock-moe/requests.csv)
- [Summary and Measurement Notes JSON](/downloads/tensor-unlock-moe/summary.json)
- [Offline Verification Script verify.py](/downloads/tensor-unlock-moe/verify.py)
- [Download Notes and Checksums](/downloads/tensor-unlock-moe/README.md)
