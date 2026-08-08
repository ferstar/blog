---
title: "1Password 又涨价了，我把密码库迁到了自建 Vaultwarden"
slug: "1password-to-self-hosted-vaultwarden"
date: "2026-08-08T10:00:00+08:00"
tags: ["1Password", "Vaultwarden", "Bitwarden", "Self-hosting", "Security"]
description: "1Password Families 年费从 59.85 美元涨到 71.88 美元后，我用 Vaultwarden 自建密码库，完成普通数据和 Passkey 迁移，并补齐备份、邀请和恢复流程。"
---

导火索很简单：1Password 又涨价了。

我的三人 Families 套餐以前是 US$59.85/年，账单页面显示下一周期会变成 US$71.88/年，约上涨 20%。这个价格本身不算离谱，但我实在不想继续跟着订阅价格走了。于是开始找平替，最后把个人密码库迁到了 VPS 上自建的 Vaultwarden。

迁移本身并不难，真正费时间的是迁移前后那一圈容易被忽略的事：Passkey 和普通登录条目的处理方式不同，服务端坏了会把恢复凭据一起锁住，批量整理还可能触发版本冲突。

这篇文章记录一次实际迁移，部署过程只保留与迁移相关的部分。文中的真实域名用 `vault.example.com` 代替。

## 先说结论

- 对个人或家庭使用，Vaultwarden 足够轻量，官方 Bitwarden 的浏览器、桌面和移动端客户端都可以继续使用。
- 密码、用户名、OTP、备注等常规数据迁移顺利；安卓端按应用内导入流程可以完整迁移，Passkey 也在这次实测中成功导入。
- 这次没有使用 `.1pux` 或其他导出文件，全部通过安卓端直接从其他 App 导入；常规数据和 Passkey 都完整迁移成功。
- 1Password 不应该在第一次导入成功后立刻删除。真正的完成标准是：新客户端能用、备份能读、恢复路径不依赖这个密码库本身。

{{< mermaid >}}
flowchart LR
    A["1Password"] --> B["Export / CXP"]
    B --> C["Vaultwarden"]
    C --> D["Client verification"]
    C --> E["Backups"]
    D --> F["Keep 1Password until verified"]
{{< /mermaid >}}

## 为什么选 Vaultwarden

当时对比过三条路线：

- **Vaultwarden**：轻量、Bitwarden 客户端生态完整，适合个人和家庭；服务端采用独立实现，兼容性需要按实际版本验证。
- **Passbolt**：团队权限、审计和共享能力更完整，但部署和配套更重。
- **KeePassXC**：服务器信任面最小，但本质是同步数据库文件，多人实时共享不如前两者自然。

我已经有一台 VPS 和 1Panel，所以最后选了 Vaultwarden：数据放在独立的数据盘，Docker 运行，继续复用 1Panel/OpenResty 的 HTTPS 和反向代理。

## 部署中最容易低估的工作

### 1. 数据盘和目录先定下来

VPS 上新增了一块 150 GiB 的盘，挂载到 `/data`，Vaultwarden 数据目录固定为：

```text
/data/services/vaultwarden
```

文件系统最后选了 ext4。中间实际比较过 XFS：它在空盘上能多出一些可用空间，但不能缩容；考虑到以后可能换更小的盘，最终还是把“恢复和迁移的余地”放在了“多省一点空间”前面。

这个选择没有普适答案，但密码库这种服务不值得为了理论性能把未来的迁移路径堵死。

### 2. DNS、证书和反代比启动容器更容易出问题

真正接入公网前，先确认 DNS 已经指向正确的 VPS。过程中曾经遇到旧 IPv6 记录导致请求没有到新机器；容器本身没问题，问题在入口。

最后让 1Panel 管理 `vault.example.com` 的证书，用现有 Cloudflare DNS 账号完成签发和续期，再由 OpenResty 反代到 Vaultwarden。这样证书只有一个管理入口，不再让独立 certbot 和面板同时维护同一份证书。

验收时不能只看容器 `healthy`：还要从公网检查 HTTPS、自动跳转、Vaultwarden 的健康接口和实际登录。后来有一次访问失败，最终查明是本机 DNS 的瞬时异常，远端服务一直是 200 和 healthy。

### 3. 关闭公开注册，邀请和注册分开控制

第一次部署时我把公开注册和邀请都关了。需要和朋友共享时，我保持公开注册关闭，只打开邀请：

```env
SIGNUPS_ALLOWED=false
INVITATIONS_ALLOWED=true
```

朋友使用自己的邮箱和主密码注册，再加入 Organization 和 Collection。个人密码留在自己的库里，需要共享的条目才放到共享集合中。

邀请邮件还需要 SMTP。这里用 Mailgun 的 SMTP 做了两层验证：先做 STARTTLS 登录握手，再发送真实邀请邮件。前者成功不等于后者一定投递成功，这两个结果要分开记录。

