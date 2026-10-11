---
title: "You Turn Off the Switch, It Opens the List: How WPS Knew My Phone Was Rooted"
slug: "wps-root-detection-loophole"
date: "2026-10-11T17:50:00+08:00"
tags: ["Android", "LSPosed", "KernelSU", "WPS", "Root"]
description: "Every launch of WPS on my rooted phone showed a 'device is rooted' warning. I first wrote and published an LSPosed module that intercepts exactly that one toast; decompiling WPS revealed a six-check detection chain, and in-process instrumentation proved the hit was a KernelSU package-name query — one that succeeds even with the 'app list' permission denied, thanks to a `<queries>` declaration in the Manifest. Hide My Applist finally made the query return 'not installed', killing the detection at its source."
---

> I am not a native English speaker; this article was translated by AI.

I bought this phone, but without root it felt like I was renting it, so I rooted it. In return, WPS — somewhere along its release history, I honestly can't tell which version — kept reaching further, to the point of caring whether my phone is rooted: every time I open it from the launcher, the home page greets me with "设备已Root，使用WPS Office可能存在安全风险。" ("This device is rooted; using WPS Office may pose security risks.") — a toast that vanishes in a second and leaves no trace in notification history. The most disgusting part: I had denied its "read app list" permission, and it still detected the KernelSU I had installed.

## Why the warning can't be turned off

It doesn't go through the notification system at all; it's a toast fired directly from the app's own process. Notification permissions don't apply, notification history keeps no record, and WPS's own settings offer no switch. I enabled KernelSU's "unmount modules" option for WPS — the warning still showed.

Only after locating the detection code did it become clear why none of this worked: on this phone the check was never tripped by su files or mounts, so touching the file layer was pointless. But that came later; the immediate goal was just to shut the message up.

## Making just that one toast disappear

