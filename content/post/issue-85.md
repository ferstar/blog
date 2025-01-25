---
title: "修复联想笔记本Linux下合盖睡死与功能键异常关机问题"
date: "2025-01-13T07:15:03+08:00"
tags: ['Linux']
comments: true
---

## 问题背景

许多使用联想ThinkBook 2024系列笔记本的Linux用户报告了两个典型问题：

1. **合盖睡死问题**  
   当合上笔记本盖时，设备会直接断电关机而非进入挂起状态，导致工作状态丢失

2. **功能键异常关机**  
   使用`Fn+F5`/`Fn+F6`组合键时（非高频次使用），可能触发意外关机

该问题在Ubuntu 24.04（内核6.9+）和Arch Linux（内核6.10+）等多个发行版中复现，经排查与ACPI电源管理模块的兼容性有关。

---

## 解决方案

开源社区开发的`ideapad-laptop-tb-dkms`内核模块通过以下方式解决问题：

- 重写ACPI事件处理逻辑
- 修正电源状态转换机制
- 禁用异常的功能键信号

### 兼容设备
- ThinkBook 2024 16+ IMH
- ThinkBook 2024 14 G6+ AHP
- ThinkBook 16 G6+ AHP

---

## 安装指南

### 对于Arch系发行版
```bash
sudo pacman -S ideapad-laptop-tb-dkms
```

### 通用安装方式（支持Ubuntu/Debian/Fedora等）
```bash
# 编译并安装DKMS模块
git clone https://github.com/ferstar/ideapad-laptop-tb.git
cd ideapad-laptop-tb-dkms
sudo dkms add .
sudo dkms install ideapad-laptop-tb/6.10  # 版本号需匹配内核版本

# 禁用原生冲突模块
sudo cp dkms/blacklist-ideapad-laptop-tb-dkms.conf /etc/modprobe.d/

# 重启生效
sudo reboot
```

### 卸载方法
```bash
sudo dkms remove ideapad-laptop-tb/6.10 --all
sudo rm /etc/modprobe.d/blacklist-ideapad-laptop-tb-dkms.conf
sudo reboot
```

---

## 注意事项

1. **功能键变更**  
   `Fn+F4`（麦克风静音）将失效，建议通过系统托盘或`pactl`命令控制麦克风状态

2. **电源状态验证**  
   安装后可通过以下命令测试：
   ```bash
   systemctl suspend  # 测试挂起功能
   lidctrl close      # 测试合盖响应
   ```

---

1. https://bbs.archlinuxcn.org/viewtopic.php?id=14053
2. https://github.com/ferstar/ideapad-laptop-tb



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-13T07:15:03+08:00
Updated at: 2025-01-25T10:12:29+08:00
Origin issue: https://github.com/ferstar/blog/issues/85
```
