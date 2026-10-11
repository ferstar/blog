---
title: "You Turn Off the Switch, It Opens the List: How WPS Knew My Phone Was Rooted"
slug: "how-to-avoid-wps-root-detection"
date: "2026-10-11T17:50:00+08:00"
tags: ["Android", "LSPosed", "KernelSU", "WPS", "Root"]
series: ['Android Root']
description: "Every launch of WPS on my rooted phone showed a 'device is rooted' warning. I first wrote and published an LSPosed module that intercepts exactly that one toast; decompiling WPS revealed a six-check detection chain, and in-process instrumentation proved the hit was a KernelSU package-name query — one that succeeds even with the 'app list' permission denied, thanks to a `<queries>` declaration in the Manifest. Hide My Applist finally made the query return 'not installed', killing the detection at its source."
---

> I am not a native English speaker; this article was translated by AI.

I bought this phone, but without root it felt like I was renting it, so I rooted it. Then WPS, starting from some version I can't pin down, began caring whether my phone is rooted: every time I open it from the launcher, the home page shows "设备已Root，使用WPS Office可能存在安全风险。" ("This device is rooted; using WPS Office may pose security risks.") It disappears after a second and leaves nothing in notification history. The worst part: I had denied its "read app list" permission, and it still detected KernelSU.

## Why the warning can't be turned off

It doesn't go through the notification shade. It's a Toast called directly from the app process, so notification permissions don't apply, notification history keeps nothing, and WPS's settings have no switch for it. Turning on KernelSU's "unmount modules" for WPS didn't help either.

Reading the detection code later explained why: this phone wasn't being flagged by su files or mount points, so touching the file layer was pointless. At the time I didn't know that, and just wanted the message gone.

## Hiding just this one message

