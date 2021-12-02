---
title: "拥抱 WSLg"
date: "2021-11-02T22:47:57+08:00"
tags: ['Windows', 'WSL2']
comments: true
---

> 开个坑, 慢慢填

0. 垃圾WSL IO巨慢

这里喷IO慢的仔细一看基本都是妈的项目在Windows里, 然后 runtime 在 WSL, 这他喵跨着9p不卡才怪

解决方法也很简单, runtime IDE什么的一股脑统统丢 WSL 里不就完了, 啥? 嫌空间不够用? WSL挂载磁盘了解下? 直接就是原生磁盘IO的性能

1. PyCharm 全局搜索框调不出来或者一闪而逝

这个[issue](https://github.com/microsoft/wslg/issues/96#issuecomment-858257113)里找到了神仙解法: 狂按快捷键, 直到全局搜索框出来为止, 然后 pin 住, 就欧了...

2. 中文输入法

方法是从[CSDN淘的](https://blog.csdn.net/defrag257/article/details/117326000) , 装好`fcitx`后, 这段丢到bashrc 或 zshrc 或 profile 里, 然后启动GUI前运行`fcitx-autostart`即可, 只需要运行一次

```shell
export LANG=zh_CN.UTF-8
export INPUT_METHOD=fcitx # wayland输入法
export XMODIFIERS=@im=fcitx # x11输入法
export GTK_IM_MODULE=fcitx # gtk输入法
export QT_IM_MODULE=fcitx # qt输入法
```

3. OpenGL 也就是显卡加速

老老实实按[官方说明](https://github.com/microsoft/wslg#pre-requisites)去装一下支持wslg的显卡驱动即可, 直观的感受是拖拽WSL的GUI应用窗口不会撕裂, 也明显不卡顿了, 纵享丝滑

后续的Windows更新可能会把装好的vGPU驱动替换成正常驱动, 从而导致WSLg GUI 应用丢掉 OpenGL 加速支持, 会显得比较卡, 暂时的解决办法是从组策略禁用Windows更新驱动程序

`Win + R -> gpedit.msc -> 计算机配置 -> 管理模板 -> Windows组件 -> Windows更新 -> 管理从Windows更新提供的更新 -> Windows更新不包括驱动程序 -> 启用 -> 应用`

4. IP老变的问题

这个也就是一个小脚本解决的事情, 以我常用的 proxychains(wsl中使用host代理) 为例

```shell
new_host=$(grep 'nameserver' /etc/resolv.conf | head -n 1 | awk '{print $2}')
old_host=$(grep -E '^socks5' /etc/proxychains4.conf | awk '{print $2}')
sudo sed -i "s/$old_host/$new_host/g" /etc/proxychains4.conf
```

5. Windows Terminal 进 Ubuntu 子系统默认目录不是`~`

设置 -> Ubuntu -> 常规 -> 命令行 -> `wsl.exe -d Ubuntu-20.04 --cd ~`

![image](https://user-images.githubusercontent.com/2854276/142790024-9b05f0e5-1784-4ae6-a575-d9536f793242.png)

6. Nahimic 无法发布?

直接卸载就完事, 如果卸载不掉, 可以试试我从[知乎](https://zhuanlan.zhihu.com/p/347961733)淘来的一个脚本 
[RemoveNahimic_20210111.zip](https://github.com/ferstar/blog/files/7599644/RemoveNahimic_20210111.zip)

7. JB全家桶里面中文输入法没法光标跟随?

参考我之前[这里](/post/issue-33/)的说明, WSLg环境依然有效, 主要就是用魔改的`jbr`替换JB官方的`jbr`目录

![image](https://user-images.githubusercontent.com/2854276/144391926-256746e8-f2cb-49d9-9476-0168fbe88b85.png)

```
# NOTE: I am not responsible for any expired content.
create@2021-11-02T22:47:57+08:00
update@2021-12-02T09:10:54+08:00
comment@https://github.com/ferstar/blog/issues/47
```