## 迁移的实际路线

### 第一步：先保留 1Password

迁移前先确认 1Password 还能正常解锁，并准备一个加密备份。不要把“新服务能登录”误认为“旧数据已经安全迁完”。

### 第二步：在安卓 App 内直接导入

这次没有使用 `.1pux`，也没有先导出文件。全部迁移都在安卓端 Bitwarden App 内完成：先配置自托管服务器，再进入：

`设置 → 密码库 → 导入项目 → 从其他 App 导入 → 1Password`

这条路径把常规数据和 Passkey 一起完整导入了。整个迁移依靠客户端提供的应用间导入，没有经过文件导出。

导入后至少检查这些内容：

- 登录名和密码是否完整；
- OTP 是否能生成正确验证码；
- 备注、自定义字段和附件是否还在；
- 文件夹是否需要重新规划；
- 是否误导入了第二份，产生重复条目。

首次操作仍建议先抽查少量关键条目，确认新设备登录、自动填充和 Passkey 正常后，再处理全部数据；在确认前保留旧的 1Password。

相关说明：

- [Bitwarden 从 1Password 导入](https://bitwarden.com/help/import-from-1password/)
- [Vaultwarden 项目](https://github.com/dani-garcia/vaultwarden)

### 第三步：客户端接入要单独验收

浏览器扩展、桌面端和手机 App 都要在登录前选择自托管服务器，地址类似：

```text
https://vault.example.com
```

我还试了 Bitwarden CLI。配置自托管地址的最小路径是：

```bash
bw config server https://vault.example.com
bw config server
bw login your-email@example.com
bw status
```

这里遇到过一个与服务端无关的坑：当时用 pnpm 全局安装的 CLI 在 Node 26.3.0 下报 `Cannot find module 'buffer/'`。最后确认是全局依赖链接和运行时组合的问题，改用 Node 22 配合 npm 安装同版本 CLI 后恢复正常。

所以 CLI 报错时，先检查 `bw` 的安装方式、Node 版本和实际服务地址，不要一上来重启 Vaultwarden。

## 数据整理给了一个很实际的教训

迁移完成后，我还想把原来全部位于 `No Folder` 的 261 条记录重新分类。分类本身不难，难的是批量更新。

我先做了加密备份，然后只修改文件夹归属，不改密码、备注、OTP，也不删除重复项。批量并发更新时，Vaultwarden 的版本竞争造成 6 条同名 Mattermost 条目暂时进入回收站。最后通过重新同步和逐条恢复，条目 ID 与备份完全对回来了。

这件事留下了几条规则：

1. 批量写入前必须有可恢复备份；
2. 只改一个字段，也要把它当作真实数据变更；
3. 并发请求不一定更快，客户端副本过旧时反而会制造竞态；
4. 最终校验不能只看 HTTP 200，要重新对比总数、条目 ID 和回收站。

现在的密码库按工作与内网、开发与云服务、个人账号、通信与社交、金融与实名、家庭与设备、安全与密钥分类，261 条都已经离开 `No Folder`。重复项没有擅自删除，留给之后人工确认。

## 备份要能拿来恢复

自建密码库最大的心理变化，是你要自己承担恢复责任。

这次的收口方式是：

- 数据库、附件和配置放在 `/data` 下；
- 本机定期生成备份；
- 本机备份成功后，再通过 SSH 同步到另一台主机 `DO_NEW`；
- 备份文件使用加密格式，并保留可核对的结果；
- 云主机、DNS、邮箱和 VPS 的恢复凭据不全部放进这个密码库，至少保留一条独立的 break-glass 路径。

只把备份放在同一台 VPS 上，不算真正的异地备份。更重要的是，备份存在也不等于能恢复：至少要做一次临时恢复，确认数据库、附件、配置和客户端登录都能回来。

## 最后的判断

这次迁移让我确认，Vaultwarden 可以作为个人或家庭场景下的 1Password 替代品，容器启动只是整个过程的第一步。

你放弃一部分托管服务，同时接手 DNS、TLS、SMTP、升级、日志、备份和恢复。普通密码数据迁移的门槛不高，Passkey、共享权限和故障恢复才是需要重点投入的部分。

如果只是为了省订阅费，而不愿意维护备份和恢复流程，迁移的收益可能不值得成本；如果更在意数据控制、客户端自由度，并愿意把它当作一个小型生产服务来维护，Vaultwarden 的确是一条很实用的路。

我把下面四件事都确认后，才把迁移视为完成：

- 新设备能登录并自动填充；
- OTP 和关键附件经过抽查；
- Passkey 已在目标客户端验证，或有明确的逐站重建计划；
- VPS 挂掉后，仍有独立的恢复入口和可验证备份。
