---
title: "I Rebuilt RustDesk with tailcat for Scan-to-Connect Remote Desktop"
slug: "yet-another-remote-desktop-application-sealdesk"
date: "2026-10-16T22:30:00+08:00"
tags: ["Rust", "P2P", "Remote Desktop", "Tailscale", "Open Source", "Security"]
series: ["Open Source Projects"]
description: "Self-hosting RustDesk means renting a public VPS to run hbbs and hbbr, and public relays are often throttled or unreliable; SealDesk swaps the transport for tailcat—zero config, no account, no server to set up, scan to connect, P2P-first sessions inside end-to-end encrypted tunnels; the post breaks down the architecture changes, the C-ABI bridge, NAT traversal, and the engineering trade-offs."
---

> I am not a native English speaker; this article was translated by AI.

Yesterday I open-sourced SealDesk: the RustDesk transport swapped for tailcat. The host taps share, the controller scans a code, and it connects.

RustDesk's public servers aren't always good, and self-hosting means renting a VPS and running `hbbs` and `hbbr`. SealDesk removes that setup, and there's no account to register either.

## How the Two Ends Find Each Other Without a Server

The trigger for this project was Tailscale open-sourcing [tailcat](https://github.com/tailscale/tailcat). Tailscale's NAT traversal and WireGuard mesh are great to use, but the standard setup depends on a coordination server (the hosted SaaS or a self-run Headscale) for authentication, node distribution, and ACLs. tailcat peels the data plane out as a standalone library: no account system, no control plane, just peer-to-peer transport itself.

The `tc` address is the complete connection credential. On startup, the server generates a Base64 string starting with `tc`, around 150 characters long; it packages the WireGuard public key, the pre-shared key (PSK), and the DERP region used for rendezvous. Every piece of cryptographic material the two ends need to find and authenticate each other lives in that one string.

The two ends meet on a public DERP node using this address. As soon as STUN/UDP hole punching succeeds, traffic switches to a direct WireGuard UDP tunnel; only in genuinely untraversable setups such as symmetric NAT does DERP fall back to forwarding ciphertext, which it cannot decrypt. That rendezvous relay is Tailscale's public DERP, so there's nothing to host, and `hbbs` / `hbbr` can be removed outright.

## After the Scan

The handshake never touches a central server; the pairing code just carries the `tc` address and temporary password over to the controller:

{{< mermaid >}}
flowchart TD
    subgraph Host
        H1[Start tailcat Listener] --> H2[Generate tc... Address + Password]
        H2 --> H3[Render SEALDESK: Pairing QR Code]
        H3 --> H4[Wait for DERP Rendezvous Beacon]
    end

    subgraph Controller
        C1[Scan QR / Load Image / Paste Code] --> C2[Parse tc Address & Temporary Password]
        C2 --> C3[Dial tailcat Transport]
    end

    subgraph Handshake & Tunnel
        C3 & H4 --> D1[Rendezvous Handshake via Public DERP]
        D1 --> D2{STUN/UDP Hole Punching}
        D2 -->|Punch Succeeded| D3[Direct P2P WireGuard Tunnel]
        D2 -->|Symmetric NAT| D4[Fallback Encrypted DERP Forwarding]
    end

    D3 & D4 --> R[RustDesk Desktop Session: Auth, Video/Audio Stream, Input Injection]
{{< /mermaid >}}

The host opens the app and taps "Share this device"; the pairing QR code sits front and center. The controller scans it with a phone, or on desktop uses the webcam, picks a QR image file, or pastes a screenshot from the clipboard. On the same LAN the two ends find each other without touching the internet—approve the first request at the host, tick "Trust this device," and it connects straight in next time.

The temporary password can be refreshed and the address reset; old pairing codes stop working once either changes. Stop sharing on either end and every session closes; nothing keeps running in the background.

## The C-ABI Between Go and Rust

tailcat is pure Go; the RustDesk core is Rust. In `libs/tailcat-ffi`, we wrapped a minimal C-ABI with cgo: the host calls `TcServe` with the local RustDesk loopback port—every tunnel connection is forwarded to it—and gets back the generated `tc...` address; the controller calls `TcForward` with the peer address, which opens a local forward port; connect to it and you're inside the tunnel. All returned strings are freed through `TcFree`, so pointers crossing the FFI boundary don't leak.

Android took an extra step: Go 1.27.1's `-buildmode=c-archive` returns "not supported" on android/arm64, so the build switches to c-shared and the Rust side links against `libtailcat.so` accordingly.

## Bypassing rendezvous_mediator

Upstream RustDesk couples its networking tightly to `rendezvous_mediator`: before connecting, the client queries the central server for the peer's direct IP list or relay endpoint. In `src/client.rs`, `src/tailcat.rs`, and `src/client/io_loop.rs`, we added a dedicated tailcat branch: whenever the peer is a `tc...` address, all centralized resolution is skipped and the desktop stream rides the tailcat-encrypted connection. RustDesk's battle-tested codecs (H.264/H.265/VP9) and input injection pipeline stay untouched.

## Android Drops the Session When the Network Switches

Controllers routinely hop between Wi-Fi and cellular, and on a switch the path update can't keep up, so the session tends to drop. Android also denies netlink to app UIDs, so the Go-side netmon cannot enumerate network interfaces on its own and depends on the app layer to feed them in. In `libs/tailcat-ffi/android_interfaces.go`, we added `TcSetAndroidInterfaces`: the Kotlin layer reads interface names and addresses via `java.net.NetworkInterface`, and every connectivity change pushes them as JSON over JNI, registering them with netmon—so a mobile session doesn't reconnect on every hop.

## Platforms and Limits

CI and packaging across platforms are now in place. Multi-platform binaries are attached to the release page: Windows (`.exe` / `.msi`), macOS (`.dmg`), Linux (`.deb` / `.rpm` / `.AppImage`), and Android (`.apk`). Desktop-to-desktop connections work in both directions; Android currently acts primarily as a controller, and there is no iOS build.

Because the macOS build is not notarized with an Apple Developer certificate, Gatekeeper may block the first launch. You can strip the quarantine attribute in your terminal:

```bash
xattr -cr /Applications/SealDesk.app
```

Interoperating with upstream RustDesk uses its legacy direct-connection protocol (raw TCP 21118 stream without tailcat's WireGuard tunnel), so that path is unencrypted, and SealDesk pops a warning before connecting.

SealDesk lives under [runseal-labs](https://github.com/runseal-labs) (the "Seal" in the name is that sealed isolation between the two ends). The repository is at [github.com/runseal-labs/sealdesk](https://github.com/runseal-labs/sealdesk), and installers are available under [Releases](https://github.com/runseal-labs/sealdesk/releases). If you're tired of babysitting `hbbs` and `hbbr`, give it a spin; issues and PRs are welcome.
