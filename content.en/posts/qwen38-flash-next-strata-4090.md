---
title: "Running Qwen3.8-Flash-Next on a 4090 24GB: Replacing Ollama with Strata"
slug: "qwen38-flash-next-strata-4090"
date: "2026-10-04T13:24:00+08:00"
tags: ["llm", "inference", "strata", "qwen"]
description: "Ollama’s Qwen3.8 27B filled the 4090, and code-analysis generation fell off a cliff. Strata running Qwen3.8-Flash-Next still fits a 256K context, with median decode around 100–110 tok/s on code-analysis traffic."
---

> I am not a native English speaker; this article was translated by AI.

The machine at home is an MSI Z790 GAMING PLUS WIFI. The CPU is an i9-14900KF: 8 P-cores and 16 E-cores, 32 threads, P-core turbo up to 6.0 GHz, E-core up to 4.4 GHz, AVX2 and no AVX-512. Memory is four 32 GB DDR5 DIMMs, ADATA XPG `AX5U6000C3032G`, rated DDR5-6000 CL30, dual channel, dual rank on each stick. They are running at 4000 MT/s, and the OS sees about 125 GiB. The GPU is an RTX 4090 D 24 GB.

It had been running `qwen3.8:27b-q4_1` in Ollama: about 17 GB of weights, VRAM around 22 GB once KV is included, and a 256K context. Short replies were still usable. On code analysis, long generations fell off a cliff.

