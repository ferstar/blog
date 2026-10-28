---
title: "Strata 0.2.7.1 在 GB10 上的性能变化与 SPEC_COST 实测"
slug: "strata-gb10-sm121-benchmark-optimization"
date: "2026-10-28T21:15:00+08:00"
tags: ["strata", "gb10", "sm_121", "arm64", "llm", "inference", "benchmark"]
description: "升级 Strata 0.2.7.1 后实测 GB10 的 prefill 和 decode 表现，通过 ABBA 交叉测试排查 SPEC_COST 开关对投机解码延迟的实际影响。"
---

之前在 [DGX Spark]({{< relref "dgx-spark-agent-inference.md" >}}) 上跑 Strata，这台机器配的是 ARM64 架构的 GB10，CUDA 计算能力（Compute Capability）为 `sm_121`。当时为了让 Strata 在 ARM64 下跑起来，我提了 [PR #3622](https://github.com/Niko1221/Strata/pull/3622)。作者在合入时重新梳理了 ARM 移植，在提交里提到因为没有 ARM 真机，内存屏障是推导出来的（*Memory ordering on ARM is reasoned, not run*）。我在实机上用 `--spec 2` 和 `--spec 4` 跨投机窗口验证了多线程下的 `dmb ishld` 内存屏障，确认输出逐字节一致。

作者随后发布了 `v0.2.7.1`，把底层引擎带到了新版本。这次直接附带了官方 Linux ARM64 预编译包（`strata-engine-linux-aarch64-cuda-cuda13.tar.gz`），补充了 `docs/DGX_SPARK_LINUX.md`，还针对 `sm_121` 默认打开了四项优化：

- `STRATA_PF_FUSED`：Prefill 算子融合
- `STRATA_PREFILL_NVFP4`：针对 Blackwell 架构的 NVFP4 预填
- `STRATA_HC_UPMIX`：混合精度通道提升
- `STRATA_SPEC_COST`：根据运行时成本与接受率动态调整投机验证窗口

作者在发布说明里提到，这套改动在 Spark 上能让 prefill 提速两成左右。正好新包发布了，我便在机器上拉下来跑了一遍基准对照。

## 对照条件

机器上的模型配置保持一致：262K context、INT8 KV cache、MTP、spec4、mmap experts，24576 个专家全部常驻 GPU 统一内存，不设 prompt cache。

为了避免进程刚启动的冷热状态影响判断，测试按交叉顺序跑：

旧版 → 中间版 → 新版本（环境变量关掉 sm_121 优化） → 新版本默认配置 → 重启再反向跑一轮。

短请求固定两次 warmup 加三次正式请求，确认 token 输出一致；长 prompt 测了 4K（实际 4099 tokens）和 16K（实际 16387 tokens）。

| 版本与配置 | 短 decode 中位数 | 4K prompt 中位数 | 16K prompt 中位数 |
|---|---:|---:|---:|
| 0.1.47 | 8260 ms | 2924 ms | 12474 ms |
| 0.1.52 | 8130 ms | 2873 ms | 12451 ms |
| 0.1.53，`STRATA_SM121_PERF=0` | 8179 ms | 2822 ms | 10190 ms |
| 0.1.53，默认全开 | 8736 ms | 2364 ms | 10192 ms |

实际结果有两个现象：

一个是 prefill 确实快了。4K prompt 耗时降了接近两成，和作者说的 1.20x 对得上；16K 下新版本开不开硬件优化区别不大，但比老版本快了 2 秒多。

另一个是 decode。新版本默认配置下的短 decode 反而比关掉优化慢了几百毫秒。

## 用 ABBA 测 SPEC_COST

decode 变慢容易让人联想到新增的 `STRATA_SPEC_COST`，因为这个开关直接管投机验证窗口的调整。如果只测一次，很容易觉得是开销变大把速度拖慢了。

不过在实机上跑，进程启动时的环境状态波动本来就不小。为了确认因果关系，我保持同一个官方二进制和显存配置，只切换 `STRATA_SPEC_COST=0`，按 **ABBA（默认 → 关 → 关 → 默认）** 跨四个独立进程跑了一轮单变量测试：

| 测试进程 | 配置 | 短 decode 中位数 | 4K prompt | 16K prompt | 投机窗口数 |
|---|---|---:|---:|---:|---|
| 进程 1 | 默认（开启） | 8359.9 ms | 2381 ms | 10309 ms | 201–202 |
| 进程 2 | cost-off（关闭） | 8567.1 ms | 2322 ms | 8605 ms | 205（固定） |
| 进程 3 | cost-off（关闭） | 8124.7 ms | 2296 ms | 8367 ms | 205（固定） |
| 进程 4 | 默认（开启） | 8356.4 ms | 2279 ms | 8333 ms | 192–197 |

从窗口表现看，参数确实生效了：关掉之后验证窗口保持固定；开启时会在动态区间内浮动，尝试更多 draft 候选。

但如果看 decode 时间：
- 从进程 1 到进程 2，关掉后慢了大约 2.5%；
- 从进程 3 到进程 4，重新打开后又慢了大约 2.8%。

{{< alert >}}
两次对比的方向是反过来的。这说明单次启动之间的跨进程抖动（两三百毫秒）已经盖过了这个开关本身的影响，不能把 decode 变慢算在 `SPEC_COST` 头上。
{{< /alert >}}

这个测试至少排除了一个错误假设，省得回头给上游提一个“把 SPEC_COST 关掉就解决”的乌龙 issue。

## 当前状态

上游这次给 Spark 专门做预编译包和文档挺省事的，而且这几项针对性设置都留了环境变量可以随时关掉，测起来很方便。

目前机器上继续跑新版本。短 decode 的那点差距还不算大，后面有空再单独排查 `STRATA_HC_UPMIX` 和 `STRATA_PF_FUSED` 的影响。
