---
title: "RTX 4090 D Unlock Measurements: Doubled Tensor Throughput and a Strata Retest"
slug: "rtx4090d-gpu-unlock-strata-benchmark"
date: "2026-10-25T08:30:00+08:00"
tags: ["gpu", "nvidia", "llm", "inference", "strata", "qwen"]
description: "The experiment's baseline lacked RTX 4090 D dispatch. A local adaptation passed two test boots, improved GEMM by 28%–90%, and enabled fresh Strata measurements. A later cross-check found corroborating reports and a separately merged 4090 D implementation."
---

> I am not a native English speaker; this article was translated by AI.

[The previous post]({{< relref "qwen38-flash-next-strata-4090.md" >}}) set up Strata on my RTX 4090 D at home, where it has been running Qwen3.8-Flash-Next. After finding [gpu-unlock](https://github.com/Zagitta/gpu-unlock), I wanted to see whether it would work on this card and how fast inference would run afterward.

At the start of the experiment, community AD102 implementations covered the regular 4090, while the selected baseline did not yet include the 4090 D. On October 24, an AI assistant added that support and ran the unlock, numerical checks, and before/after benchmarks on this machine, followed by another round of measurements against the existing Strata service.

## Device dispatch for the 4090 and 4090 D

This card has PCI ID `10de:2685`, an Ada AD102 GPU, 114 SMs, and 24 GB of VRAM. The system runs Ubuntu 24.04.4 LTS. The experiment kept kernel `6.17.0-1032-oem`, the existing NVIDIA `595.58.03 open` driver, and a 425 W power limit throughout. Secure Boot was already disabled.

Support depends on the branch. The initial check covered only Zagitta's main, which contained the Ampere GA102, GA103, GA104, and GA106 implementations. Further inspection of branches and forks found [elias-gaeros's rtx4090 branch](https://github.com/elias-gaeros/gpu-unlock/tree/4ec490d49c1cc292c0b4cd5ce5a801b5d2c396dc) and [JustAResearcher/gpu-unlock-ada](https://github.com/JustAResearcher/gpu-unlock-ada/tree/491925c1079435e260137b9f3526066e764de830). The main-branch statement refers to the [specific commit inspected](https://github.com/Zagitta/gpu-unlock/tree/4189b17711bd487d9ea4a8ff0055e6d58d19d6d3).

The regular 4090 has device ID `2684`, already included in both inspected community commits. Neither commit included the 4090 D's `2685` at that point. Starting from the pinned JustAResearcher commit, the patch updated device admission, AD102 firmware selection, the `is_ad102()` architecture check, and the corresponding host tests. Adding only an allowlist entry would select the GA102 firmware path.

The new device also requires an explicit `ad102d_experimental=1` switch. Its `targets` value must equal one complete PCI address; `all` and comma-separated lists are rejected. The target on this machine is `0000:01:00.0`, keeping the experiment scoped to this card.

The unlock firmware assets are version `610.43.03`. The NVIDIA driver loaded afterward remains the version given above. No VBIOS was flashed.

## Booting through a separate entry

The unlock module must load before the NVIDIA driver. With Strata already running, inserting it against a card owned by the driver was not the test path. The service was briefly stopped to capture the locked rates, numerical checks, and compute baseline, then restored while the next boot was prepared.

The root filesystem is Btrfs, and the default boot kernel was already one version newer than the running kernel. To keep the same kernel on both sides of the comparison, a separate kernel and initramfs were copied to the EFI partition. A dedicated test entry was selected for the next boot with UEFI `BootNext`, preserving the original default boot order.

The experimental initramfs contains the module, firmware, and an early loading script that runs before the existing init-top scripts. This is the essential load command, executed during early boot with this machine's target address:

```sh
insmod /gpu_unlock-4090d.ko targets=0000:01:00.0 ad102d_experimental=1
```

After the first normal reboot, the log recorded selector writes, readback after a PCI function-level reset (FLR), and a successful unlock. The unmodified driver then loaded. In the read-only rate query, `fmla32`, `imla2`, and `imla4` changed from `1` to `0`; this interface defines those values as half rate and full rate, respectively.

One systemd detail showed up during recovery of the service. The first boot used the kernel parameter `systemd.mask=strata.service` to keep the model from filling VRAM automatically. That mask comes from a generator and is recreated on daemon-reload, so `systemctl unmask --runtime` alone cannot remove it. For the second boot, that kernel parameter was removed and the same test entry selected again. The unlock succeeded again, Strata started from its original unit, and the health check reported a loaded model.

Both runs were normal reboots. There was no power-cycle test or long-duration stability workload. The model service and rates were checked after the second boot; the untested return to the original boot path is described below.

## Compute throughput and numerical checks

Changed rate fields still need confirmation from actual computation. The before/after cuBLAS GEMM runs used the same benchmark binary and power limit, square matrices of side 8192, five samples per mode, and 20 iterations per sample. The table reports median throughput. Both the FP16 and BF16 modes accumulate in FP32.

| GEMM mode | Before TFLOPS | After TFLOPS | Gain |
|---|---:|---:|---:|
| FP16 → FP32 | 152.83 | 195.96 | 28.22% |
| BF16 → FP32 | 153.81 | 250.97 | 63.16% |
| TF32 | 76.49 | 145.55 | 90.28% |
| Regular FP32 control | 54.27 | 54.71 | 0.80% |

The MMA instruction microbenchmark uses the best throughput from three measurements with the same configuration. Its aggregation differs from the GEMM median above.

| MMA mode | Before | After | Unit |
|---|---:|---:|---|
| FP16 / FP32 accumulation | 145.1 | 291.5 | TFLOPS |
| BF16 / FP32 accumulation | 145.0 | 289.6 | TFLOPS |
| FP16 / FP16 accumulation | 290.3 | 291.6 | TFLOPS |
| INT8 / INT32 accumulation | 579.7 | 579.6 | TOPS |
| dp4a | 144.1 | 144.1 | TOPS |
| scalar FFMA | 68.8 | 68.9 | TFLOPS |

The change is concentrated in Tensor operations with FP32 accumulation. FP16 accumulation and integer controls remain essentially unchanged. A separate tensor cubin benchmark also measured approximately doubled TF32 throughput and unchanged INT4 throughput. Actual GEMM gains depend on the data type; doubling one instruction's throughput does not establish a doubled application speed.

Numerical checks ran both before and after the unlock. FP16 and BF16 GEMMs with FP32 accumulation each checked 65536 elements, reporting `failures=0` and `max_abs=0`. The separate cubin checks for FP16, TF32, and INT4 each covered 270336 elements, all with `mismatches=0`. These results cover the inputs and precision modes used in these benchmarks.

The host unittest run contained 22 tests: 19 passed, and three offline-decryption tests were skipped because the optional PyCryptodome dependency was absent. The module compiled against the pinned kernel with `KCFLAGS=-Werror`. Neither boot log contained NVIDIA Xid, GPU fallen off bus, or kernel Oops/BUG errors. The performance tables come from one before/after experiment with repeated samples; the second reboot checked the unlock and service state without repeating the full compute suite.

## Cross-check against later community commits

While preparing this post, the JustAResearcher repository was checked again at [commit `4e7fefcc`](https://github.com/JustAResearcher/gpu-unlock-ada/tree/4e7fefcc4923f9e083d5324dc75a7d2f906af77f). It had merged [RTX 4090 D support in PR #7](https://github.com/JustAResearcher/gpu-unlock-ada/pull/7), routing device admission, firmware selection, and architecture checks through AD102. That version uses `rtx4090d_experimental=1` and permits multiple selected cards after opt-in. The patch tested here retains the earlier switch name and single-card restriction. The attachment stays pinned to its original baseline, so the two parameter sets must be kept distinct.

The [matched regular-4090 report from PR #1](https://github.com/JustAResearcher/gpu-unlock-ada/blob/4e7fefcc4923f9e083d5324dc75a7d2f906af77f/docs/evidence/rtx4090-pr1-matched/README.md) includes raw timings and numerical results. FP16 and BF16 instruction throughput with FP32 accumulation rose from 160.4 and 159.7 TFLOPS to 320.4 and 320.2 TFLOPS, respectively; FP16 accumulation and integer controls remained essentially unchanged. Recalculating its GEMM logs gives gains of about 12% and 16% for the two 8192-square cases. An [ordinary warm-reboot repeat](https://github.com/JustAResearcher/gpu-unlock-ada/blob/4e7fefcc4923f9e083d5324dc75a7d2f906af77f/docs/evidence/rtx4090-pr1-matched/warm-reboot-repeat/README.md) retained nearly doubled instruction throughput, while 4096-square BF16 GEMM was about 8% slower than the original stock baseline. These results corroborate the instruction paths that benefited on this machine and show why application gains need workload measurements. The GPUs, drivers, CUDA versions, and matrix inputs differ, so each experiment keeps its own percentages.

There is also an [independent 4090 D user report](https://github.com/JustAResearcher/gpu-unlock-ada/pull/7#issuecomment-6390126655): on an eight-card node, a before/after measurement on one card rose from about 148 to 296 TFLOPS. All eight cards then unlocked after a reboot and passed numerical checks; the existing ComfyUI workflow took about 11% less time. This is a contributor's written report without attached raw logs, giving it less complete evidence than the regular-4090 dataset above.

The newer version also adds firmware hashing at load time, seeded numerical tests across multiple matrix shapes, and a fix for MMA repetition storage. This machine's unlock and benchmarks used the earlier code. The hardware results in this post remain tied to the original patch and pinned baseline; the public data notes also record one line-ending issue in the upstream checksum manifest.

## Current Strata performance

After the compute tests, real inference requests were sent to the existing service. Strata was now `0.1.47`, still running the official GSQ-RCO IQ3_S quantization of Qwen3.8-Flash-Next. Maximum context remained 262144, with int8 KV and 32768 resident cells per layer. The automatically allocated expert cache had 8548 slots and used 16599 MiB.

The existing launch configuration was preserved: `--spec 4`, `--spec-min-p 0.5`, the CJK draft vocabulary, and fused prefill. The engine capability fields separately reported `spec=6` and `mtp_max=4`; those are recorded separately from launch arguments. No configuration or engine binary was changed, and the service was not restarted during the measurements.

One warmup request was excluded, followed by three repetitions of each of five input/output lengths, for 15 formal requests. The service handled one request at a time, with thinking disabled and greedy sampling. Each input began with a distinct measurement ID, and every response was checked for `cached_tokens=0` and `cache_n=0` to exclude reuse of the preceding request's KV prefix.

Cold prefill here means a KV-prefix miss. The model was already loaded, and the expert cache warmed across requests without being cleared between runs; the first long-code request was retained in the sample set. The medium-length Chinese material was generated by the benchmark script, while the long-code input came from the Strata server source at the time. The measurements describe inference on these inputs.

| Input / output tokens | Content | Prefill token/s | Decode token/s | First token s | Full request s |
|---|---|---:|---:|---:|---:|
| 95 / 256 | Short Chinese request | 252.1 | 134.8 | 0.390 | 2.279 |
| 2060 / 256 | About 2K Chinese material | 985.6 | 137.3 | 2.104 | 3.959 |
| 8204 / 256 | About 8K Chinese material | 3365.2 | 144.6 | 2.454 | 4.213 |
| 120 / 1024 | Sustained Chinese output | 284.4 | 137.8 | 0.440 | 7.851 |
| 32784 / 512 | About 32K source review | 3421.9 | 129.0 | 9.616 | 13.571 |

Each column is the median of three runs, and the medians need not come from the same request. Input counts include the chat template. Prefill and decode use native server token counts and phase timings; first-token and full-request latency use a client monotonic clock. Draft tokens rejected by the main model are excluded from output throughput, and prefill time is excluded from decode throughput.

The sustained-generation runs had similar decode rates, while the first long-code request was somewhat slower. Short-input prefill rates are dominated by fixed overhead; the longer-input rows are the relevant ones for long-context throughput. All formal requests returned HTTP 200 and complete SSE termination. API output counts, engine-generated counts, and timing fields agreed. Each request ended at its configured token limit; answer quality was not evaluated.

## Comparison with the previous post

The final round in the previous post used the then-updated engine and a workflow with five subagents examining a project, yielding a batch of code-related requests. A separate long-source review was added this time to put its input length inside the earlier long-prefill group. The comparison below uses only that later comparison batch from the old post, without mixing in its earlier IQ3_S aggregate.

| Metric | Previous v0.1.39, locked | This run v0.1.47, unlocked | Observed difference |
|---|---:|---:|---:|
| Code-related median decode | 106.9 token/s | 129.0 token/s | +20.67% |
| Median cold prefill, long input | 2900 token/s | 3421.9 token/s | +18.00% |

The earlier decode distribution covers an entire code workflow. Its long-prefill median uses 16 requests with 20K–40K tokens computed without prefix reuse. This run has only three requests per input case, with different input text, generation lengths, and sampling settings. MTP acceptance and expert-cache hits also changed. Together with the engine upgrade, these factors contribute to the observed differences.

The measurements establish recovered throughput in some Tensor paths on this card and record the current model service's speed. Isolating the unlock's contribution to model inference requires locked/unlocked A/B runs with the same engine, inputs, and configuration.

## Patch, data, and the recovery path

The [4090 D patch](/downloads/rtx4090d-gpu-unlock/rtx4090d.patch) applies to the pinned community commit above and remains a local experimental change. The attachments include the [GEMM benchmark source](/downloads/rtx4090d-gpu-unlock/gemm_bench.cu), [15 inference records as CSV](/downloads/rtx4090d-gpu-unlock/inference-runs.csv?v=f2a4f3653ed8), and the [complete data archive](/downloads/rtx4090d-gpu-unlock-data.tar.gz). The [data notes](/downloads/rtx4090d-gpu-unlock/README.md) list the compute logs, rate readouts, boot-log excerpts, JSON timing fields, and checksum manifest used to reproduce the table aggregates. Firmware and module binaries are not bundled; firmware sources and licensing remain governed by the base repository.

At the end of the experiment, the machine was running through the test entry selected for the second boot. Strata was healthy, the model was loaded, and rates were full. `BootNext` had been consumed, the default boot order was unchanged, and automatic unlocking on the default boot path had not been configured.

To select the experimental entry again, first inspect `efibootmgr -v` to verify its label and number, then set the next boot. To return to the original path, check for a pending test BootNext; cancel it with `efibootmgr --delete-bootnext` if present, then reboot normally. Entry numbers are machine-specific and must not be copied from this machine. After booting the original path, read the rates again to determine whether half-rate operation has returned, with a power cycle if needed. That recovery reboot and the post-power-cycle state were not tested in this experiment.

The test image is tied to this kernel and module. A kernel change requires rebuilding and validation. For now, the separate boot entry remains available for explicit selection.