The Codex agent running in Termux started with the existing [ToastBlocker](https://github.com/h465855hgg/toastblocker), scoped to WPS only. The warning was gone — but so were normal toasts like "saved", the cure was too strong.

Getting more precise hit a wall first: the warning is not a component you can disable. MyAndroidTools and its per-component toggles are useless here, because the call site is plain code inside `HomeControllerImpl$1$1.run()` on the home page, which runs the check and fires a Toast directly. Intercepting exactly one sentence requires method-level hooking — LSPosed territory.

So a module got written, with a single rule: exact-match the full warning sentence (ignoring layout whitespace), let every other toast through, and leave WPS's root detection result untouched. The implementation identifies content via the public `Toast.makeText/setText`, marks the matching Toast object, and skips only its `show()` — it never touches the hidden `Toast.mText` field that Android 16 already restricts. The first version used the legacy API and passed on-device verification; I wasn't going to ship on a deprecated API, so it was rewritten on libxposed API 102's interceptor chain. Build, signing, and release all ran through GitHub Actions, and [wps-root-toast](https://github.com/ferstar/wps-root-toast) 1.0.0 made it into the [LSPosed module repository](https://github.com/Xposed-Modules-Repo/io.github.ferstar.wpsroottoast).

At this point the warning was gone for good. But everyone understood this wasn't a fix — the detection still ran; its result was just invisible now.

## How WPS decides a device is rooted

Cracking WPS 26.9.1 open showed that the home-page verdict converges on one method, `KSystemRoot.i(context)`, which walks six checks in order and returns true if any of them hits.

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

Beyond this main chain there are two independent checks: `LogoutTracker.h()` looks for `su` at two fixed paths, and `GetDeviceInfoHandler.a()` checks `/system/bin/su` and `/system/xbin/su`, feeding the result into a `root` field of the device info that is returned via a JS callback. Nothing in the code alone proves whether it gets uploaded to a server, so I make no claim there.

The code only proves the six checks exist; it can't tell which one my phone tripped. So a temporary diagnostic build hooked the detection method itself and only logged each return value. Installed, one cold start:

| Check | Measured result |
|---|---|
| `su` file in PATH directories | false |
| `persist.sys.root.status` property | false |
| `ro.secure=0` | false |
| `Build.TAGS` contains `test-keys` | false |
| Emulator traits (`goldfish`, `ranchu`, `sdk_gphone`, etc.) | false |
| Query for `me.weishu.kernelsu` | **true** |
| Final verdict | **true** |

The first five were all clean; the hit was number six: the package-name query for the KernelSU manager. Which also explains every earlier failure — the su-file and system-property approaches never touched the actual trigger. After the test, the diagnostic build was removed and the release module restored.

## Denied the permission, but still detected

This is the part that stings. I had indeed denied WPS the "read app list" permission, and it still found KernelSU — because these are two separate mechanisms:

The vendor's "read app list" toggle governs enumerating all apps on the device. Package visibility since Android 11, on the other hand, lets an app name a list of packages in its Manifest's `<queries>`; for those named packages, checking whether they're installed requires no runtime permission at all. WPS's `<queries>` lists KernelSU, Magisk, and APatch, and the system's own visibility records confirmed the two packages were mutually visible. That "deny" in the permission panel has no effect on named queries — the sense of control the switch gives you is an illusion.

The judgment quality of this chain also doesn't live up to the words "security risk": merely having a manager app installed counts as a hit, without ever checking whether WPS could actually obtain root; and emulator traits count as rooted too — emulator users probably don't expect to be greeted like this.

## Making the query return "not installed"

Once the goal shifted from "can't see the warning" to "can't find the package", the options became clear:

| Option | Approach | Cost |
|---|---|---|
| App-list hiding module | Hide chosen package names from WPS | Mostly older APIs; needs on-device testing on new Android |
| Extend my module | Intercept package queries in WPS's process, return "not installed" | Write and maintain it myself |
| Patch the APK, strip `<queries>` | Re-sign and install | Breaks updates and signature checks; not for daily use |

I was already gearing up to write another module — an API 102 package-visibility filter, complete with a settings page where users could pick additional packages to hide. Right before starting, one extra question got asked: "does an existing module already do this?" One does: [Hide My Applist](https://modules.lsposed.org/module/com.tsng.hidemyapplist/) (HMA) does exactly this job.

The configuration stays minimal, just two entries: a blacklist template containing only `me.weishu.kernelsu`, and an app rule applying that template to WPS alone. Aggressive filtering and verbose logging stay off. To verify, I turned the "WPS Root 提示隐藏" module off, force-stopped WPS, and reopened it — no warning. That means the package query was blocked at the source and the six-check chain returned false, rather than the toast merely being hidden; the former also neutralizes the same check behind other entry points, while the latter only covers this one spot.

HMA 3.8.3 targets libxposed API 101 and additionally requires the framework to allow native library loading inside system_server; on my Android 16 + LSPosed 2.2.1 setup it works fine.

## Was the module a waste?

"Felt like I wrote that module for nothing." Codex's own post-mortem was that it should have searched for existing solutions before writing code — fair. But the more important ordering question is symptom relief versus diagnosis. Without digging out the six-check chain, we wouldn't have known the trigger was a package-name query, and the idea that a single HMA template could cure it would never have surfaced. The "wasted work" feeling really comes from discovering, after the diagnosis, that the existing arsenal was already sufficient.

The module wasn't entirely wasted either: for people who only want that one warning gone without changing package visibility, it remains an independent option; and the diagnostic build was derived from its code — without it, the root cause would still be unlocated. The whole thing closed the loop on the phone: writing code, building, on-device verification, releasing, and the repository submission were all done by Codex in Termux; I filed the requirements and accepted the results.

The boundaries, stated plainly: decompiling and hooking touched only the WPS on my own device; the module hides a toast and does not alter detection results, and the repository contains no WPS code. The release notes honestly state that only Android 16 + WPS 26.9.1 + LSPosed 2.2.1 have been tested — no untested combination is claimed as compatible.
