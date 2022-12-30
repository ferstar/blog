---
title: "修复Fcitx输入法文字候选框在PyCharm中无法跟随光标问题"
date: "2020-12-30T10:25:21+08:00"
tags: ['Linux', 'Python']
comments: true
---

- 症状：搜狗输入法文字候选框一直在窗口的左下角，根本看不见候选，只能盲打
- 系统：

> 大概JB也知道自家runtime坑了，所以不知从哪个版本开始支持更换自定义的runtime，所以事情就变得更简单了： 下载合适的runtime换一下就行OK

> 注意：如果你最近更新了PyCharm，然后发现频繁闪退，那就得先把runtime切换为IDE默认，然后再更新一下自定义runtime即可

https://github.com/ayanamist/JetBrainsRuntime-for-fcitx

---

```shell
fcitx version: 4.2.9.7
OS: Ubuntu 20.04.1 LTS x86_64 
Host: 82DM Lenovo XiaoXinPro-13ARE 2020 
Kernel: 5.6.0-1038-oem 
Uptime: 3 days, 15 hours, 10 mins 
Packages: 2526 (dpkg), 17 (snap) 
Shell: zsh 5.8 
Resolution: 1680x1050, 1920x1080 
DE: GNOME 
WM: Mutter 
WM Theme: Yaru-dark 
Theme: Yaru [GTK2/3] 
Icons: Yaru [GTK2/3] 
Terminal: x-terminal-emul 
CPU: AMD Ryzen 7 4800U with Radeon Graphics (16)  
GPU: AMD ATI 03:00.0 Renoir 
Memory: 5793MiB / 15432MiB                                                 
```

- PyCharm版本：`2020.3.1 Professional Edition from SnapStore`

- 解决办法：

    下载解压 [这个runtime](https://github.com/RikudouPatrickstar/JetBrainsRuntime-for-Linux-x64/releases)

    假设你解压的路径在`~/myprojects/jbr`

    `sudo mount -o bind ~/myprojects/jbr /snap/pycharm-professional/current/jbr`

- 效果图：

![image](https://user-images.githubusercontent.com/2854276/103345249-d78b9e00-4acb-11eb-9fd1-6f3bf0444f92.png)

- 默认runtime：

![default-runtime](https://user-images.githubusercontent.com/2854276/103345287-f722c680-4acb-11eb-920a-da50e6af00fb.png)

- 打patch后的runtime：

![new-runtime](https://user-images.githubusercontent.com/2854276/103345302-01dd5b80-4acc-11eb-90dc-b5b75aa3f3a3.png)

- 参考`对我基本无用，snap商店里的pycharm没有idea.sh这个启动脚本`

1. https://bbs.archlinuxcn.org/viewtopic.php?pid=43982#p43982
2. https://blog.csdn.net/u011166277/article/details/106287587



```
# NOTE: I am not responsible for any expired content.
create@2020-12-30T10:25:21+08:00
update@2022-12-30T06:33:09+08:00
comment@https://github.com/ferstar/blog/issues/33
```
