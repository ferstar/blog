---
title: "Enhancing Linux Touchpad Gestures: Implementing 'Three-Finger Drag'"
slug: "linux-touchpad-gestures-drag"
date: "2023-01-29T02:08:34+08:00"
tags: ['Linux', 'Rust']
series: ["Linux Experience"]
comments: true
showTableOfContents: true
description: "Linux lacks the smooth macOS-style three-finger drag; use Rust + libinput to handle gestures directly, with X11 and Wayland support; the result is low-latency, lightweight, and configurable."
---

> I am not a native English speaker; this article was translated by AI.

After switching to Linux, I kept missing one small macOS feature: three-finger drag. Years ago, many Linux laptop touchpads were barely worth the trouble, so tuning gestures felt like self-inflicted pain. Recent Windows laptops finally have decent touchpads, with larger surfaces and better tracking, so I gave it another try.

The goal was simple: make three-finger drag work well enough to keep running every day. No stutter, no fork storm, no CPU spike just because I am dragging a window around.

## First, the implementation choices

Tools like this usually take one of two paths:

1. Parse `libinput debug-events`, recognize gestures, then call tools like `xdotool` to emit keyboard or mouse events.
2. Call the `libinput` API directly and handle gestures at the event layer.

The first approach is fast to build and very script-friendly. The problem is dragging. A drag continuously emits movement events, and forwarding every tiny movement through shell commands or external processes is not going to feel great. The second approach takes more work, but it is much better for latency and resource usage.

So I went with Rust.

## Stitching together two Rust implementations

I did not plan to start from scratch. I used [riley-martin/gestures](https://github.com/riley-martin/gestures) as the base for gesture recognition, then borrowed ideas from [marsqing/libinput-three-finger-drag](https://github.com/marsqing/libinput-three-finger-drag) for the actual three-finger drag behavior. The result became this fork:

[ferstar/gestures](https://github.com/ferstar/gestures)

The rough flow looks like this:

{{< mermaid >}}
graph TD
    A[Touchpad Event] --> B{libinput}
    B --> C[ferstar/gestures <br/>Rust Engine]
    C --> D{Display Server}
    D -- X11 --> E[libxdo API]
    D -- Wayland --> F[ydotool daemon]
    E --> G[Smooth Drag / Key Stroke]
    F --> G
    
    style C fill:#f96,stroke:#333,stroke-width:2px
    style G fill:#4ecdc4,stroke:#333,stroke-width:2px
{{< /mermaid >}}

The project is now at **v0.8.1**. The main changes since the early version are:

- Automatic X11 / Wayland detection
- Direct libxdo API calls on X11, avoiding another external command layer
- ydotool integration on Wayland, with 60 FPS throttling
- A thread pool to avoid PID exhaustion in extreme cases
- Regex and event caching to reduce repeated config lookups

## How it feels in practice

The two things I care about most are drag feel and resource usage.

In a deliberately silly test where I keep dragging a window around with three fingers, this implementation stays under roughly 1% CPU. The original implementation was around 5%~10%, and some Python/Ruby-based options can go above 20%. For a small always-on desktop helper, the best state is almost invisible.

Resource usage is also modest:

- Memory usage under 5MB
- Binary size under 2MB
- No extra runtime stack dragged in

Drag speed is controlled by `acceleration`. The delay before releasing mouse down after lifting fingers is controlled by `mouse_up_delay`. That delay matters more than it sounds. Without it, a tiny finger lift can drop the window, which makes the whole interaction feel broken.

## Install dependencies

Ubuntu / Debian:

```bash
sudo apt install libudev-dev libinput-dev libxdo-dev xdotool
# For Wayland
sudo apt install ydotool
```

Arch Linux:

```bash
sudo pacman -S libinput xdotool
# Wayland
yay -S ydotool
```

## Install gestures

Download the prebuilt binary:

```bash
wget https://github.com/ferstar/gestures/releases/latest/download/gestures
chmod +x gestures
sudo mv gestures /usr/local/bin/
```

Or install from source:

```bash
cargo install --git https://github.com/ferstar/gestures.git
```

## Configuration

The config uses KDL. Here is a three-finger drag plus a four-finger workspace switch:

```kdl
// Three-finger drag (X11 & Wayland)
gesture "drag" swipe any {
    fingers 3
    acceleration 1.0      // Drag speed
    mouse_up_delay 500    // Delay after lifting fingers (ms)
}

// Four-finger swipe up to switch workspace
gesture "switch-workspace-up" swipe up {
    fingers 4
    exec "xdotool" "key" "super+Page_Up"
}
```

## Running it

I recommend installing it as a user systemd service:

```bash
# Install service file
gestures install-service

# Enable and start
systemctl --user enable --now gestures
```

If it fails with a permission error, your user probably cannot read input devices yet. Add it to the `input` group:

```bash
sudo usermod -aG input $USER
```

Log out and back in, then try again.

## Links

- GitHub: https://github.com/ferstar/gestures
- Releases: https://github.com/ferstar/gestures/releases
- Issues: https://github.com/ferstar/gestures/issues

This is one of those tiny desktop tools that becomes hard to give up once it works. Linux desktop experience is often held back by small rough edges like this. None of them looks huge alone, but they get annoying when you hit them every day. Fix one, move on to the next.