Qwen3.8-Flash-Next is a 512-expert MoE. The BF16 weights are over 300 GB, but each token activates only a small slice of them. The official quant is ISTA-DASLab GSQ-RCO. I used [Strata](https://github.com/Niko1221/Strata) for inference: experts stay in RAM, and the GPU only caches the ones used often. That matches a 24 GB card with a lot of system RAM.

After the switch, the same 4090 D decodes at about 100–110 tok/s median. A cold prefill of twenty to thirty thousand tokens sits around 2500–2800 tok/s. Context is the trained length, 262144. The service handles one request at a time.

RAM and VRAM split roughly like this:

{{< mermaid >}}
flowchart LR
  subgraph host["126 GB RAM"]
    E["Experts ~45–50 GB"]
    KV["int8 KV past 32K<br/>~3.09 GiB pinned"]
  end
  subgraph gpu["4090 D 24 GB"]
    C["Hot expert cache ~16 GB"]
    R["32768 resident KV cells per QSA layer"]
  end
  Req["OpenAI / Anthropic requests"] --> S["Strata serve :8080"]
  S --> C
  S --> E
  S --> R
  S --> KV
{{< /mermaid >}}

## Which quant

`./setup.sh --yes` picks the size from RAM alone. Above 60 GB it installs GSQ-RCO `IQ3_XXS`. The docs recommend `IQ2_XS` for a 64 GB machine and `IQ3_S` above 96 GB. On this 126 GB box the installer would pick XXS and the docs would pick S.

The limit here is VRAM. The 24 GB only holds the experts that are used often. All three quants fit in RAM, and 256K context fits too. The 14900KF has AVX2 and no AVX-512, so `Q2_0` cannot use Strata’s fastest CPU kernels. I left that size out.

I tried Unsloth `UD-IQ3_XXS` first. ModelScope has it, about 76 GB. Later I switched to official GSQ-RCO `IQ3_S`: two shards, 83.6 GB, SHA-256 checked after download. The Ollama files are still on disk. `strata.service` has `Conflicts` set, so a reboot does not have both fighting for the GPU.

## Problems during setup

### Linux build, through 0.1.38

Strata 0.1.35 and 0.1.36 GitHub Releases only ship Windows builds. 0.1.38 still ships only the Windows NVIDIA zip and the Windows HIP zip. There is no `strata-linux-x64.zip`, so the engine has to be compiled locally. The 0.1.38 build on this machine used CUDA 12.0 and g++ 13.3, arch `sm_89`. The binary is `engine/strata`.

systemd runs the service. It listens on `0.0.0.0:8080`, and `/v1/*` needs an API key. The APIs are OpenAI Chat Completions and Anthropic Messages. There is no legacy `/v1/completions` and no embeddings. Requests are FIFO, one at a time.

### The engine rejects Unsloth’s embedding format

The official installer only accepts the ISTA filenames. Unsloth `UD-IQ3_XXS` is refused by `gguf_unsupported()`. The expert tensors in the shards are IQ2_S / IQ3_S / IQ4_NL, and the CUDA kernels do cover those. The actual break is `token_embd.weight`: Unsloth stores Q6_K (ggml type 14), and Strata embeddings only accept i-quants or BF16.

I dequantized that Q6_K tensor to a separate BF16 file with llama.cpp’s gguf-py and pointed the engine at it with `--embd-gguf`. The header `ne` has to be `(2560, 248320)` so it matches the layout the engine expects. The output head is also Q6_K, but it uses native mmvq and does not need the conversion.

The MTP draft head is taken from Qwen’s official BF16 weights, packed as `mtp/rt`, with `--spec 4`. The CJK draft vocab goes in the same directory.

### Context from 128K to 256K

On a 24 GB card, setup defaults to `--max-context 131072`. The trained length is 262144, and YaRN is only needed past that, so I set 262144 and added `--kv int8 --kv-resident 32768`. Each QSA layer keeps 32K KV cells in VRAM. The rest sits in pinned RAM, about 3.09 GiB. VRAM stays around 23900 MiB. Moving from 128K to 256K barely changes it.

There is no separate cap on one generation. Omit `max_tokens`, or pass 0 / -1, and it writes until `262144 − 8 − prompt length`. Thinking tokens count against that.

### Turning zram off

Once the service was up, RAM use was about 65 GB with 60 GB free, and the model process had `VmSwap` at 0. That looked fine. `zramswap.service` was still on: 62.8 GB of lz4, `vm.swappiness=100`. The expert pages are not mlock’d. If RAM gets tight they can be compressed into zram, and an expert miss then has to decompress before the multiply.

This machine has no disk swap, and the free RAM is enough, so I ran `systemctl disable --now zramswap`. If memory really runs out, an OOM is easier to read than a decompress in the middle of a generation.

### Fused prefill kernels

The 0.1.36 release notes say Q2_0 fused int8 tensor-core prefill is 16–22% faster on a 5070. IQ2_XS / IQ3_XXS / IQ3_S only take that path with `STRATA_PF_FUSED=1`. It is off by default because IQ3 barely moves.

I turned it on anyway. On IQ3, prefill did not get clearly faster and decode did not get slower, so it stayed on. The first longer cold prefill after that logs `prompt experts on the fused int8 kernels`.

## Measurements

The numbers below come from the code-analysis load taken while the engine was still 0.1.36, with fused prefill already on. The move to 0.1.38 left `strata-iq3_s.json` unchanged and was not measured again. The same task was run once more on 0.1.39; that round is in the next section. The 0.1.38 release notes put the IQ3_S speed A/B against 0.1.37 at +0.2% and +0.1%, with the same answers as the previous version.

Two numbers in the log are easy to mix up. `prompt 25141 tokens = 0 reused + 25141 read` is the prefix cache: `reused` is the prefix that already has KV, and a higher share means a shorter prefill. `drafts accepted 919 of 1329` is MTP speculative decoding: the draft head guesses, the main model checks, and a higher accept rate means faster decode. Code and lists often land around 80–90%. Ordinary prose is about half.

Prefill tok/s on a short prompt is not very useful. A few dozen tokens are mostly fixed overhead, so the rate looks like a few hundred tok/s. A cancelled request can log tens of thousands of tok/s because it did not finish. Those rows were dropped.

Both quants used the same settings: 256K context, int8 KV, resident 32768, `--spec 4`, fused on. UD-IQ3_XXS is 107 requests, IQ3_S is 58. Both runs pointed 5 subagents at a project of about the same size. Decode counts only replies of 50 tokens or more. Prefill counts only the part that missed the prefix cache and was at least 2k tokens.

| | UD-IQ3_XXS | GSQ-RCO IQ3_S |
|---|---:|---:|
| decode p50 | 100.7 tok/s | 111.7 tok/s |
| decode p90 | 119.5 tok/s | 133.3 tok/s |
| decode max | 148.2 tok/s | 147.9 tok/s |
| prefill p50 (miss, 20k–40k) | 2781 tok/s | 2785 tok/s |
| prefill p50 (miss, ≥2k) | 2564 tok/s | 2549 tok/s |
| draft accept | 74.9% | 71.5% |
| whole exploration | about 12 min | about 8 min |
| max context | 93057 | 56199 |
| VRAM | ~23976 MiB | ~23950–23978 MiB |

<!-- ai-lint: ok 2900 official 3090 range endpoint, same digits as the later 0.1.39 prefill p50, not a second reading of that cell -->
Prefill is about the same on both. In the UD run, one 89517-token prompt missed the cache entirely: prefill took 29.9 seconds, 2998 tok/s. That lines up with the official 3090 figure, about 2200–2900 tok/s for a 30k cold prefill.

Official IQ3_S is ahead across the board. Decode is higher at both p50 and p90, and the whole exploration dropped from about 12 minutes to 8. The official 5070 12GB table has IQ3_S slower than IQ3_XXS (53 vs 62 tok/s).

While it is working, GPU utilization is 98–100%, power 270–300 W, with a peak of 346 W. VRAM sits against the 24 GB limit. In a stretch of continuous use, the GPU is busy about two thirds of the time.

## Retest after moving to 0.1.39

On October 5 the engine moved from 0.1.38 to 0.1.39, tag v0.1.39, commit 6f32ec0. GitHub still has no `strata-linux-x64.zip`. The Windows assets are CUDA 13, an experimental CUDA 12 build, and HIP. The checkout is detached, so `git pull --ff-only` inside `update.sh` fails. I stopped the service, ran `git fetch --tags`, then `git checkout --detach v0.1.39`, then `./setup.sh --update`, and compiled locally for sm_89. Nothing in `strata-iq3_s.json` changed. Parallel slots stayed off, and so did vision. This release also stops after 256 copies of the same token, can reload the last context when the engine actually restarts, and adds the Responses API for Codex. This run was a speed check, and it did not hit those.

The 0.1.39 decode speedup runs only when every expert of a layer is in VRAM. This 4090 cannot hold that. Startup still puts 46.84 GiB of expert weights in an arena in RAM, and the hot cache is the same as 0.1.38: 8563 slots, 16.24 GiB. This run hit 90.7%, and about 4.2% of the lookups were read by the GPU from RAM over PCIe. The prompt chunk stayed at 8192. The log mentions a 512-slot ring, and the chunk for this task did not change. After load, 253 MiB of VRAM was free.

The prompt was the same line: open 5 subagents and look at this project, and the project was the same one. The stopwatch is the whole task. Prefill plus decode in the log is about a second off that clock. Both stretches end at the `prompt 276` line that generated 96 tokens, and the table is those two stretches. A continuation of about 60k tokens right after the upgrade is not included.

The IQ3_S column above, 58 requests and about 8 minutes, is an earlier aggregate. This stopwatch is a different stretch. The first request of this round still had 16384 tokens of KV from the previous chat, so prefill recomputed 9246. Decode throughput is generated tokens divided by decode time. The 20k–40k prefill median is 16 requests on each side.

| | v0.1.36 | v0.1.39 |
|---|---:|---:|
| stopwatch | 9 min 27 s | 8 min 56 s |
| requests | 47 | 44 |
| prefill total | 330.0 s | 317.0 s |
| decode total | 237.9 s | 220.1 s |
| generated tokens | 26821 | 23338 |
| read tokens | 855873 | 873406 |
| decode p50 | 115.1 tok/s | 106.9 tok/s |
| decode p90 | 133.7 tok/s | 125.8 tok/s |
| decode throughput | 112.7 tok/s | 106.0 tok/s |
| prefill p50 (miss, ≥2k) | 2594 tok/s | 2761 tok/s |
| prefill p50 (miss, 20k–40k) | 2795 tok/s | 2900 tok/s |
| draft accept | 72.5% | 71.9% |

The stopwatch was 31 seconds shorter. Long prefills were a bit faster, and read tokens went up a little. Decode p50, p90, and throughput are all lower. The total came down mostly because this round wrote fewer tokens. Draft accept is about the same. On this card, for this kind of code scan, 0.1.39 barely moves the speed.

## How many people

The service handles one request at a time. `/v1/status` shows `serving: 1`, and later requests queue.

For code analysis, the median hold is about 5–9 seconds, with an occasional 30–50 second answer. Two or three people at once is still workable. An agent that keeps sending requests can fill the queue by itself. On a different large repo, with no prefix cache hit, a 90k prefill alone is about 30 seconds.

## Compared with the Ollama 27B

I did not re-measure the old Ollama 27B on this machine. The gap felt like a cliff, mostly from MoE sparse activation and MTP, and the model itself is different.

## Compared with two DGX Sparks

[Last time]({{< relref "dgx-spark-agent-inference.md" >}}), two DGX Sparks ran `MiMo-V2.6-Flash`. A short prompt decoded at about 44 tok/s on one stream, and six concurrent streams totaled 173 tok/s. On a real code scan, one stream fell to 15–25 tok/s and still had not finished a subtask after six minutes. Those machines have 128 GB of unified memory at 273 GB/s. A 24 GB 4090 has the bandwidth, and nowhere to put the model.

Strata keeps the experts in RAM and the hot ones in VRAM. Different model, same job: reading code. Median decode here is over 100 tok/s. This is way harder than Spark. Watching Qwen3.8-Flash-Next run like this on a 4090, it felt like watching an atomic bomb go off. The traditional software industry really is dead.
