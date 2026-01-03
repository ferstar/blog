---
title: "如何在Linux X11开启R9000P2021款笔记本165Hz刷新率"
slug: "r9000p-165hz-linux-x11"
date: "2023-04-25T02:40:04+08:00"
tags: ['Linux']
comments: true
---

我这款本子是 3050Ti 的显卡，Linux 下偶尔炼个超迷你小丹凑合用一下，平常大部分时候都是闲置状态，所以多数情况用的是**混合模式**而非**独显直通**。

这样有个问题，不管是 Archlinux 还是 Ubuntu，进桌面显示器配置就只有 60Hz 的选项，但切到**独显直通**，165Hz 的高刷就又有了，一通搜索以后，得出结论：在混合模式下系统无法准确获取EDID文件。另外即使是**独显直通**状态，屏幕回报的刷新率是 165.02Hz，说明这块屏幕不是标准的 165Hz 行刷新率，操作系统并没有正确的屏幕分辨率信息。

我在这里 https://wiki.archlinux.org/title/xrandr#Troubleshooting 找到了这个问题的解决办法：

先在**独显直通**状态，通过`xrandr --verbose`记下 60、165Hz 的 Modeline，我的机器是这样的：

```shell
# 60Hz
282.7 2560 2608 2640 2720 1600 1603 1609 1732 -HSync -VSync
# 165Hz
777.410 2560 2608 2640 2720 1600 1603 1609 1732 -HSync -VSync
```

接下来就是把这两种配置用`xrandr`添加到内屏配置上，由于**混合模式**和**独显直通**两种模式下，内屏设备名并不固定，可以通过如下命令找到：

```shell
xrandr | grep -i ' connected' | cut -d ' ' -f 1
```

我的机器输出如下：

```shell
eDP-1
DP-1-0  # 这个其实是我的外接屏幕
```

确定好内屏设备名（eDP-1）以后，就可以来指定我们上面探测到的分辨率配置了：

```shell
# 65Hz
xrandr --newmode "2560x1600_60.00" 282.7 2560 2608 2640 2720 1600 1603 1609 1732 -HSync -VSync
xrandr --addmode eDP-1 2560x1600_60.00
# 165Hz
xrandr --newmode "2560x1600_165.00" 777.410 2560 2608 2640 2720 1600 1603 1609 1732 -HSync -VSync
xrandr --addmode eDP-1 2560x1600_165.00
```

此时打开显示器配置，熟悉的高刷分辨率就回来了，且可以自由切换。

![image](https://user-images.githubusercontent.com/2854276/234154957-dab73e59-5526-40bd-a1be-8e5ebdf0f103.png)

当然你也可以继续用`xrandr`在命令行切换当前显示器的刷新率：

```shell
xrandr --output eDP-1 --mode "2560x1600_165.00"
xrandr --output eDP-1 --mode "2560x1600_60.00"
```

以上临时注入的配置在重启以后就会消失，Archlinux Wiki 里贴心的写了持久化方案，也就是把配置写到 xorg 文件里。作为懒癌患者，因为偶尔还有不插电的使用场景，所以当然是要搞成自动挡啦：插电 165、电池 60。那么就有两个问题需要解决：

1. 插电、离电条件触发
2. 写个切换分辨率的脚本

KDE 的系统配置==》电源管理==》节能==》（交流供电、电池供电）运行脚本刚好可以解决脚本触发条件的问题，接下来就是上脚本了：

```shell
#!/usr/bin/env bash
intern=$(xrandr | grep " connected" | grep "eDP" | cut -d" " -f1)
resolution="2560x1600"
low_mode="${resolution}_60.00"
high_mode="${resolution}_165.00"

function add_mode {
    if [ "$(xrandr | grep -E -c "$1")" -eq 0 ]; then
        if [ "$1" == "$low_mode" ]; then
            xrandr --newmode $low_mode 282.7 2560 2608 2640 2720 1600 1603 1609 1732 -HSync -VSync
            xrandr --addmode "$intern" $low_mode
        elif [ "$1" == "$high_mode" ]; then
            xrandr --newmode $high_mode 777.410 2560 2608 2640 2720 1600 1603 1609 1732 -HSync -VSync
            xrandr --addmode "$intern" $high_mode
        fi
    fi
}

function change_fps {
    if [ "$1" == "low" ]; then
        add_mode "$low_mode"
        xrandr --output "$intern" --mode $low_mode
    elif [ "$1" == "high" ]; then
        add_mode "$high_mode"
        xrandr --output "$intern" --mode $high_mode
    fi
}

if [ "$#" -eq 0 ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [low|high]"
    exit 1
fi
change_fps "$1"
```



```
# NOTE: I am not responsible for any expired content.
create@2023-04-25T02:40:04+08:00
update@2023-05-08T05:52:52+08:00
comment@https://github.com/ferstar/blog/issues/76
```
