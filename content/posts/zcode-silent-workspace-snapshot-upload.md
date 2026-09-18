---
title: "扒一扒 ZCode 静默上传全量 Git 历史的骚操作"
slug: "zcode-silent-workspace-snapshot-upload"
date: "2026-09-18T02:00:00+08:00"
tags: ["Security", "Privacy", "AI Coding", "Reverse Engineering"]
description: "ZCode 在登录状态下会静默打包整个工作区及完整 Git 历史上传至云端对象存储，且解密私钥仅存服务端；本文通过本地取证与客户端代码逆向还原完整上传链路与加密机制，并给出通过文件系统不变锁彻底阻断该行为的方案。"
---

本来只是清理磁盘时顺手看一眼 `~/.zcode` 为什么占了 700 多 MB。断断续续排查下来，确认了一件挺离谱的事：

**只要你在登录状态，ZCode（智谱官方的 AI 编程桌面端）就会在后台静默把整个工作区——包括完整的 `.git` 历史、LFS 大文件缓存、reflog 以及全局应用配置——打包加密，直接上传到阿里云 OSS。**

更讽刺的是：**加密用的 RSA 公钥是服务端动态下发的，私钥只存在云端。** 你本地生成的那份几百兆的密文，连你自己和客户端本体都解不开。

这篇文章把排查过程、证据链和最终的一键防御方案完整记录一下。

## 起点：一个卡在 pending 里的 313MB 压缩包

`~/.zcode` 是 ZCode 的本地数据根目录。当时扫出来的目录体积分布大概这样：
- `cli/`：约 257MB（本地会话数据库、执行日志）
- `computer-use/`：约 130MB（应用本体和运行依赖）
- `v2/checkpoints/`：约 303MB（也就是这次的主角）

点进 `v2/checkpoints/`，里面躺着一个 313MB 的 `.enc` 加密文件，还有一份状态文件：

```json
{
  "workspacePath": "/Users/ferstar/myprojects/<某商业项目>",
  "lastCompressedSize": {
    "encryptedSizeBytes": 313070842,
    "workspaceSizeBytes": 345549173
  },
  "kind": "baseline",
  "failureCount": 564
}
```

意思很直白：
1. 客户端扫了我本地打开的商业项目，排除了 `node_modules` 等少量目录后，把剩下的 345MB 内容打包加密成了 313MB 的压缩包，标记为 `baseline`（全量快照）；
2. 状态显示它尝试上传失败了 564 次，所以一直卡在本地 `pending/` 目录里等着重试。

整个项目总共 10GB，排除掉依赖后剩下的 345MB 几乎全是核心资产。

## 它要传到哪：从日志到 asar 逆向

日志里没有直接打出具体的上传地址，于是顺手把客户端的 `app.asar` 扒开看代码。整条上传链路还原出来如下：

{{< mermaid >}}
sequenceDiagram
    participant C as ZCode 客户端
    participant S as zcode.z.ai
    participant O as 阿里云 OSS
    C->>S: POST /api/v1/snapshot/upload-credential
    S-->>C: snapshot_id + RSA公钥 + max_size + OSS表单凭证 + callback
    C->>C: tar.gz 打包 → AES-256-CTR 加密 → RSA-OAEP 包裹密钥
    C->>O: PostObject 表单直传 tar.gz.enc
    O->>S: callback 回调确认接收
{{< /mermaid >}}

整个流程分两步：

1. **先找协调服务器要凭证**：客户端请求 `https://zcode.z.ai`（代码里的 `VITE_ZCODE_ENDPOINT_ORIGIN`），服务端返回 OSS 表单签名（`policy`、`x-oss-signature`）、动态分配的 Object Key、大小限制，以及本次加密要用的公钥；
2. **表单直传 OSS**：客户端在本地打包并流式加密后，**根本不经过智谱自己的业务服务器，直接走 HTTP POST 表单把 `tar.gz.enc` 甩给阿里云 OSS**。传完之后由 OSS 服务端触发 callback 通知智谱后端登记。

抓包看了下 ZCode 运行时的连接，进程常驻的 HTTPS 连接刚好就是 `zcode.z.ai` 的解析 IP 外加两个阿里云 OSS 节点。

## 最讽刺的部分：这把钥匙是服务端的

客户端用的加密是标准的信封加密（Envelope Encryption）：

```javascript
keyId: String(i.encryption.key_version),
keyWrapAlgorithm: "rsa-oaep-sha256",
publicKeySpkiPem: Ylt(i.encryption.public_key)
```

- 文件内容用随机生成的对称密钥走 AES-256-CTR 加密；
- 对称密钥用 RSA-OAEP-SHA256 包裹，公钥就是上面从服务端动态拿到的。

关键就在这把 RSA 公钥：**它是服务端在下发上传凭证时临时给的，私钥从头到尾只在云端。** 我拿本机的所有私钥去解 envelope 里的密钥，毫无悬念全都失败。

这意味着：你硬盘上那份 313MB 的密文，你打不开，ZCode 客户端自己也打不开，全天下只有智谱后端的私钥能解。

如果这玩意真是为了给用户做断点恢复或者跨设备同步，密钥理应绑在本地（像 Git 或者 Time Machine 一样）。**一把只有服务端能解开的钥匙，目的只有一个：确保服务端单方面能看。**

## 快照里到底装了啥：近九成是 .git

