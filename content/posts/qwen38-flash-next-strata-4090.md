---
title: "4090 24G 本地部署 Qwen3.8-Flash-Next：从 Ollama 换到 Strata"
slug: "qwen38-flash-next-strata-4090"
date: "2026-10-04T13:24:00+08:00"
tags: ["llm", "inference", "strata", "qwen"]
description: "Ollama 上的 Qwen3.8 27B 把 4090 显存占满，代码分析时生成断崖式地慢。换成 Strata 跑 Qwen3.8-Flash-Next MoE 后，256K context 照样开得住，代码分析场景 decode 中位大概 100～110 tok/s。"
---

家里这台机器主板是微星 Z790 GAMING PLUS WIFI。CPU 是 i9-14900KF，8 个 P-core、16 个 E-core，32 线程，P-core 睿频最高 6.0 GHz，E-core 最高 4.4 GHz，指令集到 AVX2，没有 AVX-512。内存是 4 条 32 GB DDR5，威刚 XPG `AX5U6000C3032G`，标称 DDR5-6000 CL30，双通道，每条 dual rank；实际频率是 4000 MT/s，系统里看到大约 125 GiB。显卡是 RTX 4090 D 24 GB。

之前一直用 Ollama 跑 `qwen3.8:27b-q4_1`，权重大约 17 GB，加上 KV 显存要到 22 GB 左右，context 也能开到 256K。短回复还能用，代码分析这种长生成基本是断崖式地慢。

