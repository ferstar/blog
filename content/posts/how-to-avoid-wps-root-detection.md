---
title: "你关的是开关，它开的是名单：WPS 是怎么查到我 Root 的"
slug: "how-to-avoid-wps-root-detection"
date: "2026-10-11T17:50:00+08:00"
tags: ["Android", "LSPosed", "KernelSU", "WPS", "Root"]
series: ['Android Root']
description: "root 手机上每次打开 WPS 都弹「设备已Root」警告，先写了个 LSPosed 模块精确拦截这条 Toast 还发布到了模块仓库；反编译挖出六项检测链，进程内实测命中的是 KernelSU 包名查询——明明拒绝了「读取应用列表」权限，WPS 靠 Manifest 里的 <queries> 声明照样查得到；最后用 Hide My Applist 对 WPS 隐藏管理器包名，检测在源头失效。"
---

买了个手机，不 root 感觉跟租的一样，所以我 root 了。结果 WPS 不知道从哪个版本开始，手越伸越长，连我 root 没 root 都要管：每次从桌面打开它，首页先弹一句「设备已Root，使用WPS Office可能存在安全风险。」一秒就消失，连通知历史都不留。最恶心的是，我明明拒绝了它的「读取应用列表」权限，它还是检测到了我装的 KernelSU。

## 这句警告为什么关不掉

这东西压根没走通知栏，是进程里直接调用的 Toast，通知权限管不着，通知历史不留痕，WPS 设置里也翻不到开关。把 KernelSU 对 WPS 的「卸载模块」打开，照弹不误。

后来看了检测代码才知道为什么没用：这台手机根本不是因为 su 文件或挂载点被查出来的，动文件层自然白搭。不过当时还不知道，只想先让这句话闭嘴。

## 先让这一句消失

先试了现成的 [ToastBlocker](https://github.com/h465855hgg/toastblocker)，作用域只勾 WPS。警告是没了，「保存成功」这类正常提示也跟着没了。

想拦得准一点，写轮眼（MyAndroidTools）那套组件开关用不上，这句警告不是单独的 Activity、Service 或 Receiver，调用点在首页 `HomeControllerImpl$1$1.run()` 里，检测完直接调 Toast。只拦这一句，就只能上方法级 Hook，也就是 LSPosed。

于是写了个模块，规则只有一条：整句精确匹配那句警告（忽略排版空白），其他 Toast 照常显示，WPS 的检测结果也不动。实现上通过公开的 `Toast.makeText/setText` 认内容，标记命中的 Toast 对象，只跳过它的 `show()`，不去读 Android 16 已经限制访问的隐藏字段 `Toast.mText`。第一版用 legacy API 在实机上验证过，发布前又迁到 libxposed API 102 的 interceptor chain 重写了一遍。构建、签名、发布都走 GitHub Actions，[wps-root-toast](https://github.com/ferstar/wps-root-toast) 1.0.0 已经进了 [LSPosed 模块仓库](https://github.com/Xposed-Modules-Repo/io.github.ferstar.wpsroottoast)。

警告是不弹了，但检测还在跑，只是看不见结果。

## WPS 怎么判定「已 Root」

把 WPS 26.9.1 拆开，首页用的判定在 `KSystemRoot.i(context)`，六项检查按顺序走，任何一项命中就返回 true。

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

另外还有两处独立检测：`LogoutTracker.h()` 查两个固定路径的 `su`；`GetDeviceInfoHandler.a()` 查 `/system/bin/su` 和 `/system/xbin/su`，结果放进设备信息的 `root` 字段，通过 JS 回调返回。光看代码看不出会不会上传到服务器，这里不下结论。

代码只能说明有这六项，看不出我这台手机命中的是哪一项。于是临时改了个诊断版，hook 检测方法本身，只记录每一项的返回值，装上冷启动一次：

| 检测项 | 本机实测 |
|---|---|
| PATH 各目录下的 `su` 文件 | false |
| `persist.sys.root.status` 属性 | false |
| `ro.secure=0` | false |
| `Build.TAGS` 含 `test-keys` | false |
| 模拟器特征（`goldfish`、`ranchu`、`sdk_gphone` 等） | false |
| 查询 `me.weishu.kernelsu` | **true** |
| 最终判定 | **true** |

前五项都是 false，命中的是第六项，查 KernelSU 管理器的包名。前面藏 su、改属性之所以没用，也是因为碰的都不是这一项。测完把诊断版卸了，换回正式模块。

## 权限被拒，为什么还查得到

我确实没给 WPS「读取应用列表」权限，它照样查到了 KernelSU，因为这是两套机制。

厂商设置里的「读取应用列表」管的是枚举设备上的全部应用。Android 11 之后的包可见性机制允许 App 在 Manifest 的 `<queries>` 里点名一批包名，点了名的包不需要任何运行时权限就能查装没装。WPS 的 `<queries>` 里就列着 KernelSU、Magisk、APatch，系统的可见性记录也显示这两个包互相可见。所以权限面板上点的「拒绝」，对这种点名查询根本不起作用。

这套判定也配不上「安全风险」这个说法：装了管理器 App 就算命中，根本不看 WPS 自己能不能拿到 root；模拟器特征也算 Root，用模拟器的人大概也想不到会被这么提醒一句。

## 让查询返回「未安装」

既然查的是包名，那让 WPS 查不到这个包就行。可选的做法有三种：

| 方案 | 做法 | 代价 |
|---|---|---|
| 应用列表隐藏类模块 | 对 WPS 隐藏指定包名 | 多数基于旧 API，新系统兼容性要实测 |
| 扩展现有模块 | 在 WPS 进程里拦截包查询，返回「未安装」 | 要自己写、自己维护 |
| 改 APK 删 `<queries>` | 重签名后安装 | 影响更新和签名校验，不适合日常 |

本来打算再写一个 API 102 的包可见性过滤模块，后来发现 [Hide My Applist](https://modules.lsposed.org/module/com.tsng.hidemyapplist/)（HMA）干的就是这事，就没必要自己写了。

配置只有两条：建一个黑名单模板，里面只放 `me.weishu.kernelsu`；应用规则只对 WPS 生效，激进过滤和详细日志都不开。验证时先把「WPS Root 提示隐藏」模块关掉，强停后重开 WPS，没再弹。说明包名查询直接被挡住了，六项检测都返回 false。其他入口如果也用同一套判定，一样会失效，原来的模块只能遮住首页这一处。

HMA 3.8.3 用的是 libxposed API 101，还要求框架允许在系统服务里加载原生库，我这套 Android 16 + LSPosed 2.2.1 上实测正常。

## 模块白写了吗

回头看，确实该先找找现成方案再动手。不过不把六项检测挖出来，也不知道触发点是包名查询，更想不到 HMA 一个模板就能解决。

[wps-root-toast 仓库](https://github.com/ferstar/wps-root-toast)现已归档，README 保留了 HMA 的实测配置，源码和已发布 APK 也保留供查阅。

模块也不算完全白写。只想去掉这句提醒、不想改包可见性的话，它还能单独用；诊断版也是在它的代码上改出来的。

反编译和 Hook 都只在自己手机上的 WPS 里做，模块只隐藏提示、不改检测结果，仓库里没有 WPS 的代码。发布说明里也只写了实测过的 Android 16 + WPS 26.9.1 + LSPosed 2.2.1。

后来雅迪也开始管 VPN，而且检测藏在加固后面，处理过程写在[下一篇](/posts/how-to-avoid-yadea-vpn-detection/)。