密文虽然解不开，但快照生成时留下的 Manifest（文件清单）是明明白白写在本地的。拉出这份包含 42,411 个文件的清单统计了一下：

| 内容 | 体积 | 占比 | 包含的信息 |
|---|---|---|---|
| `.git/lfs/` | 196.1 MB | 56.8% | LFS 缓存，项目历史下拉过的所有大文件和二进制资产 |
| `.git/objects/` | 102.2 MB | 29.6% | 完整的 Git 历史对象库（Commit、Tree、Blob） |
| `.git/logs/` | 0.6 MB | 0.2% | reflog 轨迹，本地所有分支操作和未推送记录 |
| 其余源码与文档 | ~46.2 MB | 13.4% | `src/`、各类配置文件和业务代码 |

`.git` 一个目录就占了整整 **86.6%**。

也就是说，只要这个包传上去了，云端拿到的绝不只是你当前工作区的代码，而是**这个仓库自打创建以来的全部历史底裤**：
- 哪怕早就被覆盖删掉的敏感配置和历史 key；
- 本地还没推远端的分支名（直接暴露业务未公开的研发动向）；
- `.git/config` 里配的内部自建 GitLab 域名和仓库路径。

另外代码里还带了一个 `repo_snapshot_extra_manifest`，会把你的 ZCode 全局配置文件（比如 `settings.behavior.json`）算完哈希，跨工作区打包，随每次快照一起传上云端。

## 开关的真相：你关掉的开关根本管不着它

很多人第一反应是去设置里找开关关掉。我把设置项和代码逻辑逐个对了一遍：

| 开关 | 你以为它管 | 实际管 |
|---|---|---|
| **优化体验** (`optimizeAgentExperienceEnabled`) | 数据采集 / 遥测上传 | **只管要不要拿你的数据去训练模型**。关了照样抓快照上传 |
| **仓库快照索引** (`repoSnapshotIndexingEnabled`) | 快照功能本身 | **只管服务端拿了快照后要不要建索引**。关了本地打包上传一点不落 |

看客户端组装代码更直白：负责快照捕获和上传的 sidecar 是在启动时**无条件实例化的**。代码里根本没有任何针对用户配置的 if 判断，唯一的要求就是 `tokenProvider` 能拿到登录后的 JWT。

**一句话：只要你登录了账号，这个上传机制就是常开的，而且 UI 里没有任何开关能把它关掉。**

抓取触发点有两个：一个是 `captureBeforePrompt`（每次发 Prompt 前），另一个是任务结束时标记 `repo-wiki-update`。翻看日志，单个活跃会话里最多能产生 62 次快照捕获。

## 隐私政策怎么说的

翻了下 ZCode 的隐私政策，里面明确写了会收集“对话中提交的文本、文件和代码”——这属于 AI 助手调模型推理的常规操作，各家都一样。

但通篇**只字未提会把整个工作区连同完整 Git 历史静默打包上传**。官方文档、FAQ 和更新日志里对此也完全没有任何说明。

能对得上的只有一句万能套话：“优化计划默认关闭，不主动加入不会将输入用于训练”。

## 防御：删是打地鼠，直接锁目录

刚发现这个 pending 包时我顺手把它删了，结果半小时内它又重新抓了一次——新的 313MB 压缩包，失败计数从 564 蹦到 565。上传器发现本地文件没了，直接重新打包一个。纯靠手动删就是打地鼠。

最直接有效的办法是在文件系统层加不变锁，从内核层面禁止写入这个目录：

### macOS

```bash
# 清空并锁定 checkpoints 目录
rm -rf ~/.zcode/v2/checkpoints
mkdir -p ~/.zcode/v2/checkpoints
chflags uchg ~/.zcode/v2/checkpoints

# 验证：应该输出 Operation not permitted
touch ~/.zcode/v2/checkpoints/test
```

### Linux

```bash
# 清空并锁定 checkpoints 目录
rm -rf ~/.zcode/v2/checkpoints
mkdir -p ~/.zcode/v2/checkpoints
sudo chattr +i ~/.zcode/v2/checkpoints

# 验证：应该输出 Operation not permitted
touch ~/.zcode/v2/checkpoints/test
```

### 影响与恢复
- **阻断效果**：快照逻辑在尝试写目录时直接被系统内核拦截，没有产物，后续向 OSS 的直传自然无从谈起；
- **功能影响**：ZCode 的“检查点回滚 / 时间线”功能不可用（本来也是拿全量代码上云换的）。日常的代码补全、对话、工具调用完全正常，日志里被吞掉的 IO 报错不影响使用；
- **想恢复**：执行 `chflags nouchg ~/.zcode/v2/checkpoints`（macOS）或 `sudo chattr -i ~/.zcode/v2/checkpoints`（Linux）即可。

## 写在最后

用 AI 工具，模型推理必然要吃代码上下文，这个在用的时候大家心里都有数。但这事越线的地方很明确：

一是**数据范围**。推理给的是当前任务相关的上下文，而快照是把整个仓库连同几年的 Git 提交历史全部打包端走。

二是**架构姿态**。如果真是给用户做断点恢复或跨端同步，解密密钥理应在用户本地。一把只有服务端能解的钥匙、零披露的隐私政策、关不掉的默认行为、删了还自动重传的执拗——这摆明了不是备份，更像采集。

工具没有原罪，但红线应该由使用者自己划。既然软件里关不掉，那就用操作系统的锁把它关进笼子里。
