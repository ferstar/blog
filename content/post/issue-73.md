---
title: "Linux触控板手势增强之「三指拖拽」"
date: "2023-01-29T02:08:34+08:00"
tags: ['Linux']
comments: true
---

转用 Linux 后一直都比较怀念 macOS 上丝滑的**三指拖拽**效果，鉴于近几年出的 Windows 本子触控板面积以及跟手性肉眼可见的改善了很多，我觉得是时候在 Linux 上折腾下**触控板手势**了。

After switching to Linux, I've been missing the smooth **three-finger drag** experience from macOS. Given that recent Windows laptops have significantly improved touchpad size and responsiveness, I decided it was time to tackle **touchpad gestures** on Linux.

---

## 调研与选型

说干就干，放狗搜了一下，发现类似的实现还不少：

## Research and Selection

Let's dive in. After some searching, I found quite a few similar implementations:

1. https://github.com/riley-martin/gestures
2. https://github.com/bulletmark/libinput-gestures
3. https://github.com/Coffee2CodeNL/gebaar-libinput
4. https://github.com/osleg/gebaar-libinput-fork
5. https://github.com/iberianpig/fusuma
6. https://github.com/marsqing/libinput-three-finger-drag

基本上就是两种实现思路：

1. 解析 `libinput debug-events` 输出，判断手势进而借用类似 `xdotool` 之类的工具发送具体的键盘组合或者鼠标点击或位移指令
2. 直接调用 `libinput` API，明显此方法性能最优

There are basically two implementation approaches:

1. Parse `libinput debug-events` output, detect gestures, then use tools like `xdotool` to send keyboard combinations or mouse click/move commands
2. Directly call `libinput` API - this method obviously has the best performance

---

## 核心需求

我最在意的手势莫过于**三指拖拽**，实现这个功能有两个注意的点：

