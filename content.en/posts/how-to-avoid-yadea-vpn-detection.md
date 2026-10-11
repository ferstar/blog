---
title: "It Doesn't Use the VPN, but You're Not Allowed to Either: How I Fixed Yadea's VPN Detection"
slug: "how-to-avoid-yadea-vpn-detection"
date: "2026-10-11T21:45:00+08:00"
tags: ["Android", "KernelSU", "LSPosed", "VPN", "Yadea"]
series: ['Android Root']
description: "Opening the Yadea app with a VPN on triggers a 'VPN environment detected' warning, then the app exits outright; the app hides behind 360 Jiagu packing with anti-hook defenses, so the in-process diagnostics from my previous post all failed. The measured truth is even more annoying: Yadea's own traffic never goes through the VPN, yet it still polices your whole phone's network. VPN Hide finally solved it — filtering VPN traces at the system_server Binder layer and via a kernel module, for Yadea alone — and cold starts went back to normal. The detection was stopped at a layer it cannot see."
---

> I am not a native English speaker; this article was translated by AI.

Right after dealing with [the WPS root warning](/en/posts/how-to-avoid-wps-root-detection/), it was Yadea's turn. Opening the Yadea app with a VPN on shows "检测到VPN环境，请调整网络" ("VPN environment detected, please adjust your network"), and then the app exits. You can't even get to the vehicle page.

WPS at least only showed a reminder; Yadea just refuses to work. What's more absurd is that Yadea's own traffic doesn't go through the VPN at all. Whether my VPN is on has nothing to do with its network, but it insists on checking anyway.

## Symptoms

logcat makes it clear: the main process logs "检测到VPN环境,请调整网络" and then exits on its own. The `:pushservice` push process shows the same message.

I wanted to unpack the APK, but Yadea 8.8.12 is packed with 360 Jiagu. Unpacking it only gives the shell code; the business logic isn't visible.

## In-process hooks blocked by the packer

For WPS, I used a temporary LSPosed diagnostic module that hooked the detection method inside the process and logged return values. On Yadea, the packer noticed during initialization and the app kept exiting before reaching the business code; removing the module brought back the original VPN warning. In-process hooking was a dead end. I also tried Frida, but it had version compatibility problems and never ran.

## Code dumped from memory

Since the static route was blocked, I let the app decrypt itself at runtime. After a normal start, I dumped the business DEX from memory and could finally read the code.

Following the network checks led to an interface-enumeration routine in the Getui push SDK that looks for VPN interfaces like `tun0` and `ppp0`. But there's no evidence that this is what shows the warning, and I never caught which API triggers it, so I won't draw a conclusion.

What I could confirm is something else. Yadea's UID is `10450`. It's not in the list of UIDs the VPN covers, and not in the VPN client's per-app list either; its traffic was direct all along. So setting Yadea to bypass the VPN in the client doesn't help: it checks whether the phone has a VPN at all, regardless of how its own traffic is routed. WPS checked which apps were installed; Yadea polices the whole phone's network state, which reaches even further.

## Handling it outside the process

Since nothing can be done inside the process, the data has to be changed somewhere the app can't see. [VPN Hide](https://github.com/okhsunrog/vpnhide) does exactly this, on two layers:

- **Java layer**: the LSPosed module hooks system_server. At Binder's `writeToParcel`, it removes VPN information from `NetworkCapabilities`, `NetworkInfo`, and `LinkProperties`, so the network data the app gets over IPC contains no VPN. Nothing is injected into Yadea's process, so the packer's anti-hook and memory-integrity checks don't notice.
- **Native layer**: a kernel module (kmod, based on kprobe/kretprobe) hides the `tun` interface in the kernel. Interface-enumeration ioctls, `getifaddrs`, and netlink route dumps are all filtered, so native code can't find it either. The backend can be kmod, KPM, or Zygisk. Zygisk does inline hooks inside the process and may be caught by the packer; this phone's kernel supports kmod, so I used kmod.

{{< mermaid >}}
flowchart TD
    Y["Yadea app (360 Jiagu pack + anti-hook)"]
    Y -->|"in-process hook injection"| X["Packer detects it, repeated exits ✗"]
    Y -->|"Java API network queries"| S["system_server<br/>VPN Hide: Binder-layer filtering ✓"]
    Y -->|"native interface/route enumeration"| K["Kernel<br/>VPN Hide kmod: tun0 hidden ✓"]
{{< /mermaid >}}

kmod doesn't require flashing the kernel or modifying the boot image; the KernelSU module loads a `.ko` into the existing kernel at boot. But it does change the running kernel's behavior: if it's incompatible, the system may crash, and after uninstalling it you need another reboot to fully restore things.

The configuration enables Java and native hiding for `com.yadea.smartmoto` only, with the LSPosed scope set to the system framework, not Yadea.

## Result

After rebooting to load the kernel module, with NekoBox connected, Yadea cold-started twice in a row straight into the vehicle home page. No VPN warning, no exit.

VPN Hide has a statistics page. I recorded for 43 seconds, cold-starting Yadea once during that window, and it logged 156 interceptions:

| Query type | Count |
|---|---|
| Native ioctl network interface queries | 130 |
| IPv4 / IPv6 address enumeration | 3 each |
| Java `NetworkInfo` | 12 |
| Java `Network` handles | 5 |
| Java `ConnectivityService` | 3 |

Most of it is native ioctl interface queries. That path returns the interface list, addresses, and up/down state, which is enough to spot VPN interfaces like `tun0`. Filtering only at the Java layer can't block these queries, which is why kmod has to be enabled as well. These counts also include normal network calls, though, so they don't mean Yadea deliberately checked for a VPN 156 times, and the stats alone can't identify which call triggered the warning.

VPN Hide's own status page shows "no check needed", which looks like it isn't working. It's actually because VPN Hide itself doesn't go through the VPN, so that's the expected display.

VPN Hide only handles VPN traits that can be queried on the phone. It doesn't hide root or deal with Play Integrity. Server-side checks such as DNS leaks, IP blacklists, and TLS fingerprinting are out of its reach.

## Compared with WPS

| | WPS | Yadea |
|---|---|---|
| What it checks | whether a root manager is installed | whether the phone has a VPN |
| Is the check protected | no | packing + anti-hook |
| After a hit | shows a toast | shows a warning, then exits |
| Where it was fixed | package visibility (HMA) | system_server + kernel (VPN Hide) |

WPS's check sits in the app layer without protection, so hiding the package name with HMA was enough. Yadea's check is behind a packer and can't be touched in-process, so the only option was to go down to system_server and the kernel and change the data it receives.

Unpacking, dumping memory, reading decompiled code, picking a kernel module: in the past, even a professional wouldn't have found it worth this much effort for one vendor app's unreasonable restrictions, and ordinary users just had to put up with it. With AI's help, ordinary people can get this done too, and finally decide for themselves how to use their own phones.
