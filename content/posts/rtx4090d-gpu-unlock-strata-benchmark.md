---
title: "RTX 4090 D 解锁实测：Tensor 吞吐翻倍，Strata 推理重测"
slug: "rtx4090d-gpu-unlock-strata-benchmark"
date: "2026-10-25T08:30:00+08:00"
tags: ["gpu", "nvidia", "llm", "inference", "strata", "qwen"]
description: "实验基线尚未接入 RTX 4090 D；补齐 2685 型号分派后，两次重启验证成功，GEMM 提升 28%～90%，并重测 Strata 推理速度。成稿时交叉核对社区新报告，确认该仓库已另行合入 4090 D 支持。"
---

[上一篇]({{< relref "qwen38-flash-next-strata-4090.md" >}})给家里的 RTX 4090 D 配上了 Strata，一直拿它跑 Qwen3.8-Flash-Next。这次看到 [gpu-unlock](https://github.com/Zagitta/gpu-unlock)，想试试这张卡能不能用，实际推理又能快多少。

开始实验时，普通 4090 已经有社区 AD102 实现，选定的基线还没接入 4090 D。10 月 24 日让 AI 助手补完适配，在这台机器上跑了解锁、数值校验和性能对照，随后又测了一轮现有 Strata 服务。

## 4090 和 4090 D 的型号分派

这张卡的 PCI ID 是 `10de:2685`，芯片是 Ada AD102，有 114 个 SM、24 GB 显存。系统是 Ubuntu 24.04.4 LTS，实验全程固定内核 `6.17.0-1032-oem`，驱动用原来的 NVIDIA `595.58.03 open`，功耗上限保持 425 W。Secure Boot 当时已经关闭。

查支持范围要看具体分支。最初只看了 Zagitta 的 main，里面是 Ampere 的 GA102、GA103、GA104、GA106，后来继续查分支和 fork，找到了 [elias-gaeros 的 rtx4090 分支](https://github.com/elias-gaeros/gpu-unlock/tree/4ec490d49c1cc292c0b4cd5ce5a801b5d2c396dc)和 [JustAResearcher/gpu-unlock-ada](https://github.com/JustAResearcher/gpu-unlock-ada/tree/491925c1079435e260137b9f3526066e764de830)。这里说的 main，是检查时的[固定提交](https://github.com/Zagitta/gpu-unlock/tree/4189b17711bd487d9ea4a8ff0055e6d58d19d6d3)。

普通 4090 的设备号是 `2684`，检查的两个社区提交都已经接入；当时都还没有 4090 D 的 `2685`。本次以 JustAResearcher 的固定提交为基础，补丁改了几个相互关联的位置：设备准入、AD102 固件选择、`is_ad102()` 架构判断，以及对应的主机测试。只在白名单里加一个设备号，会选到 GA102 固件路径。

新型号还加了一个显式开关 `ad102d_experimental=1`。它要求 `targets` 恰好等于一个完整 PCI 地址，拒绝 `all` 和逗号分隔的多个目标。本机目标是 `0000:01:00.0`，补丁的实验范围就限定在这张卡。

解锁使用的固件资产版本为 `610.43.03`，后面加载的 NVIDIA 驱动仍是前面那版。这次也没有刷写 VBIOS。

## 用独立入口启动

解锁模块要在 NVIDIA 驱动之前加载，而这台机器正在跑 Strata，不能直接往已经被驱动占用的卡上插模块。测试先短暂停服务，保存未解锁的 rates、数值校验和计算基线，再恢复服务，准备下一次启动。

机器的根分区是 Btrfs，默认启动内核已经比当前运行内核新一版。为了让前后对照用同一个内核，单独复制了实验内核和 initramfs 到 EFI 分区，新增一个测试入口，用 UEFI `BootNext` 只选下一次启动，原有默认顺序保留。

实验 initramfs 把模块、固件和加载脚本放在一起，在原有 init-top 脚本之前执行。关键加载参数是下面这一行；它运行在早期启动阶段，目标地址是本机的值：

```sh
insmod /gpu_unlock-4090d.ko targets=0000:01:00.0 ad102d_experimental=1
```

第一次普通重启之后，日志记录了 selector 写入、PCI function-level reset（FLR）后的读回，以及模块解锁成功。随后原版驱动正常加载，只读 rate 查询中的 `fmla32`、`imla2`、`imla4` 从 `1` 变为 `0`；这个接口里前者表示半速，后者表示全速。

启动过程中还碰到一个 systemd 细节。第一轮为了避免模型自动占满显存，在内核参数里加了 `systemd.mask=strata.service`。这个 mask 来自 generator，执行 daemon-reload 会重新生成，单靠 `systemctl unmask --runtime` 解除不了。第二轮去掉这个内核参数，再选同一个测试入口重启，解锁再次成功，Strata 也从原来的 unit 自动启动，健康检查返回模型已加载。

两次都是普通重启，没有做断电冷启动，也没跑长期稳定性负载。第二次启动后的模型服务恢复和 rates 已复核；原启动路径的恢复重启留在后面说明。

## 计算吞吐和数值校验

rates 变了，还得看真正执行的计算。解锁前后用同一份基准二进制、相同功耗上限测 cuBLAS GEMM：方阵边长 8192，每种模式采 5 个样本，每个样本跑 20 次迭代，表里取吞吐中位数。FP16、BF16 两项都使用 FP32 累加。

| GEMM 模式 | 解锁前 TFLOPS | 解锁后 TFLOPS | 提升 |
|---|---:|---:|---:|
| FP16 → FP32 | 152.83 | 195.96 | 28.22% |
| BF16 → FP32 | 153.81 | 250.97 | 63.16% |
| TF32 | 76.49 | 145.55 | 90.28% |
| 普通 FP32 对照 | 54.27 | 54.71 | 0.80% |

再看 MMA 指令微基准。这里使用同一配置下 3 次测量中的最佳吞吐，统计口径和上面的 GEMM 不同。

| MMA 模式 | 解锁前 | 解锁后 | 单位 |
|---|---:|---:|---|
| FP16 / FP32 累加 | 145.1 | 291.5 | TFLOPS |
| BF16 / FP32 累加 | 145.0 | 289.6 | TFLOPS |
| FP16 / FP16 累加 | 290.3 | 291.6 | TFLOPS |
| INT8 / INT32 累加 | 579.7 | 579.6 | TOPS |
| dp4a | 144.1 | 144.1 | TOPS |
| scalar FFMA | 68.8 | 68.9 | TFLOPS |

变化集中在 Tensor 的 FP32 累加路径，FP16 累加和整数对照基本保持原样。独立 tensor cubin 基准也测到了 TF32 吞吐约翻倍，INT4 基本不变。实际 GEMM 的幅度随数据类型变化，不能把某条指令的翻倍直接套给整段程序。

数值校验也在解锁前后各跑了一遍。FP16、BF16 的 FP32 累加 GEMM 每项核对 65536 个元素，都是 `failures=0`、`max_abs=0`；独立 cubin 的 FP16、TF32、INT4 每项核对 270336 个元素，都是 `mismatches=0`。这些结果覆盖了本次基准的输入和精度模式。

主机 unittest 共 22 项，19 项通过，3 项离线解密测试因未安装可选 PyCryptodome 而跳过。模块针对固定内核以 `KCFLAGS=-Werror` 编译通过，两轮启动日志未发现 NVIDIA Xid、GPU fallen off bus 或 kernel Oops/BUG。性能表来自一组解锁前后测量，第二次重启复核了解锁和服务状态，没有重跑整套计算基准。

## 社区新提交的交叉验证

成稿时又核对了 JustAResearcher 仓库的[新提交 `4e7fefcc`](https://github.com/JustAResearcher/gpu-unlock-ada/tree/4e7fefcc4923f9e083d5324dc75a7d2f906af77f)。它已合入 [4090 D 支持 PR #7](https://github.com/JustAResearcher/gpu-unlock-ada/pull/7)，设备准入、固件选择和架构判断都走 AD102。这个版本用 `rtx4090d_experimental=1`，开启后允许多卡选择；本次实测补丁保留前面的开关名和单卡限制，附件也固定在原基线，不能把两套参数混用。

[PR #1 的普通 4090 成对报告](https://github.com/JustAResearcher/gpu-unlock-ada/blob/4e7fefcc4923f9e083d5324dc75a7d2f906af77f/docs/evidence/rtx4090-pr1-matched/README.md)提供了原始计时和数值结果：FP16、BF16 的 FP32 累加指令吞吐分别从 160.4、159.7 TFLOPS 升到 320.4、320.2 TFLOPS，FP16 累加和整数对照基本不变。重新计算其 GEMM 日志，8192 方阵的两项收益约为 12% 和 16%；[普通重启复测](https://github.com/JustAResearcher/gpu-unlock-ada/blob/4e7fefcc4923f9e083d5324dc75a7d2f906af77f/docs/evidence/rtx4090-pr1-matched/warm-reboot-repeat/README.md)仍有接近翻倍的指令吞吐，4096 方阵的 BF16 GEMM 却比原基线慢约 8%。这些结果与本机受益的指令路径一致，也说明应用收益要按负载测。两边的卡、驱动、CUDA 和矩阵输入不同，百分比各自保留。

4090 D 也有[独立用户报告](https://github.com/JustAResearcher/gpu-unlock-ada/pull/7#issuecomment-6390126655)：八卡节点上，单卡前后对照约从 148 升到 296 TFLOPS，随后八卡重启均解锁成功，数值检查通过；现有 ComfyUI 工作流耗时缩短约 11%。这条是贡献者的文字报告，没有附原始日志，证据完整度低于上面的普通 4090 数据集。

新版本还合入了加载时固件哈希校验、带随机种子的多形状数值测试，以及 MMA 重复测量存储修复。本机的解锁和基准测试使用了此前代码，文章中的硬件结果仍对应原补丁与固定基线；公开数据说明另记了上游数据清单的一处换行符问题。

## Strata 的当前速度

计算测完，接着向现有服务发真实模型请求。这时 Strata 已经是 `0.1.47`，模型仍是官方 GSQ-RCO IQ3_S 量化的 Qwen3.8-Flash-Next，最大上下文 262144，KV 用 int8，每层常驻 32768 个 cell。专家缓存自动分配，运行时是 8548 个槽、16599 MiB。

这轮保留原有启动配置：`--spec 4`、`--spec-min-p 0.5`、CJK draft 词表和 fused prefill。引擎能力字段另报 `spec=6`、`mtp_max=4`，与启动参数分别记录。测量期间没有改配置、换引擎或重启服务。

先做一次不计入结果的预热，再测 5 种输入和输出长度，每种跑 3 次，共 15 条正式请求。服务一次处理一条，请求关闭 thinking，用 greedy 采样。每条输入开头放不同的编号，并逐条核对 `cached_tokens=0`、`cache_n=0`，避免上一次的 KV 前缀复用进来。

这里的冷 prefill 指 KV 前缀没有命中。模型已经加载，专家缓存会随请求预热，没有在每轮之间清空；首轮长代码输入也保留在样本里。中等长度的中文材料由脚本生成，长代码取自当时 Strata 服务端源码，测的是这些输入下的推理速度。

| 输入 / 输出 token | 内容 | prefill token/s | decode token/s | 首 token 秒 | 整次请求秒 |
|---|---|---:|---:|---:|---:|
| 95 / 256 | 短中文请求 | 252.1 | 134.8 | 0.390 | 2.279 |
| 2060 / 256 | 约 2K 中文材料 | 985.6 | 137.3 | 2.104 | 3.959 |
| 8204 / 256 | 约 8K 中文材料 | 3365.2 | 144.6 | 2.454 | 4.213 |
| 120 / 1024 | 持续中文长输出 | 284.4 | 137.8 | 0.440 | 7.851 |
| 32784 / 512 | 约 32K 源码审查 | 3421.9 | 129.0 | 9.616 | 13.571 |

表里每列各取 3 次的中位数，未必来自同一次请求。输入 token 包含 chat template；prefill、decode 使用服务端原生 token 计数和对应阶段耗时，首 token 与整次请求时间由客户端单调时钟测量。被主模型拒绝的 draft token 不计入输出吞吐，长输入的 prefill 时间也不算进 decode。

持续长输出几轮的生成速度接近，长代码输入的第一轮稍慢。短输入的 prefill 主要受固定开销影响，评估长上下文要看后面的长输入行。所有正式请求都返回 HTTP 200 和完整 SSE 结束标记，API 输出数、引擎生成数与计时字段一致，生成到指定 token 上限后结束；本轮没有评估回答质量。

## 和旧文的速度记录对照

旧文最后一轮使用升级后的引擎，让 5 个 subagent 看项目，统计了一批代码请求；这次单独补长源码审查，是为了让输入长度落在当时的长 prefill 分组内。下面只用旧文后半段的那批对照数据，未混入开头更早的 IQ3_S 汇总。

| 指标 | 旧文 v0.1.39，未解锁 | 本次 v0.1.47，解锁状态 | 观察差值 |
|---|---:|---:|---:|
| 代码相关 decode 中位数 | 106.9 token/s | 129.0 token/s | +20.67% |
| 长输入冷 prefill 中位数 | 2900 token/s | 3421.9 token/s | +18.00% |

旧文 decode 来自整段代码工作流，长 prefill 取未复用的 20K～40K token 请求，共 16 条；这次每种输入只有 3 条，输入文本、生成长度和采样设置也不相同。MTP 接受率以及专家缓存命中情况都有变化，加上中间升级了引擎，表里的差值包含这些因素。

所以现在能确认这张卡的部分 Tensor 路径确实恢复了吞吐，也有了当前模型服务的速度记录。解锁对模型推理的单项贡献，还需要固定同一引擎、同一输入和配置，再做锁定与解锁的 A/B。

## 补丁、数据和恢复入口

[4090 D 适配补丁](/downloads/rtx4090d-gpu-unlock/rtx4090d.patch)基于上面固定的社区提交，仍是本次本地实验修改。附上 [GEMM 基准源码](/downloads/rtx4090d-gpu-unlock/gemm_bench.cu)、[15 条推理记录 CSV](/downloads/rtx4090d-gpu-unlock/inference-runs.csv?v=f2a4f3653ed8)和[完整数据包](/downloads/rtx4090d-gpu-unlock-data.tar.gz)；[数据说明](/downloads/rtx4090d-gpu-unlock/README.md)列出了计算日志、rates、启动日志节选、JSON 计时字段和文件哈希清单，可以重新汇总表中的结果。附件没有打包固件和模块二进制，固件来源及许可证仍按基础仓库处理。

实验结束时，机器运行在第二次选中的测试入口里，Strata 正常、模型已加载、rates 全速。`BootNext` 已经消耗，默认启动顺序没改，也没有设置默认开机解锁。

要再次选实验入口，需要先读 `efibootmgr -v` 核对标签和编号，再设置下一次启动。要回原路径，则确认没有待执行的测试 BootNext；如有，用 `efibootmgr --delete-bootnext` 取消，再正常重启。入口编号由各台机器分配，不能照搬这台机器的值。回原路径后还要重读 rates，才能确认半速是否恢复，必要时再断电启动。本次没有执行这段恢复重启，断电后的状态也没验证。

这套测试镜像绑定了本次内核与模块，更换内核需要重建并重新验证。暂时保留独立启动入口，按需选择。
