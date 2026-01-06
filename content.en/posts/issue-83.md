---
title: "How to update InsydeH2O BIOS with pure Linux"
slug: "update-insydeh2o-bios-linux"
date: "2025-01-12T16:58:10+08:00"
tags: ['Linux', 'Idea']
comments: true
---

> I am not a native English speaker; this article was translated by Gemini.

As a long-time Linux enthusiast, I usually install a Linux distro as soon as I get a new laptop. That makes the preinstalled Windows almost useless, but I still couldn't delete it — I needed it to run vendor BIOS updaters. Keeping a ~100GB Windows partition just for the occasional BIOS update is pretty annoying. Sure, something like Windows To Go exists, but that doesn't really change the situation: you're still relying on Windows.

Right before the end of 2024, I came across someone mentioning a pure-Linux BIOS update workflow on Twitter:
https://x.com/felixonmars/status/1876646199207604351

It was only a few lines, but it lit the tinkering fire in my head: this might work — let's do it.

All my laptops are Lenovo ThinkBooks. I started with one machine at home (A). Specs:

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

1. Download Framework's UEFI Shell flashing tool. We only need `H2OFFT-Sx64.efi`. Save it to `/boot/efi`: https://downloads.frame.work/bios/Framework_Laptop_13_13th_Gen_Intel_Core_BIOS__3.05_EFI.zip
2. Download UEFI Shell. Save `shellx64.efi` to `/boot/efi`: https://github.com/pbatard/UEFI-Shell/releases/tag/24H2
3. Download the BIOS updater for your exact laptop model from Lenovo's driver page. It's usually named something like `j6cn50ww.exe`.
4. Try extracting the `exe` with `7z`: `7z e j6cn50ww.exe`. You may see output like: `Comments: This installation was built with Inno Setup.`
5. Use `innoextract` to unpack it: `innoextract -e j6cn50ww.exe`. You'll get a new `exe` — mine was `J6CN50WW.exe`.
6. Extract again with `7z`: `7z e J6CN50WW.exe`. This time you should get the actual BIOS firmware, `WinJ6CN50WW.fd`.
7. Save `WinJ6CN50WW.fd` to `/boot/efi`.
8. Add a UEFI Shell boot entry. Edit `/etc/grub.d/40_custom`, paste the following, then run `sudo update-grub`:
    ```shell
    menuentry "UEFI Shell" {
        insmod part_gpt
        insmod chain
        set root='(hd0,gpt1)'
        chainloader /shellx64.efi
    }
    ```
9. Reboot into UEFI Shell. Type `FS0:` and press Enter to switch to the EFI partition, then run `H2OFFT-Sx64.efi WinJ6CN50WW.fd` and press Enter.
10. You should see the familiar BIOS flashing UI. Wait for it to complete.

Finally, I can throw the bundled Windows partition into the trash ✌️

---

Note: For some newer Lenovo models, `7z` may be able to extract the BIOS firmware directly — usually named `xxx.bin` — so `innoextract` is not required. Also, `7z` isn't mandatory either. You can use any tool that can unpack an `exe` (for example `bsdtar`).

---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-12T16:58:10+08:00
Updated at: 2025-01-12T17:04:21+08:00
Origin issue: https://github.com/ferstar/blog/issues/83
```
