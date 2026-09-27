---
title: "两台 DGX Spark 跑 Agent：跑分一时爽，干活卡成狗"
slug: "dgx-spark-agent-inference"
date: "2026-09-27T08:25:00+08:00"
tags: ["dgx-spark","llm","inference","agent"]
description: "把 MiMo-V2.6-Flash 搬到两台 DGX Spark 上跑推理，短 Prompt 压测 6 并发总吞吐能到 173 token/s；但换到真实多 Agent 扫工程代码场景，单路直接暴跌到 15–25 token/s，跑满 6 分钟连一个子任务的完整结果都没吐出来。"
---

网上到处都是两台 DGX Spark（GB10）跑大模型的压测视频，标题一个比一个唬人，动辄「170+ token/s 吞吐」「把数据中心搬上桌面」。

前几天我也把两台 Spark 拿 QSFP 铜缆直连，照着网上的双机配方把 `MiMo-V2.6-Flash`（TP=2）拉了起来。但我折腾这套环境不是为了测 Hello World，纯粹是想知道：**这玩意儿到底能不能接进我日常的 Coding Agent 里当主力模型用？**

直接说结论：**单人一问一答还能凑合，想开多 Agent 协同或者重度扫代码，劝你趁早死心。**

---

## 先泼盆冷水：别被 200G 网口和跑分骗了

很多人看到机器上两个 200G 的网口，第一反应就是「双线聚合 400G，机间通信起飞」。

实际拿 `ethtool` 和 `lspci` 一看就露馅了：

1. **机间带宽物理上限就 200 Gb/s**：两台机器没有机间 NVLink，也没接交换机，靠两条 QSFP 铜缆直连。虽然 `ethtool` 里协商速率是 `200000Mb/s`，但每块 ConnectX-7 在主板上只分到了 PCIe Gen5 x4（`32GT/s, Width x4`）。单向物理带宽算下来顶天也就 126 Gb/s：
   
   `32 × 4 × (128/130) ÷ 8 ≈ 15.8 GB/s ≈ 126 Gb/s`

   拿 `ib_write_bw` 实测，单线打满 99.7 Gb/s，双线同时跑是 97.9 + 97.9 ≈ 196 Gb/s。
2. **访存带宽才是真正的死穴**：DGX Spark 用的统一内存是 128 GB LPDDR5X，带宽只有 **273 GB/s**。
   对比一下主流设备：
   - RTX 4090：**1008 GB/s**（可惜显存只有 24 GB）
   - Mac Studio M4 Max：**410–546 GB/s**
   - Mac Studio M3 Ultra：**819 GB/s**

Spark 的卖点从来都是「统一内存够大」，不是「访存带宽够高」。200G 的网线只够保证把大模型切成 TP=2 装进两台机器，至于解码速度，照样被 273 GB/s 的内存带宽死死摁住。

---

## 跑分看着很猛：短 Prompt 压测

先用脚本做常规的基准压测：固定 128 token 短 Prompt，打开 `ignore_eos`，测不同并发下的总吞吐：

| 并发数 | 总吞吐 (token/s) | 耗时与单路情况 |
| :--- | :---: | :--- |
| **1** | 37.1 | 单路解码约 43.8 token/s |
| **2** | 73.6 | 吞吐基本翻倍 |
| **4** | 127.4 | 多路扩展性尚可 |
| **6** | **172.7** | 总吞吐峰值，整批耗时 4.5s |
| **8** | 79.8 | 墙钟拉到 12.8s，单路散在 10–47 token/s |

从表上看，6 并发是高点，合计 172.7 token/s。到 8 并发，合计掉到 79.8，单路也散了，没有看到调度器报错。单路空载最快能摸到 54 token/s；平时一个人单聊、系统 Prompt 能吃上 90% 前缀缓存的时候，生成大约在 35–45 token/s。

这也是为什么网上很多评测动不动就吹「170+ token/s」——因为他们测的全是这种几百字节的空载短请求，大家各自解自己的 token，各走各的，互不干扰。

---

## 真实上工：5 个子 Agent 扫项目直接原地卡死

测完跑分，我把它挂进常用的 Coding Agent 里，上来就开了 5 个子 Agent 去探索一个中型开源项目的代码库。