Qwen3.8-Flash-Next 是 512 个 expert 的 MoE，BF16 权重三百多 GB，但每个 token 只激活其中一小部分。官方量化用的是 ISTA-DASLab 的 GSQ-RCO，推理引擎我选了 [Strata](https://github.com/Niko1221/Strata)，它能把 expert 放在内存里，只在显存里缓存常用的那部分，正好适合 24 GB 显存配大内存的机器。

换完的效果：同一张 4090 D，decode 中位数大概 100～110 tok/s，两三万 token 的冷 prefill 在 2500～2800 tok/s，context 开到训练长度 262144。代价是服务同时只能跑一条请求。

内存和显存大致是这么分的：

{{< mermaid >}}
flowchart LR
  subgraph host["内存 126 GB"]
    E["Experts 约 45～50 GB"]
    KV["超出 32K 的 int8 KV<br/>约 3.09 GiB 锁页内存"]
  end
  subgraph gpu["4090 D 24 GB"]
    C["常用 expert 缓存 约 16 GB"]
    R["每层 QSA 常驻 32768 个 KV cell"]
  end
  Req["OpenAI / Anthropic 协议请求"] --> S["Strata serve :8080"]
  S --> C
  S --> E
  S --> R
  S --> KV
{{< /mermaid >}}

## 选哪档量化

Strata 的 `./setup.sh --yes` 只按内存选档，60 GB 以上默认装 GSQ-RCO `IQ3_XXS`。文档里又写着 64 GB 的机器推荐 `IQ2_XS`，96 GB 以上推荐 `IQ3_S`，这台 126 GB 的机器按安装器会装 XXS，按文档应该用 S。

可这台机器的瓶颈在显存。24 GB 里只放常用的 expert，三档量化都能整个装进内存，256K context 也都开得了。CPU 方面，14900KF 只有 AVX2，没有 AVX-512，`Q2_0` 用不上 Strata 最快的那套 CPU kernel，这档就没考虑。

我先试的是 Unsloth 的 `UD-IQ3_XXS`，魔塔上能直接下，大约 76 GB。后来又换成官方 GSQ-RCO 的 `IQ3_S`，两个分片共 83.6 GB，下完核对过 SHA-256。Ollama 的模型文件留着没删，只是在 `strata.service` 里配了 `Conflicts`，开机后不会两边抢 GPU。

## 部署时遇到的几个问题

### Linux 自己编译到 0.1.38

Strata 0.1.35 和 0.1.36 的 GitHub Release 里都只有 Windows 包，0.1.38 也还是只有 Windows NVIDIA 和 Windows HIP 两个包，没有 `strata-linux-x64.zip`，只能自己编译。这台机器现在跑的引擎是本地编的 0.1.38，环境是 CUDA 12.0、g++ 13.3，arch 指定 `sm_89`，二进制在 `engine/strata`。

服务交给 systemd 管，监听 `0.0.0.0:8080`，`/v1/*` 需要 API key。接口支持 OpenAI Chat Completions 和 Anthropic Messages，没有旧的 `/v1/completions`，也没有 embeddings。请求按 FIFO 排队，同一时间只处理一条。

### Unsloth 包的 embedding 格式引擎不认

官方安装器只认 ISTA 那几档的文件名，Unsloth 的 `UD-IQ3_XXS` 会被 `gguf_unsupported()` 直接拒掉。不过看了下，shard 里 expert 用到的 IQ2_S / IQ3_S / IQ4_NL，CUDA kernel 都支持，真正的问题出在 `token_embd.weight`：Unsloth 存的是 Q6_K（ggml type 14），而 Strata 的 embedding 只支持 i-quant 或 BF16。

解决办法是用 llama.cpp 的 gguf-py 把这个 Q6_K 张量反量化成一份单独的 BF16 文件，再通过 `--embd-gguf` 指给引擎。header 里的 `ne` 要写成 `(2560, 248320)`，跟引擎期望的 layout 对上。output head 同样是 Q6_K，但它走的是原生 mmvq，不用转。

另外，MTP 的 draft 头从 Qwen 官方 BF16 权重里取出来，打包成 `mtp/rt`，启动参数加 `--spec 4`，CJK 的 draft 词表也拷到同一个目录下。

### context 从 128K 拉到 256K

24 GB 显存的卡，setup 默认给的是 `--max-context 131072`。模型训练长度是 262144，超过这个才需要 YaRN，所以我直接拉到 262144，同时加上 `--kv int8 --kv-resident 32768`：每层 QSA 只在显存里保留 32K 个 KV cell，多出来的部分放到锁页内存，大约 3.09 GiB。这样显存稳定在 23900 MiB 左右，从 128K 换到 256K 几乎没涨。

单次生成长度没有单独设上限。请求里不传 `max_tokens`，或者传 0 / -1，就会一直写到 `262144 − 8 − prompt 长度`，thinking token 也算在里面。

### 关掉 zram

服务跑起来后内存占了 65 GB 左右，还剩 60 GB，模型进程的 `VmSwap` 是 0，看着没什么问题。但系统里 `zramswap.service` 开着，62.8 GB 的 lz4 压缩区，`vm.swappiness=100`。expert 所在的内存页没有 mlock，内存一紧张就可能被压进 zram，之后遇到 expert miss，得先解压才能算。

这台机器本来就没有磁盘 swap，内存余量也够，我就执行了 `systemctl disable --now zramswap`。真到内存不够的时候，直接 OOM 也比推理到一半去解压更好排查。

### fused prefill kernel

0.1.36 的 Release 说明提到，Q2_0 的 fused int8 tensor-core prefill 在 5070 上能快 16%～22%；IQ2_XS / IQ3_XXS / IQ3_S 要设置 `STRATA_PF_FUSED=1` 才会走这套 kernel，官方默认关闭，理由是 IQ3 上几乎没有提升。

我还是打开了。实测 IQ3 的 prefill 没有明显变快，decode 也没变慢，就一直开着。打开后第一次较长的冷 prefill，日志里能看到 `prompt experts on the fused int8 kernels`。

## 实测数据

下面的数字是引擎还在 0.1.36、fused prefill 已经打开时打的负载。后来升到 0.1.38，`strata-iq3_s.json` 里的参数没改，这台机器上没有重测。官方 release 里 IQ3_S 相对 0.1.37 的速度 A/B 是 +0.2% 和 +0.1%，回答和上一版一致。

先说下日志里两个容易混在一起的数。`prompt 25141 tokens = 0 reused + 25141 read` 说的是 prefix cache：reused 是前缀里已经有现成 KV 的部分，越高 prefill 越快。`drafts accepted 919 of 1329` 是 MTP speculative decoding 的命中情况：draft 头先猜，主模型再校验，命中率越高 decode 越快。代码和列表一般能到 80%～90%，普通文字大概只有一半。

还有一点，短 prompt 算出来的 prefill tok/s 参考意义不大，几十个 token 的时候固定开销占了大头，算出来只有几百 tok/s。中途取消的请求，日志里会出现上万 tok/s，那是没算完，统计时都去掉了。

两个量化版本的配置完全一样：256K context、int8 KV、resident 32768、`--spec 4`、fused 打开。UD-IQ3_XXS 统计了 107 条请求，IQ3_S 统计了 58 条，都是拿同样规模的项目开 5 个 subagent 去看代码。decode 只统计生成 50 token 以上的请求，prefill 只统计没命中前缀缓存、需要重新计算的部分在 2k token 以上的请求。

| | UD-IQ3_XXS | GSQ-RCO IQ3_S |
|---|---:|---:|
| decode p50 | 100.7 tok/s | 111.7 tok/s |
| decode p90 | 119.5 tok/s | 133.3 tok/s |
| decode 最高 | 148.2 tok/s | 147.9 tok/s |
| prefill p50（未命中 20k～40k） | 2781 tok/s | 2785 tok/s |
| prefill p50（未命中 ≥2k） | 2564 tok/s | 2549 tok/s |
| draft 命中率 | 74.9% | 71.5% |
| 整次探索 | 约 12 分钟 | 约 8 分钟 |
| 最大 context | 93057 | 56199 |
| 显存 | 约 23976 MiB | 约 23950～23978 MiB |

prefill 两边基本一样。UD 那一轮里有一次 89517 token 完全没命中缓存，prefill 用了 29.9 秒，折合 2998 tok/s，跟官方给的 3090 上 3 万 token 冷 prefill 约 2200～2900 tok/s 能对上。

换成官方 IQ3_S 之后是全面领先。decode 的 p50、p90 都更高，整次探索从大约 12 分钟收到 8 分钟。官方 5070 12GB 的表里 IQ3_S 比 IQ3_XXS 慢（53 vs 62 tok/s）。

跑起来的时候 GPU 利用率在 98%～100%，功耗 270～300 W，最高见过 346 W，显存基本贴着 24 GB。连续用的时候，大约三分之二的时间 GPU 都在算。

## 能给几个人用

服务同时只处理一条请求，`/v1/status` 里能看到 `serving: 1`，后面的请求排队。

代码分析这类请求，单条占用时间中位数在 5～9 秒，偶尔有 30～50 秒的长回答，两三个人一起用还算能接受。不过如果是 agent 连续发请求，一个人就能把队列占满。换一个大仓库、前缀缓存用不上的时候，9 万 token 光 prefill 就要 30 秒左右。

## 和 Ollama 的 27B 比

原来 Ollama 跑的 27B，我没在这台机器上重新测一组对照数据，体感上是断崖式落后，差距主要来自 MoE 的稀疏激活和 MTP，模型本身也换了。

## 和两台 DGX Spark 比

[上次]({{< relref "dgx-spark-agent-inference.md" >}})两台 DGX Spark 跑 `MiMo-V2.6-Flash`，短 prompt 单路大约 44 tok/s，6 并发合计 173 tok/s。换成真的扫代码，单路掉到 15～25 tok/s，六分钟吐不完一个子任务。那边 128 GB 统一内存带宽是 273 GB/s。24 GB 的 4090 带宽够用，模型装不进去。

Strata 把 expert 放进内存，常用的留在显存。模型不是同一个，但都是拿去扫代码，这边 decode 中位过 100。这可比 Spark 猛多了。看着 Qwen3.8-Flash-Next 在这张 4090 上跑起来，我仿佛看到了原子弹爆炸。传统软件行业真就死了。
