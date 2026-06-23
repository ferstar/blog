---
title: "把 Codex 工作流养成活系统：从会话扫描到 Skills"
slug: "codex-workflow-skills-feedback-loop"
date: "2026-06-22T12:00:00+08:00"
tags: ['Idea', 'AI']
description: "Codex 长期使用后会积累大量重复排查和交付动作；扫描本机会话，找出高频摩擦点，再沉淀成 skills、脚本和跨机器同步；让工作流自己持续变轻。"
series: ['AI Coding']
---

前几天干了一件很土的事：把本机 `~/.codex` 里的会话记录扫了一遍。

不是怀旧，也不是做数据面板。就想看看自己到底在哪些地方反复浪费时间。

猜也猜得到。真正耗人的不是某次代码改得难，是一堆小动作每天都得来一遍：

- `git status`、`git diff`、`glab api`、`glab mr`
- 查 CI 第一个挂掉的 job
- 远端主机查 SSH、PATH、Tailscale、权限
- 判断这次改动该跑哪组测试
- release / deploy 前确认 SHA、workflow、artifact
- 中途续会话重新捋 issue、branch、MR

这些事都太小了，小到你懒得专门去管。但就是因为小，才一直被放过。结果就是每天泡在这些手工胶水里。

这件事最开始的提示词其实很短：

```text
根据我最近 codex 的项目和线程，帮我提出一些可以简化项目流程和提升效率的方法，使用子代理分头分析。
```

第一轮结果还是太偏最近几个项目，于是又补了一句：

```text
不止这几个项目，扫描 ~/.codex 下所有可能的会话，分派多个 sub agent 分头分析，最后汇总。
```

重点不是“让模型想点优化建议”，而是把分析对象从印象里的项目，换成真实会话里的重复动作。

### 别急着写工具

我以前也这样——看见重复就觉得该写脚本。后来发现这一步常常太早。

很多重复不是命令本身重复，是判断过程重复。比如 CI 挂了，真正该固化的不是某条 `gh run view`，而是：

1. 先确认 run 和 head SHA
2. 找第一个挂掉的 job
3. 把有效错误截出来
4. 再判断是 workflow 的问题、依赖的问题、测试还是代码

一上来就写个大工具，容易把错误假设焊进去。轻一点的做法是先写成 skill：什么时候用、最小几步、别干什么、输出什么。

skill 不是百科全书，就是张便签——让 agent 少走一条死路。

{{< mermaid >}}
flowchart LR
  A[Session history] --> B[Repeated friction]
  B --> C[Small skill]
  C --> D[Run on real tasks]
  D --> E[Script only when repeated]
  E --> C
{{< /mermaid >}}

最后只留了这几个：

- `agent-preflight`：开工前读真实 repo 状态，不靠印象
- `gitlab-mr-context`：用 `glab api` 拉 issue / MR / pipeline / notes，稳得多
- `ci-first-failure`：先找第一个真实失败点，再动代码
- `path-verify`：按改动的文件选最小验证命令
- `release-deploy-preflight`：部署前确认 full SHA、workflow、artifact、健康检查
- `remote-health`：远端主机先查 SSH、PATH、服务、锁和 Tailscale

名字都不酷，好处是不用想就知道该什么时候用。

### skill 先行，脚本后补

还有一个教训：别一上来就给每个 skill 配脚本目录。

很多流程写个 `SKILL.md` 就够用了。`path-verify` 不是替你跑测试，是提醒你按变更路径选最小检查。让它先跟 agent 在真实任务里跑几轮，自动化等确认了再说。

脚本只干一类事：已经确定重复、确定机械、确定低风险的。

这轮我只加了一个——把 repo 里的 skills 链接到用户目录：

```bash
scripts/link-user-skills.sh
```

Windows 补了个 PowerShell 版：

```powershell
.\scripts\link-user-skills.ps1
```

中间踩了个坑：软链接方向。

正确方向是 repo 放真实文件，用户目录放链接：

```text
~/.agents/skills/glab -> /path/to/repo/skills/glab
```

这样 repo 能提交真实内容，本机 Codex 也能直接用。搞反了就糟了——repo 里只剩一个指向 `~/.agents` 的链接，推上去别人拿不到内容，Git 还以为原文件被删了。

### 让它跨机器能跑

我常年在 macOS、Windows、远端之间切。skill 要是只在一台机器上能用，价值直接打折。

所以本机搞完之后，把 repo 同步到 `my-win`，Windows 上也跑同一套维护。PowerShell 版用的是 directory junction 而不是 symlink——Windows 上建 symlink 经常跟权限干架，junction 对目录链接已经够用了。

挺琐碎的一步。但不做的话，工作流沉淀很快退化成一台机器的偏方。

### 我现在这样想

做了这轮以后，几个想法慢慢变硬了。

先从会话里找重复，别从想象里设计系统。如果 `git status`、`glab api`、`ssh`、`pnpm test` 真的是高频，就从它们开刀。别为了"流程治理"编一套没人用的东西出来。

skill 要短。一个只堵一个口子。它唯一的作用是让 agent 少问一次、少查一次、少猜一次。别往里面塞百科全书。

脚本只做机械活——链接 skills、采 CI 日志、远端健康检查。产品判断、风险边界、要不要部署，该留人的确认就留，至少留个显式 preflight。

错误得回炉。软链接方向我一上来就搞反了。修完以后经验不能只停在对话窗口里，得落到脚本和 README 里，不然下次还犯。

### 最后留下的

不多：

- 几个短 skill
- 一个 Bash 链接脚本
- 一个 PowerShell 链接脚本
- 一次 Windows 同步确认
- 一条规则：repo 放真实 skill，用户目录放链接

够了。

越来越觉得，AI coding 的工作流不是造一个大平台。是把最烦人的五分钟，一遍一遍地拿掉。每次少一点，系统就轻一点。这些小规则攒够了，agent 才像是在一个配好的工程环境里干活，而不是每次从野地里重新开路。
