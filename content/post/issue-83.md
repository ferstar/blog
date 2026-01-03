---
title: "How to update InsydeH2O BIOS with pure Linux"
slug: "update-insydeh2o-bios-linux"
date: "2025-01-12T16:58:10+08:00"
tags: ['Linux', 'Idea']
comments: true
---

作为一个骨灰级 Linux 发烧友，我的电脑到手基本都是第一时间换装 Linux 发行版。这样设备厂商出厂自带的 Windows 系统几乎毫无作用，但我又不能把它干掉——我还得靠它来更新厂商发布的 BIOS。为了偶尔更 BIOS 的需求而不得不保留这近 100GB 磁盘占用的 Windows 着实有些蛋疼，当然我知道可以用类似 WIN2GO 的玩意来更 BIOS，但这又有什么区别呢，还是离不开 Windows。

终于赶在 2024 年的尾巴，我在 Twitter 上闲逛时发现有人提到了纯 Linux 环境更新 BIOS 的方案：https://x.com/felixonmars/status/1876646199207604351

虽然寥寥数语，但激起了心中折腾的一团火：有戏&干之！

我手头笔记本清一色都是联想的 ThinkBook，先拿家里的机器 A 开刀，配置如下：

```shell
OS: Ubuntu oracular 24.10 x86_64
Host: 21D0 (ThinkBook 14 G4+ ARA)
Kernel: Linux 6.12.9-bigv
Uptime: 1 day, 53 mins
Packages: 2800 (dpkg), 7 (flatpak)
Shell: zsh 5.9
Display (AUOC391): 2880x1800 @ 90 Hz in 14"
DE: GNOME
WM: Mutter (X11)
WM Theme: Yaru
Theme: Yaru [GTK2/3/4]
Icons: Yaru [GTK2/3/4]
Font: Cantarell (11pt) [GTK2/3/4]
Cursor: DMZ-White (48px)
Terminal: tmux 3.4
CPU: AMD Ryzen 7 6800H (16) @ 4.79 GHz
GPU: AMD Radeon 680M [Integrated]
Memory: 12.95 GiB / 29.55 GiB (44%)
Swap: 5.25 MiB / 32.00 GiB (0%)
Disk (/): 312.72 GiB / 414.32 GiB (75%) - btrfs
Local IP (wlan0): 192.168.31.157/24
Battery (AP16L5J): 77% [AC Connected]
Locale: en_US.UTF-8
```

1. 下载 Framework 家的 UEFI shell 更新工具，我们只用到`H2OFFT-Sx64.efi`，把他保存至`/boot/efi`：https://downloads.frame.work/bios/Framework_Laptop_13_13th_Gen_Intel_Core_BIOS__3.05_EFI.zip
2. 下载 UEFI-Shell，将`shellx64.efi`保存至`/boot/efi`：https://github.com/pbatard/UEFI-Shell/releases/tag/24H2
3. 去联想驱动官网下载你笔记本型号对应的 BIOS 更新程序，通常会是`j6cn50ww.exe`的名字
4. 尝试用`7z`解压这个`exe`文件：`7z e j6cn50ww.exe`，可能有类似的输出：`Comments: This installation was built with Inno Setup.`
5. 我们需要`innoextract`来解包：`innoextract -e j6cn50ww.exe`，你会得到一个新的`exe`，我这里的名字是`J6CN50WW.exe`
6. 再用`7z`解压：`7z e J6CN50WW.exe`，这次我们应该可以顺利得到真实的 BIOS 固件`WinJ6CN50WW.fd`
7. 将`WinJ6CN50WW.fd`保存至`/boot/efi`
8. 添加 UEFI-Shell 启动项，编辑`/etc/grub.d/40_custom`，填入如下内容后执行`sudo update-grub`：
    ```shell
    menuentry "UEFI Shell" {
        insmod part_gpt
        insmod chain
        set root='(hd0,gpt1)'
        chainloader /shellx64.efi
    }
    ```
9. 重启进入 UEFI-Shell，输入：`FS0:` 回车进入 EFI 分区，再输入：`H2OFFT-Sx64.efi WinJ6CN50WW.fd`回车
10. 此时熟悉的 BIOS 更新界面出现，耐心等待进度条走完即可完成更新

终于可以把自带的 Windows 分区扔进垃圾堆了✌️

---

注意：对于某些比较新的联想机型，可能`7z`就能直接解压得到 BIOS 固件了，一般是 `xxx.bin` 的命名，`innoextract` 并不是必须的；还有`7z`也不不是必须的，你可以换任何能解包`exe`的工具，比如`bsdtar`之类。

---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-12T16:58:10+08:00
Updated at: 2025-01-12T17:04:21+08:00
Origin issue: https://github.com/ferstar/blog/issues/83
```
