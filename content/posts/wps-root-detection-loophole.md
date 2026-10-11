---
title: "你关的是开关，它开的是名单：WPS 是怎么查到我 Root 的"
slug: "wps-root-detection-loophole"
date: "2026-10-11T17:50:00+08:00"
tags: ["Android", "LSPosed", "KernelSU", "WPS", "Root"]
description: "root 手机上每次打开 WPS 都弹「设备已Root」警告，先写了个 LSPosed 模块精确拦截这条 Toast 还发布到了模块仓库；反编译挖出六项检测链，进程内实测命中的是 KernelSU 包名查询——明明拒绝了「读取应用列表」权限，WPS 靠 Manifest 里的 <queries> 声明照样查得到；最后用 Hide My Applist 对 WPS 隐藏管理器包名，检测在源头失效。"
---

买了个手机，不 root 感觉跟租的一样，所以我 root 了。结果 WPS 不知道从哪个版本开始，手越伸越长，连我 root 没 root 都要管：每次从桌面打开它，首页先弹一句「设备已Root，使用WPS Office可能存在安全风险。」一秒就消失，连通知历史都不留。最恶心的是，我明明拒绝了它的「读取应用列表」权限，它还是检测到了我装的 KernelSU。

## 这句警告为什么关不掉

这东西压根没走通知栏，是进程里直接调用的 Toast：通知权限管不着它，通知历史不留痕，WPS 设置里也翻不到开关。我把 KernelSU 对 WPS 的「卸载模块」选项打开，照弹不误。

后来定位到检测代码才知道这些手段为什么全落空：这台手机上根本就不是被 su 文件或挂载点触发的，动文件层自然没用。但那是后话，当时第一反应就是先让这句话闭嘴。

## 先让这一句消失

