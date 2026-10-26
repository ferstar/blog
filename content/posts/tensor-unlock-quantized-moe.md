---
title: "RTX 4090 D Tensor 解锁之后，量化 MoE 能快多少"
slug: "tensor-unlock-quantized-moe"
date: "2026-10-26T16:16:00+08:00"
tags: ["gpu", "nvidia", "llm", "inference", "strata", "moe"]
description: "4090 D 解锁翻倍了浮点 Tensor 算力，但跑低比特量化 MoE 几乎测不出收益。结合底层 INT8 PTX 汇编与实测数据，讲清为什么解开浮点枷锁治不好整数与带宽瓶颈。"
draft: false
---

[上一篇]({{< relref "rtx4090d-gpu-unlock-strata-benchmark.md" >}})给 RTX 4090 D 解锁了限制，在纯 GEMM 测试里，部分 Tensor 指令吞吐接近翻倍。[发到 X 后](https://x.com/ferstar_org/status/2114172808305762327?s=20)，有朋友提醒：“这对跑 MoE 量化推理可能几乎没用。”

我在家里这张卡上主要跑 Strata + IQ3_S 量化的 Qwen3.8-Flash-Next。翻了源码再拉出运行日志对照，实际情况确实如此。

{{< alert icon="lightbulb" cardColor="#e0f2fe" iconColor="#0284c7" textColor="#0369a1" >}}
**TL;DR**：**基本没有收益（波动全在测试噪声里）。**
4090 D 解锁只恢复了 FP16/BF16/TF32 等浮点 Tensor 算力；而低比特量化 MoE 真正跑的是 **INT8/INT32 整数指令**，推理瓶颈全卡在**显存带宽、PCIe 搬运与 CPU 异构调度**，跟浮点算力没太大关系。
{{< /alert >}}

## 为什么“浮点翻倍”在量化 MoE 上使不上劲

### 浮点算力涨了，整数原地踏步
先看本机的基准测试（边长 8192 方阵乘法，425 W 功耗上限）：

| GEMM 模式 | 原厂 TFLOPS | 解锁 TFLOPS | 吞吐提升 |
|---|---:|---:|---:|
| FP16 → FP32 | 152.83 | 195.96 | **+28.22%** |
| BF16 → FP32 | 153.81 | 250.97 | **+63.16%** |
| TF32 | 76.49 | 145.55 | **+90.28%** |
| 普通 FP32 对照 | 54.27 | 54.71 | +0.80% |

乘法输入为 FP16/BF16、累加为 FP32 的路径确实涨幅明显。但 **INT8、INT4 和 dp4a 指令吞吐完全没变**。

### Strata 专家内核走的是纯整数指令
MoE 模型参数量虽大，但以 IQ3_S 这种低比特格式加载后，GPU 实际在执行什么？

翻看 Strata 0.1.48 的[量化专家预填充内核](https://github.com/Niko1221/Strata/blob/5c8dd322528cc84f68f461ad54a506b9da8fa8d4/src/prefill/moe_fused_iq.cu#L163)源码，关键 PTX 汇编就这一句：

```text
mma.sync.aligned.m16n8k32.row.col.s32.s8.s8.s32
```

这里的 `s8` 是有符号 INT8 输入，`s32` 是 INT32 累加。这条指令正是基准测试里**完全没被加速的整数路径**。虽然注意力或部分 cuBLAS 调用里夹杂着少量 BF16 计算，但关键耗时全在整数矩阵乘与权重反量化/解包上。

### 瓶颈在显存带宽与异构通信，而非算力
解锁没有给 4090 D 增加哪怕 1 Byte 的显存带宽或 PCIe 带宽。Strata 的架构是一部分专家放显存，其余专家放内存由 CPU 计算，两边重叠流水线。瓶颈一直卡在显存吞吐和跨总线数据搬运上。按 Amdahl 定律，加速一个耗时占比极小的浮点环节，整体吞吐不会有任何起色。

## 跑分验证：解锁到底快没快

### 社区实测：48GB 4090 受控对比（0.98x ~ 0.99x）
社区已有研究者在改装 48 GB 的 4090 上，针对同款 Strata 引擎与 IQ3_S 模型做了严格的[受控测试](https://github.com/JustAResearcher/gpu-unlock-ada/blob/d28c485418c3d9d034cd4bac19200bc33dd3453b/docs/evidence/rtx4090-48g-modded/serving-workload.md)：

| 预填充场景 | 原厂 token/s | 解锁 token/s | 解锁 / 原厂加速比 |
|---|---:|---:|---:|
| 8K 输入 | 3518.8 | 3457.8 | **0.983×** |
| 32K 输入 | 3916.6 | 3890.3 | **0.993×** |

长输入 Prefill 下解锁不仅没有提升，甚至还在测量噪声内微跌。Decode 阶段的速度同样在正常抖动范围内，测不出稳定正收益。

### 本机日常服务快照
本机 Strata 0.1.48 在真实请求下的统计也能印证：

| 指标 | 解锁窗口 (82 请求) | 原厂窗口 (39 请求) |
|---|---:|---:|
| 生成 token 总量 | 60,707 | 25,163 |
| 加权生成速度 (token/s) | 126.34 | 141.14 |
| 生成速度中位数 (token/s) | 130.6 | 142.2 |
| 加权预填充速度 (token/s) | 1775.79 | 2170.54 |
| 前缀复用比例 | 94.02% | 82.87% |
| MTP 草稿接受率 | 68.05% | 72.58% |

{{< alert icon="triangle-exclamation" cardColor="#fef3c7" iconColor="#d97706" textColor="#b45309" >}}
真实自然流量里各请求长度与缓存命中率不同，不能当成严格受控的 A/B 组来看。但它至少说明：**原厂倍率完全能跑出当前这个水平，解锁并不能带来任何可感知的加速。**
{{< /alert >}}

## 哪些场景才能吃满这部分算力

解锁既然对量化 MoE 推理不灵，那多出来的 Tensor 算力用在哪里才实在？

1. **全精度 / 半精度微调与训练 (LoRA / SFT)**：大量矩阵乘法走 FP16/BF16 输入与 FP32 累加，算力利用率高，直接受益。
2. **图像与视频扩散模型 (Stable Diffusion / Flux / CogVideoX)**：去噪网络纯跑高密度浮点 GEMM，且模型整卡常驻，加速立竿见影。
3. **原生半精度（如 BF16）且 Batch 较大的 Dense 模型推理**：算力受限（Compute-bound）而非访存受限（Memory-bound）的场景才能体现优势。

## 稳定性与数据归档

日常使用中曾遇到过一次 `Xid 79: GPU has fallen off the bus` 掉卡。切回原厂倍率后也复现了一次，确认掉卡跟解锁没有直接因果关系，多半由供电瞬变、驱动或自定义内核（`7.3.0-ros2go-btf`）引起。目前显卡已切回原厂倍率日常跑着。

后续我整理了一套固定 Prompt 脚本，用于同一前缀与缓存状态下的复测。原始脱敏数据与复算脚本在附件里：
- [脱敏请求计时 CSV](/downloads/tensor-unlock-moe/requests.csv)
- [统计与测量说明 JSON](/downloads/tensor-unlock-moe/summary.json)
- [离线校验脚本 verify.py](/downloads/tensor-unlock-moe/verify.py)
- [校验说明与 Checksum](/downloads/tensor-unlock-moe/README.md)