后台监控看上去一片健康：HTTP 请求全是 200，排队数是 0。

但从终端这边一看就露馅了：**单路生成速度一下子掉到 15–25 token/s，整整跑了 6 分钟，连一个子 Agent 的总结都没吐完。**

这次会话里对得上的数就这些：请求是 200，排队是 0，每路 15–25 token/s，六分钟没有最终结果。另外一次两路同时解码，合计大约 65–75 token/s，每路大约 30–37。短测的 173 是 128 token、`ignore_eos` 的合计，和这次不是同一种输入。

长预填是另一次观察，不是这次五路的日志。大约 25 万 token 的预填可以自己占掉几分钟，并且会把同一段统计里的生成速度拉低。这次没有记下每路的输入长度，也没有记下前缀命中率。单人聊天大约 90% 的命中来自重复的系统提示；子 Agent 各读各的文件，命中会低，这是推断，不是这次量出来的。

---

## 别人的双机记录也在这个区间

公开的 GLM-5.3-Flash NVFP4，双机单路大约 20–30 token/s，四台大约 36。显卡从 1500 MHz 拉到 2100 MHz，解码大约多 4%，这是三台那篇，不要和四台的 35.7 算成同一次。标题写 43.4 的那篇，正文中位数是 21.8。六十多 token/s 来自更低比特的 EXL3，加上结构化输出和短上下文。DeepSeek V4.1 Flash 的正式权重按四台配方在跑；两台 EXL3 的目录有了，仓库标的是还没跑分。每条数字的链接在文末。

---

## 彩蛋：换成魔改卡，总账真算得过来吗

肯定有人想问：同样的预算，买魔改卡不香吗？先别急着掏钱——裸卡只是个开头，配套的流水账还在后头：

