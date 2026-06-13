---
title: "ACE 靠不住了：ace-wrapper 之后我换了个方式做语义检索"
slug: "ace-wrapper-to-fast-context"
date: "2026-06-01T10:35:09+08:00"
tags: ['Idea', 'AI']
description: "ace-wrapper 写完后，ACE 越来越难薅，中转也纷纷扑街；不如直接逆向 Windsurf 的 SWE-grep 协议，再加本地 Semble 缓存做降级，最后做成一个混合检索工具 fast-context。"
series: ['AI Coding']
---

[上一篇](/posts/ace-wrapper-semantic-search-ai-coding-harness/) 我写过 `ace-wrapper`：把 ACE（Augment Context Engine）的 filesystem context search 包成一个 shell 命令，让 agent 在关键词不明确时先走语义检索，再决定读哪些文件。

结果 ACE 开始不稳定了。

API key 换着花样失效，免费额度越来越难薅，几个中转服务也一个个扑街。

这也怪不了谁，毕竟本来就是 preview 功能。问题在于，编码助手的工作流已经长在语义检索上了：一天几十次 `ace` 调用，少了它，agent 又回到盲猜关键词的老路。

所以我换了个办法：

[ferstar/fast-context](https://github.com/ferstar/fast-context)

这次我没走第三方 API，而是直接逆向 Windsurf 的 SWE-grep 协议——也就是 Codex CLI 和 Windsurf IDE 自己在用的那个语义搜索后端——同时在本地加了一层 Semble 缓存做降级。

### 结构跟 ace-wrapper 最大的区别

ace-wrapper 是纯远程调用：本地只传参数，一切靠 ACE 服务。

fast-context 则是本地和远端一起上。

{{< mermaid >}}
flowchart TB
  subgraph Input
    Q[User query]
  end

  subgraph Local
    S[Semble local prefetch<br/>cached index + chunk search]
    A[Lexical anchors<br/>filename / path / literal hits]
    R["Repo map<br/>(auto-shrink when too large)"]
  end

  subgraph Remote
    WS[Windsurf SWE-grep<br/>agentic verify + expand]
  end

  subgraph Output
    O["Candidate files<br/>line ranges<br/>follow-up terms<br/>(or local chunks when remote fails)"]
  end

  Q --> S
  Q --> A
  Q --> R
  S --> WS
  A --> WS
  R --> WS
  WS -- success --> O
  WS -- auth / rate-limit / timeout --> O
  S -- fallback path --> O
{{< /mermaid >}}

流程变成：

1. **先在本地跑 Semble**——缓存的索引+ chunk 搜索，毫秒级返回命中
2. **收集本地 lexical anchors**——精确的文件名、路径片段、内容中的字面量匹配
3. **生成 repo map**——代码树结构，太大了就自动压缩
4. **把这三样打包发给 Windsurf**——Semble 的 chunk 候选当提示，lexical anchors 当锚点，repo map 给路径上下文
5. **Windsurf 用 rg/readfile/tree/ls/glob 验证和扩展**——agent 层的工具调用循环
6. **远端走不通时，直接返回本地 Semble 结果**——不空手，不卡住

这个“不空手”其实很关键。ace-wrapper 依赖 ACE 时，服务一挂，那一轮搜索就没了。现在远端断了，本地缓存至少还能给出 chunk 级别的候选，质量差一点，但工作流不会直接卡死。

### 逆向 SWE-grep 的过程

Windsurf 的 SWE-grep 走的是 Connect-RPC + Protobuf，和典型的 REST API 完全不是一回事。

最麻烦的是 Connect 协议的帧编码。每个 RPC 帧前有个 5 字节头（1 字节 flag + 4 字节大端长度），请求和响应都这么包。协议本身还要求先发一条 Connect-Connect 帧，然后才是实际数据。

Protobuf 这边更烦。Windsurf 用的是自定义 proto schema，公开定义找不到。核心数据结构的 field numbers 只能从抓包或已知的 Wireshark 解密配置里猜——比如调用链 `{1: name, 2: args, 3: id}`、变量定义 `{1: name, 2: type, 3: value}`。猜错就整个请求失败，而且没有什么友好的报错。

整个编码器大概这样（[ProtobufEncoder](https://github.com/ferstar/fast-context/blob/main/src/core.py#L64)）：

```python
class ProtobufEncoder:
    """手动 protobuf 编码器，完全匹配 Windsurf 的请求格式。"""
    def __init__(self) -> None:
        self.buf = bytearray()

    def _varint(self, value: int) -> bytes:
        parts: list[int] = []
        while value > 0x7F:
            parts.append((value & 0x7F) | 0x80)
            value >>= 7
        parts.append(value & 0x7F)
        return bytes(parts)

    def _tag(self, field: int, wire: int) -> bytes:
        return self._varint((field << 3) | wire)
```

反过来，接 Windsurf 返回的流式响应也得自己解码——拆帧、读数据、找流结束标志——最后才能拿到语义结果。比调 REST API 麻烦得多，但好处也明显：不需要任何中间服务，直接打 Windsurf 后端。

### 本地 Semble 缓存为什么管用

当初加 Semble 之前，我其实犹豫过：本地建一份索引，会不会是多此一举？

后来 benchmark 一跑，这事就没悬念了。

我拿 40 条标注查询在两个仓库上跑了对比（fastapi 和 axios），结果是：

| Backend | NDCG@10 | Recall@10 | Top-1 | Batch p50 |
|:---|---:|---:|---:|---:|
| local（仅 Semble） | 0.854 | 0.946 | 0.775 | 30 ms |
| remote（仅 Windsurf） | 0.453 | 0.467 | 0.450 | 24.4 s |
| hybrid（Semble + Windsurf） | 0.890 | 0.979 | 0.825 | 28.3 s |

本地 Semble 自己的召回率已经 94.6%，p50 只有 30 毫秒。Windsurf 单独跑反而有点拉——成功率只有 52.5%，剩下的不是被限流，就是报 `resource_exhausted`。

hybrid 模式则是把 Windsurf 放到 Semble 结果后面做验证和扩展，NDCG@10 涨到 0.890，召回率升到 97.9%。

这个结果让我确定了两件事：

- **本地缓存不是备胎，是第一道防线**。它在 30 毫秒内能搞定绝大部分常见搜索，远端挂了就是降级路径，而不是直接废掉。
- **Windsurf 的价值在验证，不在首轮搜索**。直接让它从头搜，容易超时或被限流；给它 Semble 的 chunk 候选和精确的关键词锚点后，它只需要在已知问题上做确认，成功率明显高很多。

### 凭据处理也比之前复杂了

ace-wrapper 只需要一个 API key。fast-context 拿的是 Windsurf 的 session token，存在本地的 `state.vscdb`（SQLite 数据库）。

提取逻辑在 [extract_key.py](https://github.com/ferstar/fast-context/blob/main/src/extract_key.py)：

```
从 state.vscdb 的 ItemTable 里查 key 为 'windsurf.api_key' 的行
→ 如果有，直接返回
→ 如果没查到，再查 key 包含 'devin-session-token' 的行
→ 两种格式都能用
→ 也可以通过 WINDSURF_API_KEY 环境变量覆盖
```

为什么两种格式都要支持？因为 Windsurf 自己就在变。前期是标准 API key，后来改成了 `devin-session-token$...` 这种 session 风格的凭据。不跟着变，用户升级 IDE 后工具就废了。

### 现在的工作流

ace-wrapper 阶段，我的 AGENTS.md 长这样：

```
用 ace 做语义检索找候选文件 → 读文件 → 用 rg 确认精确证据
```

现在改成了：

```
用 fast-context search（默认 hybrid）找候选文件 + 行号范围
如果 hybrid 超时或无结果，试试 fast-context local-search
如果有 chunk 候选想看相关代码，用 fast-context find-related
读完文件后用 rg/ast-grep 确认精确证据
```

路径是多了几条，但每条都知道失败后该往哪退。

远程也搭了一套模型 fallback 链：

1. 默认用 `MODEL_SWE_1_6_FAST`
2. 遇到 `resource_exhausted` 或限流，自动降级到 `MODEL_SWE_1_5`
3. 还能通过 `WS_FALLBACK_MODELS` 自定义 fallback 顺序

### Benchmark 数据

用 fair runner（completion-based cooldown, 40 queries）重新跑 benchmark 后，几个指标更能说明问题：

- **hybrid 模式非空输出率 100%**——40 条查询全部返回了有效结果
- **remote 模式非空输出率只有 50%**——剩下一半要么超时要么被限流
- **local 模式零失败**——100% 非空，p50 延迟 30 ms

这意味着，如果纯靠远程语义搜索，高峰期可能一半查询直接没响应。hybrid 模式有本地 Semble 打底后，最差也会给出本地 chunk，而不是空结果。

### 这次暂时不想再推翻重来的几个点

这次重写有几个架构选择，目前看来是对的：

1. **始终保持降级路径**。任何远程依赖都得有本地回退。ACE 那次已经吃过亏了。
2. **纯 Python 更好维护**。ace-wrapper 也是 Python，但这次代码量从几百行涨到了两千多行——有 protobuf 编码器、Connect 帧协议、Semble 适配层、benchmark runner——结构清楚比语言选型重要得多。Python 只是我最顺手。
3. **Benchmark 要跟代码一起放**。[benchmarks/](https://github.com/ferstar/fast-context/tree/main/benchmarks/) 里的 40 条标注查询和 runner，跑一次就能看到各个 backend 的真实差异。没有数据支撑的优化决策，基本靠猜。
4. **凭据提取要自动适配**。`devin-session-token` 这种变化是预料之外的，但代码结构上留了扩展点——查不到 key 就换个 pattern 再查一次，不用改主流程。

### 收尾

ace-wrapper 到现在我还在用——ACE 偶尔又能通了。但我已经不想把工作流绑死在它上面。

fast-context 的核心思路其实很简单：语义搜索先靠本地缓存托底，远端负责验证和补充。纯远程方案一旦上游抽风，就容易断绳。

如果你也踩过这个坑，代码在这：[ferstar/fast-context](https://github.com/ferstar/fast-context)
