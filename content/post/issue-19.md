---
title: "ThinkPad x220首装Manjaro Xfce4配置"
date: "2020-04-22T06:45:22+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-04-22T06:45:22+08:00

> update_date: 2020-07-12T04:32:48+08:00

> comment_url: https://github.com/ferstar/blog/issues/19

> 给老古董x220装了个Manjaro，顺路记录一下安装完成之后大概的配置过程

##### 1. 机器配置

![image](https://user-images.githubusercontent.com/2854276/79948260-19c50000-84a6-11ea-9869-291df81aa785.png)

##### 2. 换源

```shell
# 选择一个快的, 我选了中科大和清华的
sudo pacman-mirrors -i -c China -m rank
```

##### 3. 添加ArchLinuxCN 中文源

```shell
sudo vi /etc/pacman.conf
# 在文件的末尾添加
[archlinuxcn]
SigLevel = Optional TrustedOnly
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn//$arch
# 更新源和密钥环
sudo pacman -Syy
sudo pacman -S archlinux-keyring archlinuxcn-keyring
```

##### 4. 装yay并修改 AUR 源

```shell
sudo pacman -S yay
yay --aururl "https://aur.tuna.tsinghua.edu.cn" --save
```

##### 5. 装输入法

```shell
# 如果之前安装了 fcitx-im 或者相关的包，直接删除。
sudo pacman -Rsn fcitx-im fcitx-configtool
# 然后从 ArchLinuxCN 中文源里安装 fcitx-lilydjwg-git 和搜狗输入法的包， fcitx-lilydjwg-git 这个包里默认是包含 fcitx-qt4 的。
sudo pacman -S fcitx-lilydjwg-git fcitx-sogoupinyin fcitx-qt5 fcitx-configtool
# 这里需要安装 fcitx-qt5 的原因是 fcitx-configtool 这个包依赖于 QT5。
# 安装完成后手动添加用户变量，编辑 ~/.pam_environment 这个文件，如果没有就手动创建
vi ~/.pam_environment
GTK_IM_MODULE=fcitx
QT_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx
```
##### 6. 看见啥好用yay之

- 比如`火焰截图-flameshot`，超级好用的截图工具，当然深度截图工具也不错

- 又比如Google Chrome，vscode，qv2ray，WPS for Linux之类

##### 7. 调快捷键

xfce4有两处可以调快捷键的地方，如图，比较割裂，我只是小改一下以适应Windows的风格。

![image](https://user-images.githubusercontent.com/2854276/79948925-4b8a9680-84a7-11ea-8b67-07a9db2a553a.png)
![image](https://user-images.githubusercontent.com/2854276/79948974-5e9d6680-84a7-11ea-950c-b039e429998c.png)

