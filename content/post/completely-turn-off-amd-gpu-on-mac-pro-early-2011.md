---
title: "Completely Turn Off Amd Gpu on Mac Pro Early 2011"
date: 2018-12-09T16:57:37+08:00
tags: ['OTHERS']
comments: false
---

手上的MacPro中了显卡门, 频繁花屏重启, 各种折腾后总算堪用, 完全禁掉了坑爹的AMD独显, 副作用是本子关上盖子屏幕就无法点亮(休眠是OK的,就是屏幕不亮, 重启才正常), 除了不再花屏卡死重启以外, 还有个额外的好处就是`C`面右手掌托位置几乎不会发热, 所以完全可以把左边风扇转速调大, 右边保持默认, 兼顾静音+散热

https://gist.github.com/blackgate/17ac402e35d2f7e0f1c9708db3dc7a44

hw: mac pro i7 15' early 2011(with the fucking AMD GPU inside)

os: HighSierra 10.13.6 (17G4015)

here are my final EFI file tree structure(extra efi files are come from Ubuntu 18.04 official ISO):

```
.
├── [ 512]  EFI
│   ├── [ 512]  APPLE
│   │   ├── [ 512]  CACHES
│   │   │   └── [ 512]  CAFEBEEF
│   │   └── [ 512]  EXTENSIONS
│   │       └── [ 15M]  Firmware.scap
│   └── [ 512]  grub
│       ├── [1.1M]  BOOTx64.EFI
│       └── [1.1M]  grubx64.efi
└── [ 512]  boot
    └── [1.0K]  grub
        ├── [2.3M]  efi.img
        ├── [4.9K]  font.pf2
        ├── [ 278]  grub.cfg
        ├── [  55]  loopback.cfg
        └── [ 12K]  x86_64-efi
            ├── [ 15K]  acpi.mod
            ├── [1.9K]  adler32.mod
            ├── [ 22K] xxx.mod
```

and my grub.cfg:

```
set timeout=10
menuentry "macOS with outb - Power Off AMD GPU at boot - lose brightness control HighSierra" {
outb 0x728 1
outb 0x710 2
outb 0x740 2
outb 0x750 0
exit
}
menuentry "macOS without outb - AMD GPU stay Power On at boot - with brightness control HighSierra" {
exit
}
```

and follow [this post steps](https://forums.macrumors.com/threads/disable-a-failed-amd-gpu-on-a-2011-macbook-pro-grub-solution.2087527/) load the attached kext to prevent the GPU from waking up from sleep

I also installed smcFanControl to lower the CPU temperature and use Brightness Slider to control screen light

Unfortunately, when I close the lid and open again, the screen can't wake up unless reboot it.

But, compared to the frequent crash and boot loops, the wake up issue is just little case which can be ignored.

PS: I upload some useful software to Google disk

<https://drive.google.com/drive/folders/1bURkW1n8ARDR4TsjcE08WJ2gCpAevubw?usp=sharing>
