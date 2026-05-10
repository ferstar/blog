---
title: "Linux触控板手势增强之「三指拖拽」"
slug: "linux-touchpad-gestures-drag"
date: "2023-01-29T02:08:34+08:00"
tags: ['Linux', 'Rust']
comments: true
showTableOfContents: true
description: "Linux 触控板缺少 macOS 那种顺手的三指拖拽；用 Rust + libinput 直接处理手势，并分别适配 X11/Wayland；最终做到低延迟、低占用、可配置。"
series: ["Linux Experience"]
---

转用 Linux 之后，我一直惦记 macOS 上那个很顺手的三指拖拽。以前很多 Linux 本子的触控板实在一言难尽，折腾手势多少有点自找罪受。这几年 Windows 本子的触控板终于像个正经外设了，面积、跟手性都上来了，于是又动了这个念头。

目标很简单：在 Linux 上做一个能长期挂着用的三指拖拽。不要卡，不要疯狂 fork，不要一拖窗口 CPU 就起飞。

## 先看实现路线

这类工具大概有两条路：

1. 解析 `libinput debug-events` 输出，识别手势后再调用 `xdotool` 之类的工具去发键盘、鼠标事件。
2. 直接调用 `libinput` API，在事件层处理手势。

第一种写起来快，脚本味也重。问题是拖拽这种动作会持续产生位移事件，如果每一小段都靠 shell 命令或者外部进程去转发，体验很难好。第二种麻烦一点，但性能和延迟都更像正路。

所以最后我选了 Rust。

## 缝了两个 Rust 实现

一开始没打算从零写。先拿 [riley-martin/gestures](https://github.com/riley-martin/gestures) 做手势识别基础，再参考 [marsqing/libinput-three-finger-drag](https://github.com/marsqing/libinput-three-finger-drag) 处理三指拖拽。最后缝成了这个 fork：

[ferstar/gestures](https://github.com/ferstar/gestures)

大体链路是这样：

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

现在项目已经到 **v0.8.1**，主要补了这些东西：

- X11 / Wayland 自动检测
- X11 下直接走 libxdo API，少一层外部命令
- Wayland 下接 ydotool，并做了 60 FPS 节流
- 线程池限制并发，避免极端情况下 PID 被打爆
- 正则缓存和事件缓存，减少重复配置查找

## 实际表现

我最关心的还是拖拽手感和资源占用。

极端一点测试，疯狂三指拖拽窗口，本实现 CPU 基本压在 1% 以内。原始实现大概 5%~10%，一些 Python/Ruby 方案能到 20%+。这类常驻小工具，平时存在感越低越好，最好像没运行一样。

资源也比较克制：

- 内存占用不到 5MB
- 二进制不到 2MB
- 没有一串额外 runtime 依赖

拖拽速度可以通过 `acceleration` 调，抬手后继续保持 mouse down 的时间可以通过 `mouse_up_delay` 调。这个延迟很关键，不然手指稍微离开一下，窗口就掉了，体验会很割裂。

## 安装依赖

Ubuntu / Debian：

```bash
sudo apt install libudev-dev libinput-dev libxdo-dev xdotool
# Wayland 需要额外安装
sudo apt install ydotool
```

Arch Linux：

```bash
sudo pacman -S libinput xdotool
# Wayland
yay -S ydotool
```

## 安装 gestures

直接下载预编译二进制：

```bash
wget https://github.com/ferstar/gestures/releases/latest/download/gestures
chmod +x gestures
sudo mv gestures /usr/local/bin/
```

或者从源码装：

```bash
cargo install --git https://github.com/ferstar/gestures.git
```

## 配置

配置文件用 KDL。比如三指拖拽加一个四指切换工作区：

```kdl
// 三指拖拽（X11 & Wayland 通用）
gesture "drag" swipe any {
    fingers 3
    acceleration 1.0      // 拖拽速度
    mouse_up_delay 500    // 抬手后延迟（ms）
}

// 四指上滑切换工作区
gesture "switch-workspace-up" swipe up {
    fingers 4
    exec "xdotool" "key" "super+Page_Up"
}
```

## 运行

推荐装成 user systemd service：

```bash
# 安装服务文件
gestures install-service

# 启动并设为开机自启
systemctl --user enable --now gestures
```

如果启动时报权限问题，通常是当前用户没有读取输入设备的权限，加入 `input` 组：

```bash
sudo usermod -aG input $USER
```

重新登录后再试。

## 链接

- GitHub: https://github.com/ferstar/gestures
- Releases: https://github.com/ferstar/gestures/releases
- Issues: https://github.com/ferstar/gestures/issues

这玩意儿属于典型的“用上之后就不想再回去”的小工具。Linux 桌面体验很多时候差的就是这些细碎地方，单独看都不大，天天用就很烦。能补一个算一个吧。

```js
NOTE: I am not responsible for any expired content.
Created at: 2023-01-29T02:08:34+08:00
Updated at: 2026-01-04T06:00:00+08:00
comment@https://github.com/ferstar/blog/issues/73
```