I first tried the existing [ToastBlocker](https://github.com/h465855hgg/toastblocker), scoped to WPS only. The warning was gone, but so were normal toasts like "saved".

To be more precise, MyAndroidTools' component toggles were no use: the warning isn't a separate Activity, Service, or Receiver. The call site is inside `HomeControllerImpl$1$1.run()` on the home page, which runs the check and calls Toast directly. Blocking only this sentence needs a method-level hook, which means LSPosed.

So I wrote a module with a single rule: exact-match the whole warning sentence (ignoring layout whitespace), let every other Toast through, and leave WPS's detection result alone. It identifies the content through the public `Toast.makeText/setText`, marks the matching Toast object, and skips only its `show()`, without reading the hidden `Toast.mText` field that Android 16 restricts. The first version used the legacy API and was verified on the device; before release it was rewritten on libxposed API 102's interceptor chain. Build, signing, and release run on GitHub Actions, and [wps-root-toast](https://github.com/ferstar/wps-root-toast) 1.0.0 is now in the [LSPosed module repository](https://github.com/Xposed-Modules-Repo/io.github.ferstar.wpsroottoast).

The warning no longer shows, but the detection still runs; its result is just hidden.

## How WPS decides a device is rooted

In WPS 26.9.1, the home-page check is `KSystemRoot.i(context)`. It runs six checks in order and returns true as soon as one hits.

{{< mermaid >}}
flowchart TD
    A["KSystemRoot.i(context)"] --> B1{"su file exists in any PATH directory?"}
    B1 -->|hit| T["Rooted"]
    B1 -->|miss| B2{"persist.sys.root.status set and not 0?"}
    B2 -->|hit| T
    B2 -->|miss| B3{"ro.secure is 0?"}
    B3 -->|hit| T
    B3 -->|miss| B4{"Build.TAGS contains test-keys?"}
    B4 -->|hit| T
    B4 -->|miss| B5{"fingerprint or model shows emulator traits?"}
    B5 -->|hit| T
    B5 -->|miss| B6{"root manager package name found?"}
    B6 -->|hit| T
    B6 -->|miss| F["Not rooted"]
    T --> S["Home-page toast: device is rooted, security risk"]
    style B6 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
{{< /mermaid >}}

There are also two separate checks: `LogoutTracker.h()` looks for `su` at two fixed paths, and `GetDeviceInfoHandler.a()` checks `/system/bin/su` and `/system/xbin/su`, puts the result into the `root` field of the device info, and returns it through a JS callback. The code alone doesn't show whether this is uploaded to a server, so I won't draw a conclusion.

The code only shows that these six checks exist, not which one my phone hits. So I made a temporary diagnostic build that hooks the detection method itself and only logs each return value, installed it, and did one cold start:

| Check | Measured result |
|---|---|
| `su` file in PATH directories | false |
| `persist.sys.root.status` property | false |
| `ro.secure=0` | false |
| `Build.TAGS` contains `test-keys` | false |
| Emulator traits (`goldfish`, `ranchu`, `sdk_gphone`, etc.) | false |
| Query for `me.weishu.kernelsu` | **true** |
| Final verdict | **true** |

The first five were false; the hit was number six, the package-name query for the KernelSU manager. That's also why hiding su and changing properties didn't help: none of them touched this check. After the test I removed the diagnostic build and reinstalled the release module.

## The permission was denied, so why does the query work?

I really hadn't given WPS the "read app list" permission, and it still found KernelSU, because these are two separate mechanisms.

The vendor's "read app list" setting controls enumerating all apps on the device. Package visibility, introduced in Android 11, lets an app name packages in the Manifest's `<queries>`, and for those named packages it can check whether they're installed without any runtime permission. WPS's `<queries>` lists KernelSU, Magisk, and APatch, and the system's visibility records show the two packages as mutually visible. So tapping "deny" in the permission panel does nothing against these named queries.

This check also doesn't justify the words "security risk": having a manager app installed counts as a hit, without checking whether WPS could actually get root; emulator traits count as rooted too, which emulator users probably wouldn't expect.

## Making the query return "not installed"

Since the check is a package-name query, WPS just needs to not find the package. There were three options:

| Option | Approach | Cost |
|---|---|---|
| App-list hiding module | Hide chosen package names from WPS | Mostly older APIs; needs on-device testing on new Android |
| Extend my module | Intercept package queries in WPS's process, return "not installed" | Write and maintain it myself |
| Patch the APK, strip `<queries>` | Re-sign and install | Breaks updates and signature checks; not for daily use |

I was planning to write another API 102 package-visibility filter module, then found that [Hide My Applist](https://modules.lsposed.org/module/com.tsng.hidemyapplist/) (HMA) already does exactly this, so there was no need.

The configuration has two entries: a blacklist template containing only `me.weishu.kernelsu`, and an app rule applying it to WPS only, with aggressive filtering and verbose logging off. To verify, I turned off the "WPS Root 提示隐藏" module, force-stopped WPS, and reopened it: no warning. The package query was blocked and all six checks returned false. Other entry points using the same check fail the same way, while the original module only covered the home page.

HMA 3.8.3 targets libxposed API 101 and requires the framework to allow loading native libraries in system services. It works on my Android 16 + LSPosed 2.2.1 setup.

## Was the module a waste?

Looking back, I should have searched for existing solutions first. But without digging out the six checks, I wouldn't have known the trigger was a package-name query, let alone that one HMA template would fix it.

The [wps-root-toast repository](https://github.com/ferstar/wps-root-toast) is now archived. Its README includes the tested HMA configuration, and the source and released APK remain available for reference.

The module isn't entirely wasted. If you only want this warning gone without changing package visibility, it still works on its own, and the diagnostic build was made from its code.

Decompiling and hooking were only done on the WPS on my own phone. The module only hides the toast and doesn't change detection results, and the repository contains no WPS code. The release notes only list the tested combination: Android 16 + WPS 26.9.1 + LSPosed 2.2.1.

Later Yadea started policing VPNs too, with its check hidden behind a packer. That one is in the [next post](/en/posts/how-to-avoid-yadea-vpn-detection/).