- **魔改 RTX 4090（48G）**：单卡 1008 GB/s，带宽是 Spark 的三倍还多。但这是一张卡，不是一台机器，板 U、内存、千瓦电源、机箱散热都得配齐，2026 年内存是什么价大家心里有数。而且你得先有台能插卡的机器——本来就攒着台式机的另说，那确实等于白捡。
- **魔改 RTX 5090（96G）**：速桥在阿里巴巴的报价是 3888 美元，只是裸卡价。报道同时指出商品页把显存写成 GDDR6X 14Gbps，和 96GB 对不上，第一批质量没有第三方拆机兜底。[cnBeta](https://www.cnbeta.com.tw/articles/tech/1577618.htm)，[Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/china-modified-nvidia-rtx-5090-with-massive-96gb-of-memory-appears-on-alibaba-for-less-than-usd4-000-3x-more-vram-at-65-percent-the-cost-of-the-original)
- **两台 Spark**：不用装机。NVIDIA 标的是整机电源 240W、GB10 芯片 TDP 140W，还带原厂保修。128 GB 内存折在整机价里。

带宽差是规格页上的。整机和裸卡加板 U、内存、电源的总账，我没有列价，这里比不出谁更便宜。

---

## 总结：这玩意儿到底该怎么用？

如果你手里也有两台 DGX Spark，我对它的定位建议是：

- **可以用的场景**：单人、一问一答、单任务写代码。配合稳定的系统 Prompt 和高命中率的前缀缓存，35–45 token/s 属于勉强能用的状态，至少不依赖云端 API（当然，前提是你的代码和数据敏感到根本不能出本地，否则犯不上受这个罪）。
- **天然契合的场景**：富哥（或接商单的博主）买来当大玩具发评测、刷跑分视频。摆在桌面上既有极客感又有牌面，跑个短 Prompt 压测录个屏，数据好看得很。
- **千万别指望的场景**：丢给多 Agent 当后端、大代码库整仓分析、重度并发长任务。一上这种负载，LPDDR5X 的访存带宽和长上下文 Prefill 耗时会立刻教做人。

继续堆机器，解决的只是**「能不能把模型装进内存」**，根本改变不了**「单路解码就是很慢」**的物理事实。别拿短 Prompt 跑分忽悠自己，在真实的 Agent 负载下，物理瓶颈从来不会说谎。

## 来源

本文自己的数，和别人帖子里的数分开。

**这两台机器，2026 年 9 月测的，没有对外日志。** MiMo 用的是 [tonyd2wild 的双机配方](https://github.com/tonyd2wild/MiMo-V2.6-Flash-DGX-Spark-Recipe)，TP=2，`mimo-v2.6-flash`，`max_model_len` 30 万，`max_num_seqs` 8，服务在头节点 `:8888`。短 Prompt 表是本机打的 128 token、`ignore_eos`。五子 Agent 是同一次服务上的真实会话：没有排队，每路大约 15–25 token/s，六分钟没有最终结果。`ethtool` 两条口都报 `200000Mb/s`、Direct Attach Copper；`lspci` 两条都是 PCIe Gen5 x4（`32GT/s, Width x4`）。126 Gb/s 是用这个链路参数算的：`32 × 4 × (128/130) ÷ 8`。`ib_write_bw` 一条大约 99.7 Gb/s，两条同时大约 97.9 + 97.9。

**规格页，不是实测速度。**

- DGX Spark 内存带宽 273 GB/s、128 GB LPDDR5X、电源 240W、GB10 TDP 140W：[NVIDIA 规格](https://www.nvidia.com/en-us/support/dgx-spark.md)
- RTX 4090 显存带宽 1008 GB/s、24 GB：[NVIDIA GeForce](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/)。48G 是魔改容量，带宽数字仍是这张原卡的规格，没有一份统一的 48G 规格书。
- Mac Studio：M4 Max 410 GB/s，40 核 GPU 那一档 546 GB/s；M3 Ultra 819 GB/s。[Apple 技术规格](https://www.apple.com/mac-studio/specs/)

**社区跑分。** 升频大约 4% 来自三台那篇，四台 35.7 是另一篇。

- 双机 NVFP4，正文中位数 21.8 token/s，峰值 22.7；标题写 43.4。同一篇末尾四台 TP4 是 35.7。[NVIDIA 论坛](https://forums.developer.nvidia.com/t/glm-5-3-flash-on-2x-nvidia-dgx-spark-43-4-tok-s-peak-checkpoint/381429)
- 另一组双机：代码 24.7，结构化 30.3，散文 19.6；关掉推测解码 14.6。单路、temperature 0。[论坛](https://forums.developer.nvidia.com/t/glm-5-3-flash-running-on-2x-dgx-spark-sm-121-day-0-24-7-30-3-tok-s-with-mtp-5-two-silent-gb10-gotchas-worth-knowing/381433)，[配方](https://github.com/kingjones30/GLM-5.3-Flash-2x-DGX-Spark)
- 三台 TP3：1500 MHz 解码 35.2，2100 MHz 是 36.8。大约 16 万 token 上下文时，2 路每路 7.5，3 路每路 6.1。[NVIDIA 论坛](https://forums.developer.nvidia.com/t/glm-5-3-flash-nvfp4-on-3x-dgx-spark-tp-3-512k-context-35-tok-s/381534)
- 双机 EXL3 4bpw：结构化单路 62.9，散文中位数 26.9。[MiaAI](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks/blob/main/README.md)
- 单机 EXL3 2.05bpw：结构化大约 64，散文大约 25。跟帖提到空转和质量问题。[论坛](https://forums.developer.nvidia.com/t/60-tok-s-glm-5-3-flash-on-a-single-dgx-spark/382140)，[模型卡](https://huggingface.co/gitcommit90/GLM-5.3-Flash-EXL3-2.05-One-Spark)
- DeepSeek V4.1 Flash 四台环网，单路大约 43–50 token/s。[记录](https://github.com/yunwei37/dgx-spark-4-ring-no-switch/blob/main/docs/deepseek-v41-flash.md)。另一篇四台帖的散文是 23 token/s。[论坛](https://forums.developer.nvidia.com/t/deepseek-v4-1-flash-552b-moe-on-4x-dgx-spark-tp4-77-2-tok-s-c1-on-peak-52-code-72-tok-s-on-a-warm-code-run-47-math-39-reasoning-23-prose/382897)。两台 EXL3 标成未跑分；四台 EXL3 散文 30.2、代码 33.4。[配方](https://github.com/vcruz305/DeepSeek-V4.1-Flash-EXL3-DGX-Spark-recipe)