1. 拖拽起止会有持续不断的位移指令发出，所以通过 fork shell 不间断发送位移指令的操作是非常低效的，见这个[讨论](https://github.com/riley-martin/gestures/discussions/6)
2. 为了媲美 macOS 的丝滑拖拽效果，必须使用尽可能高效的实现

## Core Requirements

The gesture I care about most is **three-finger drag**. There are two key considerations for implementing this:

1. Dragging involves continuous position update commands, so forking shells to send movement commands non-stop is very inefficient (see this [discussion](https://github.com/riley-martin/gestures/discussions/6))
2. To match macOS's smooth dragging experience, we must use the most efficient implementation possible

---

## 实现方案

于是乎我选择了一个 Rust [实现](https://github.com/riley-martin/gestures)开抄，负责实现 API 级别的触控手势识别，然后缝合了另一个 Rust [实现](https://github.com/marsqing/libinput-three-finger-drag)，负责实现 API 级别的**拖拽**效果。

## Implementation Approach

I chose a Rust [implementation](https://github.com/riley-martin/gestures) as the base for API-level touch gesture recognition, then integrated another Rust [implementation](https://github.com/marsqing/libinput-three-finger-drag) to handle API-level **dragging** effects.

目前项目已发展到 **v0.8.1** 版本，主要改进包括：

- **双平台支持**：同时支持 X11 和 Wayland（自动检测）
- **性能优化**：
  - X11 直接使用 libxdo API，延迟最小
  - Wayland 优化 ydotool 集成，60 FPS 节流
  - 4 线程池防止 PID 耗尽
  - 正则缓存（once_cell::Lazy）
  - 事件缓存（1秒）减少配置查找

The project has evolved to **v0.8.1** with major improvements:

- **Dual-platform support**: Both X11 and Wayland (auto-detection)
- **Performance optimizations**:
  - X11 uses libxdo API directly for minimal latency
  - Wayland optimized ydotool integration with 60 FPS throttling
  - 4-worker thread pool preventing PID exhaustion
  - Regex caching via once_cell::Lazy
  - 1-second event caching for config lookups

---

## 性能表现

终极缝合以后的产物效果还不错，基本符合预期：

## Performance Metrics

The final stitched-together product works quite well and basically meets expectations:

1. **CPU 占用极低**
   - 极限情况：疯狂三指拖拽某窗口，本 fork 实现 CPU 占用不到 1%
   - 原实现 5~10%
   - Python、Ruby 等实现 20%+

2. **资源占用**
   - 内存占用不到 5MB
   - 程序体积不到 2MB
   - 无多余依赖

3. **拖拽体验丝滑**（如果觉得不够滑，那一定是你本子的触控板太渣）

4. **重放手指后支持继续拖动**（延迟时间 `mouse_up_delay` 可配）

5. **拖拽速度 `acceleration` 可配置**

1. **Extremely low CPU usage**
   - Extreme case: frantically three-finger dragging a window, this fork uses <1% CPU
   - Original implementation: 5-10%
   - Python/Ruby implementations: 20%+

2. **Resource footprint**
   - Memory usage <5MB
   - Binary size <2MB
   - No extra dependencies

3. **Smooth dragging experience** (if it's not smooth enough, your touchpad is probably to blame)

4. **Supports continued dragging after lifting fingers** (delay time `mouse_up_delay` is configurable)

5. **Configurable drag speed via `acceleration`**

---

## 安装使用

### 依赖安装

**Ubuntu/Debian:**
```bash
sudo apt install libudev-dev libinput-dev libxdo-dev xdotool
# Wayland 需要额外安装
sudo apt install ydotool
```

**Arch Linux:**
```bash
sudo pacman -S libinput xdotool
# Wayland
yay -S ydotool
```

## Installation & Usage

### Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt install libudev-dev libinput-dev libxdo-dev xdotool
# Wayland requires additional packages
sudo apt install ydotool
```

**Arch Linux:**
```bash
sudo pacman -S libinput xdotool
# Wayland
yay -S ydotool
```

### 安装程序

**方法 1：直接下载预编译二进制**
```bash
# 从 Releases 下载最新版本
wget https://github.com/ferstar/gestures/releases/latest/download/gestures
chmod +x gestures
sudo mv gestures /usr/local/bin/
```

**方法 2：Cargo 安装**
```bash
cargo install --git https://github.com/ferstar/gestures.git
```

**方法 3：手动编译**
```bash
git clone https://github.com/ferstar/gestures.git
cd gestures
cargo build --release
sudo cp target/release/gestures /usr/local/bin/
```

### Install Binary

**Method 1: Download pre-compiled binary**
```bash
# Download latest from Releases
wget https://github.com/ferstar/gestures/releases/latest/download/gestures
chmod +x gestures
sudo mv gestures /usr/local/bin/
```

**Method 2: Install via Cargo**
```bash
cargo install --git https://github.com/ferstar/gestures.git
```

**Method 3: Manual compilation**
```bash
git clone https://github.com/ferstar/gestures.git
cd gestures
cargo build --release
sudo cp target/release/gestures /usr/local/bin/
```

---

## 配置说明

### 生成配置文件

```bash
# 生成默认配置（自动放到 ~/.config/gestures/config.kdl）
gestures generate-config
```

## Configuration

### Generate Config File

```bash
# Generate default config (auto-placed in ~/.config/gestures/config.kdl)
gestures generate-config
```

### 配置示例

配置文件使用 KDL 格式，示例：

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

// 四指下滑切换工作区
gesture "switch-workspace-down" swipe down {
    fingers 4
    exec "xdotool" "key" "super+Page_Down"
}

// 四指左右滑动切换虚拟桌面
gesture "desktop-left" swipe left {
    fingers 4
    exec "xdotool" "key" "ctrl+alt+Left"
}

gesture "desktop-right" swipe right {
    fingers 4
    exec "xdotool" "key" "ctrl+alt+Right"
}

// 捏合缩放（Pinch）
gesture "zoom-in" pinch in {
    fingers 2
    exec "xdotool" "key" "ctrl+plus"
}

gesture "zoom-out" pinch out {
    fingers 2
    exec "xdotool" "key" "ctrl+minus"
}
```

### Configuration Examples

Config file uses KDL format, example:

```kdl
// Three-finger drag (X11 & Wayland)
gesture "drag" swipe any {
    fingers 3
    acceleration 1.0      // Drag speed
    mouse_up_delay 500    // Delay after lifting (ms)
}

// Four-finger swipe up to switch workspace
gesture "switch-workspace-up" swipe up {
    fingers 4
    exec "xdotool" "key" "super+Page_Up"
}

// Four-finger swipe down to switch workspace
gesture "switch-workspace-down" swipe down {
    fingers 4
    exec "xdotool" "key" "super+Page_Down"
}

// Four-finger horizontal swipe for virtual desktops
gesture "desktop-left" swipe left {
    fingers 4
    exec "xdotool" "key" "ctrl+alt+Left"
}

gesture "desktop-right" swipe right {
    fingers 4
    exec "xdotool" "key" "ctrl+alt+Right"
}

// Pinch to zoom
gesture "zoom-in" pinch in {
    fingers 2
    exec "xdotool" "key" "ctrl+plus"
}

gesture "zoom-out" pinch out {
    fingers 2
    exec "xdotool" "key" "ctrl+minus"
}
```

### Wayland 配置注意

Wayland 下需要使用 `ydotool` 替代 `xdotool`：

```kdl
// Wayland 示例
gesture "switch-workspace" swipe up {
    fingers 4
    exec "ydotool" "key" "125:1 33:1 33:0 125:0"  // Super+Page_Up
}
```

### Wayland Configuration Notes

On Wayland, use `ydotool` instead of `xdotool`:

```kdl
// Wayland example
gesture "switch-workspace" swipe up {
    fingers 4
    exec "ydotool" "key" "125:1 33:1 33:0 125:0"  // Super+Page_Up
}
```

**Wayland 下必须启动 ydotoold 守护进程：**
```bash
sudo systemctl enable --now ydotool
# 或者手动启动
sudo ydotoold
```

**On Wayland, the ydotoold daemon must be running:**
```bash
sudo systemctl enable --now ydotool
# Or start manually
sudo ydotoold
```

---

## 运行程序

### Systemd 服务（推荐）

```bash
# 安装服务文件
gestures install-service

# 启动并设为开机自启
systemctl --user enable --now gestures

# 重新加载配置（无需重启）
systemctl --user reload gestures

# 查看日志
journalctl --user -u gestures -f
```

## Running the Program

### Systemd Service (Recommended)

```bash
# Install service file
gestures install-service

# Enable and start service
systemctl --user enable --now gestures

# Reload config (no restart needed)
systemctl --user reload gestures

# View logs
journalctl --user -u gestures -f
```

### 手动运行

```bash
# 自动检测显示服务器（X11/Wayland）
gestures start

# 指定显示服务器
gestures start --display-server x11
gestures start --display-server wayland
```

### Manual Execution

```bash
# Auto-detect display server (X11/Wayland)
gestures start

# Specify display server
gestures start --display-server x11
gestures start --display-server wayland
```

---

## 常见问题

### 权限问题

需要将用户加入 `input` 组：
```bash
sudo usermod -aG input $USER
# 需要重新登录生效
```

## Common Issues

### Permission Issues

Add user to `input` group:
```bash
sudo usermod -aG input $USER
# Requires re-login to take effect
```

### 三指拖拽不生效

**X11:**
```bash
# 检查 xdotool 是否安装
which xdotool

# 测试手动拖拽
xdotool mousedown 1
xdotool mousemove_relative -- 100 100
xdotool mouseup 1
```

**Wayland:**
```bash
# 检查 ydotoold 是否运行
ps aux | grep ydotoold

# 启动 ydotoold
sudo systemctl start ydotool
```

### Three-Finger Drag Not Working

**X11:**
```bash
# Check if xdotool is installed
which xdotool

# Test manual dragging
xdotool mousedown 1
xdotool mousemove_relative -- 100 100
xdotool mouseup 1
```

**Wayland:**
```bash
# Check if ydotoold is running
ps aux | grep ydotoold

# Start ydotoold
sudo systemctl start ydotool
```

### 桌面环境冲突

某些桌面环境（如 GNOME、KDE）自带手势功能，需要禁用：

**GNOME:**
```bash
gsettings set org.gnome.desktop.peripherals.touchpad disable-while-typing false
```

**KDE:**
系统设置 → 输入设备 → 触摸板 → 禁用手势

### Desktop Environment Conflicts

Some DEs (GNOME, KDE) have built-in gestures that need to be disabled:

**GNOME:**
```bash
gsettings set org.gnome.desktop.peripherals.touchpad disable-while-typing false
```

**KDE:**
System Settings → Input Devices → Touchpad → Disable gestures

### Wayland 下 CPU 占用高

已在 v0.8.1 优化，默认 60 FPS 节流，CPU 占用应在 5% 以内

如果仍然偏高，可降低刷新率：
```kdl
// 在配置文件中调整（仅影响 Wayland）
// 降低到 30 FPS
fps_limit 30
```

### High CPU Usage on Wayland

Optimized in v0.8.1 with default 60 FPS throttling, CPU usage should be <5%

If still high, reduce frame rate:
```kdl
// Adjust in config (Wayland only)
// Reduce to 30 FPS
fps_limit 30
```

---

## 项目链接

- **GitHub**: https://github.com/ferstar/gestures
- **最新发布**: https://github.com/ferstar/gestures/releases
- **问题反馈**: https://github.com/ferstar/gestures/issues

## Project Links

- **GitHub**: https://github.com/ferstar/gestures
- **Latest Release**: https://github.com/ferstar/gestures/releases
- **Issue Tracker**: https://github.com/ferstar/gestures/issues

---

理论上支持所有使用 libinput 触摸板驱动的 Linux 桌面环境（GNOME、KDE、i3、Sway 等）。

除 X11 和 Wayland 的「三指拖拽」以外，其他功能与原作基本一致，但性能和稳定性有大幅提升。

In theory, it supports all Linux desktop environments using libinput touchpad drivers (GNOME, KDE, i3, Sway, etc.).

Beyond the "three-finger drag" functionality for X11 and Wayland, other features remain largely consistent with the original implementation, but with significantly improved performance and stability.

**Enjoy!**



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2023-01-29T02:08:34+08:00
Updated at: 2025-11-02T07:07:00+08:00
Origin issue: https://github.com/ferstar/blog/issues/73
```
