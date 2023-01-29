---
title: "X11触控板手势增强"
date: "2023-01-29T02:08:34+08:00"
tags: ['Linux']
comments: true
---

> 转用 Linux 后我一直都比较怀念 macOS 上丝滑的**三指拖拽**效果，鉴于近几年出的 Windows 本子触控板面积以及跟手性肉眼可见的改善了很多，我觉得是时候在 Linux 上折腾下**触控板手势**了。

说干就干，放狗搜了一下，发现类似的实现还不少，小罗列下：

1. https://github.com/riley-martin/gestures
2. https://github.com/bulletmark/libinput-gestures
3. https://github.com/Coffee2CodeNL/gebaar-libinput
4. https://github.com/osleg/gebaar-libinput-fork
5. https://github.com/iberianpig/fusuma
6. https://github.com/marsqing/libinput-three-finger-drag

基本上就是两种实现思路：

1. 解析`libinput debug-events`输出，判断手势进而借用类似`xdotool`之类的工具发送具体的键盘组合或者鼠标点击或位移指令
2. 直接调用`libinput` API，明显此方法性能最优

我最在意的手势莫过于**三指拖拽**，实现这个功能有两个注意的点：

1. 拖拽起止会有持续不断的位移指令发出，所以通过 fork shell 不间断发送位移指令的操作是非常低效的，见这个[讨论](https://github.com/riley-martin/gestures/discussions/6)。
2. 为了媲美 macOS 的丝滑拖拽效果，那就要求程序实现要尽可能的高效。

于是乎我选择了一个 Rust [实现](https://github.com/riley-martin/gestures)开抄，负责实现 API 级别的触控手势识别，然后缝合了另一个 Rust [实现](https://github.com/marsqing/libinput-three-finger-drag)，负责实现 API 级别的**拖拽**效果。

终极缝合以后的产物效果还不错，基本符合预期：

1. CPU 占用极低（极限情况：疯狂三指拖拽某窗口，本 fork 实现 CPU 占用不到1%；原实现5~10%；Python、Ruby等实现30%+）
2. 拖拽体验丝滑
3. 重放手指后支持继续拖动（延迟时间`mouse_up_delay`可配）
4. 拖拽速度`acceleration`可配置

编译好的二进制和示例配置文件见：https://github.com/ferstar/gestures/releases/tag/0.3.0 理论上支持所有 Linux X11 桌面环境。

Enjoy！



```
# NOTE: I am not responsible for any expired content.
create@2023-01-29T02:08:34+08:00
update@2023-01-29T02:11:08+08:00
comment@https://github.com/ferstar/blog/issues/73
```