跑在 Termux 里的 Codex 先装了现成的 [ToastBlocker](https://github.com/h465855hgg/toastblocker)，作用域只勾 WPS。警告确实没了，但「保存成功」这类正常提示也一起消失，药效太猛。

想拦得更准一点，路却先断了：这句警告不是能单独禁用的 Activity、Service 或 Receiver，写轮眼（MyAndroidTools）那套组件级开关在这儿用不上。定位到的调用点是首页 `HomeControllerImpl$1$1.run()` 里的普通代码，检测完直接调 Toast。要精确到「只拦这一句」，只剩方法级 Hook，也就是 LSPosed。

于是写了个模块，规则只有一条：整句精确匹配那句警告（忽略排版空白），其他 Toast 一律放行，WPS 的 root 检测结果原样保留。实现上走公开的 `Toast.makeText/setText` 认内容、标记命中的 Toast 对象、跳过它的 `show()`，不碰 Android 16 已经限制读取的隐藏字段 `Toast.mText`。第一版用 legacy API 实机验证通过；我不希望发布版停在旧 API，又迁到 libxposed API 102 的 interceptor chain 重写。构建、签名、发布全走 GitHub Actions，[wps-root-toast](https://github.com/ferstar/wps-root-toast) 1.0.0 就这么进了 [LSPosed 模块仓库](https://github.com/Xposed-Modules-Repo/io.github.ferstar.wpsroottoast)。

到这里警告彻底消失。但谁都清楚这不算解决：检测还在跑，只是结果看不见了。

## WPS 怎么判定「已 Root」

把 WPS 26.9.1 拆开，首页这次的判定收敛在一个方法：`KSystemRoot.i(context)`，六项检查按顺序走，任何一项命中就返回 true。

{{< mermaid >}}
flowchart TD
    A["KSystemRoot.i(context)"] --> B1{"PATH 各目录下存在 su 文件？"}
    B1 -->|命中| T["判定已 Root"]
    B1 -->|未命中| B2{"persist.sys.root.status 非空且不为 0？"}
    B2 -->|命中| T
    B2 -->|未命中| B3{"ro.secure 为 0？"}
    B3 -->|命中| T
    B3 -->|未命中| B4{"Build.TAGS 含 test-keys？"}
    B4 -->|命中| T
    B4 -->|未命中| B5{"指纹或型号含模拟器特征？"}
    B5 -->|命中| T
    B5 -->|未命中| B6{"查询到 Root 管理器包名？"}
    B6 -->|命中| T
    B6 -->|未命中| F["判定未 Root"]
    T --> S["首页 Toast：设备已Root，使用WPS Office可能存在安全风险"]
    style B6 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
{{< /mermaid >}}

主链之外还有两处独立检测：`LogoutTracker.h()` 检查两个固定路径的 `su`；`GetDeviceInfoHandler.a()` 检查 `/system/bin/su` 和 `/system/xbin/su`，把结果放进设备信息的 `root` 字段经 JS 回调返回。仅从代码看不出有没有上传服务器，这里不断言。

代码摆在那，只能说明「有这六项」，定不了我这台手机中的是哪一项。做了个临时诊断版，把检测方法本身 hook 住、只记录各项返回值，装机冷启动一次：

| 检测项 | 本机实测 |
|---|---|
| PATH 各目录下的 `su` 文件 | false |
| `persist.sys.root.status` 属性 | false |
| `ro.secure=0` | false |
| `Build.TAGS` 含 `test-keys` | false |
| 模拟器特征（`goldfish`、`ranchu`、`sdk_gphone` 等） | false |
| 查询 `me.weishu.kernelsu` | **true** |
| 最终判定 | **true** |

前五项全干净，命中的是第六项：查询 KernelSU 管理器的包名。这也顺带解释了前面所有失败，su 文件、系统属性那些手段动的都不是这次的触发点。测完把诊断版撤下，恢复正式模块。

## 权限被拒，为什么还查得到

这是整件事里最膈应的地方。我确实没给 WPS「读取应用列表」权限，它照样查到了 KernelSU，因为这是两套机制：

厂商设置里的「读取应用列表」开关，管的是枚举设备上全部应用；而 Android 11 之后的包可见性机制，允许 App 在 Manifest 的 `<queries>` 里点名一批包名，点了的这些不需要任何运行时权限就能查装没装。WPS 的 `<queries>` 里就列着 KernelSU、Magisk、APatch，系统侧的可见性记录也确认这两个包之间互相可见。权限面板上那个「拒绝」，对点名查询完全不生效——开关给人的控制感是错觉。

这条检测链的判定质量也配不上「安全风险」四个字：只要装了管理器 App 就算命中，压根不验证 WPS 自己能不能真申请到 root 权限；模拟器特征也算 Root，用模拟器的人大概想不到会被这么问候一句。

## 让查询返回「未安装」

目标从「看不见警告」换成「查不到包」，可选的路一下子清晰了：

| 方案 | 做法 | 代价 |
|---|---|---|
| 应用列表隐藏类模块 | 对 WPS 隐藏指定包名 | 多数基于旧 API，新系统兼容性要实测 |
| 扩展现有模块 | 在 WPS 进程里拦截包查询，返回「未安装」 | 要自己写、自己维护 |
| 改 APK 删 `<queries>` | 重签名后安装 | 影响更新和签名校验，不适合日常 |

我当时已经打算再写一个 API 102 的包可见性过滤模块，连「让用户自选要隐藏的包」的配置页都想好了。动手前多问了一句「有没有现成模块干这个」——有，[Hide My Applist](https://modules.lsposed.org/module/com.tsng.hidemyapplist/)（HMA），干的就是这事。

配置克制到只有两条：建一个黑名单模板，里面只放 `me.weishu.kernelsu`；应用规则只对 WPS 生效。激进过滤、详细日志都不开。验证方式是把「WPS Root 提示隐藏」模块关掉，强停重开 WPS——不弹了。这说明包名查询在源头被挡住、六项检测返回了 false，而不是提示被藏起来；前者连其他入口的同类判定也一起失效，后者只是遮住了这一处。

HMA 3.8.3 用的是 libxposed API 101，还要求框架允许在系统服务里加载原生库，在我这套 Android 16 + LSPosed 2.2.1 上实测正常。

## 模块白写了吗

「感觉我上一个模块白写了啊。」Codex 的检讨是应该先查现有方案再动手，这没错；但更关键的顺序问题是先灭症状还是先找病因。不挖出六项检测链，就不知道触发点是包名查询，也就想不到 HMA 一个模板就能治本。病因挖出来之后发现武器库里现成的够用，才是「白写」感觉的真正来源。

模块本身也没全白写：给只想去掉这句提醒、不想改变包可见性的用户，它是个独立的选择；诊断版就是在这个模块的代码基础上改的，没有它，病因还定位不了。整件事没离开过手机：写码、构建、实机验证、发版、提收录全由 Codex 在 Termux 里完成，我负责提需求和验收。

边界也说清楚：反编译和 Hook 只动自己设备上的 WPS，模块只隐藏提示、不改检测结果，仓库里没有一行 WPS 的代码；发布时如实标注仅实测 Android 16 + WPS 26.9.1 + LSPosed 2.2.1，没把没验证过的组合写成已兼容。
