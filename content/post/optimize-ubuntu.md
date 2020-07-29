---
title: "Ubuntu 16.04 系统调优"
date: "2015-09-10T11:37:25+08:00"
tags: ['LINUX', 'SHELL', 'UBUNTU']
comments: true
---

## 删除旧内核

一个偷懒的脚本解决战斗

```shell
#!/bin/sh
#
#    purge-old-kernels - remove old kernel packages
#    Copyright (C) 2012 Dustin Kirkland <kirkland@ubuntu.com>
#
#    Authors: Dustin Kirkland <kirkland@ubuntu.com>
#             Kees Cook <kees@ubuntu.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
# Ensure we're running as root
if [ "$(id -u)" != 0 ]; then
    echo "ERROR: This script must run as root.  Hint..." 1>&2
    echo "  sudo $0 $@" 1>&2
    exit 1
fi
 
# NOTE: This script will ALWAYS keep the currently running kernel
# NOTE: Default is to keep 2 more, user overrides with --keep N
KEEP=2
# NOTE: Any unrecognized option will be passed straight through to apt
APT_OPTS=
while [ ! -z "$1" ]; do
    case "$1" in
        --keep)
            # User specified the number of kernels to keep
            KEEP="$2"
            shift 2
        ;;
        *)
            APT_OPTS="$APT_OPTS $1"
            shift 1
        ;;
    esac
done
 
# Build our list of kernel packages to purge
CANDIDATES=$(ls -tr /boot/vmlinuz-* | head -n -${KEEP} | grep -v "$(uname -r)$" | cut -d- -f2- | awk '{print "linux-image-" $0 " linux-headers-" $0}' )
for c in $CANDIDATES; do
    dpkg-query -s "$c" >/dev/null 2>&1 && PURGE="$PURGE $c"
done
 
if [ -z "$PURGE" ]; then
    echo "No kernels are eligible for removal"
    exit 0
fi
 
apt $APT_OPTS remove --purge $PURGE

```

## 替换 Firefox 为国内版

火狐自 Quantum 之后的版本在 Linux 上的体验都很棒，火狐通行证的同步也很方便，不过 Ubuntu 自带的火狐是国际版本，个人感觉不如国内版的同步速度快，所以就研究了下替换国内版的操作。 

### 1. 下载国内版火狐

 via: [Firefox-latest-x86_64.tar.bz2](https://download-ssl.firefox.com.cn/releases/firefox/59.0/zh-CN/Firefox-latest-x86_64.tar.bz2) 

### 2. 重命名系统自带

 `sudo mv /usr/lib/firefox /usr/lib/firefox.bak` 

### 3. 解压下载的文件放到/usr/lib/firefox

 `sudo cp firefox /usr/lib/` 

### 4. 复制原 Firefox 启动脚本

 `sudo cp /usr/lib/firefox.bak/firefox.sh /usr/lib/firefox` 

### 5. 复制原 dictionaries 软链接[可不做]

 `sudo cp /usr/lib/firefox.bak/dictionaries /usr/lib/firefox` 

### 6. 删除原默认配置文件

 `rm -rf ~/.mozilla` 

## 安装一些版权受限的软件

```
sudo apt-get install ubuntu-restricted-extras
```

## 换个趁手的oh-my-zsh
[http://ohmyz.sh/][1]
`sh -c "$(curl -fsSL https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"`

## ~~右键添加`打开终端`的选项~~
~~`sudo apt-get install nautilus-open-terminal`~~
> 似乎15.04开始这个package自带了～

## 某些应用`indicator`图标无法正常显示问题
`sudo apt-get install python-appindicator`

## 更改Chromium浏览器缓存到/tmp
`sudo vi /etc/chromium-browser/default`
改路径到/tmp
```
# Default settings for chromium-browser. This file is sourced by /bin/sh from
# /usr/bin/chromium-browser

# Options to pass to chromium-browser
CHROMIUM_FLAGS="--disk-cache-dir=/tmp/Chromium/"
```
收工～啥？还在用火狐？启动那么慢能忍受么。。。

## 利用tmpfs文件系统（要求`RAM>4G`）
`sudo vi /etc/fstab`
新起一行，写入以下内容
```
# temporary directories 
tmpfs /tmp tmpfs defaults,noatime,mode=1777  0 0 
tmpfs /var/tmp tmpfs defaults,noatime,mode=1777 0 0 
tmpfs /var/spool tmpfs defaults,noatime,mode=1777 0 0 
# log directories  
tmpfs /var/log tmpfs defaults,noatime,mode=0755 0 0 
```
## 调`swappiness`值
关于swap的介绍，挺详细
[https://help.ubuntu.com/community/SwapFaq](https://help.ubuntu.com/community/SwapFaq)
我机器内存够大，所以基本上是不分swap分区的
`sudo gedit /etc/sysctl.conf`
Search for vm.swappiness and change its value as desired. If vm.swappiness does not exist, add it to the end of the file like so:
`vm.swappiness=10`
内存如果够大，这里完全可以设为0，或者干脆干掉swap分区，机智如我～

## 关于磁盘分区格式的选择
- 我只分三个`/efi fat16 # 100MB左右足够`、`/ ext4 # 20GB左右`和`/home ext4 #剩余空间全给`，如果是SSD，格式换为[`btrfs`](https://wiki.archlinux.org/index.php/Btrfs) 
- 要不要swap分区？我的选择是不要，因为物理内存足够大，就算不够用，可以随时用swapfile启用，用完再删即可

## 截图工具的选择
我比较喜欢用深度截图工具，简单好用
[deepin-scrot_2.0-0deepin_all.deb](http://packages.linuxdeepin.com/deepin/pool/main/d/deepin-scrot/deepin-scrot_2.0-0deepin_all.deb) 
```
sudo dpkg -i deepin-scrot_2.0-0deepin_all.deb
sudo apt-get -f install
```
然后设定快捷键呼出`ctrl+alt+A`
`system-settings --> keyboard --> custom shortcuts`添加`command` `deepin-scrot %u`绑定`ctrl+alt+A`

## 禁用系统bug报告弹窗
bug报告本来是好事，但无奈弹的太多了些，多数情况除了影响心情外，并没有什么卵用，所以需要禁用之：
`sudo vi /etc/default/apport`

```
# set this to 0 to disable apport, or to 1 to enable it
# you can temporarily override this with
# sudo service apport start force_start=1
enabled=0
```
## 更改普通用户密码为简单密码
系统默认策略不允许普通用户设定简单密码，所以如果想要设定简单密码的话，可以先切到root然后再换
```
sudo -i
passwd uersname
```
## 安装`deb`二进制包
可以简单的双击安装， 或者命令行
```
sudo dpkg -i xxx.deb
sudo apt-get -f install
```

## 百度网盘`bcloud`
[https://github.com/LiuLang/bcloud][2]

## 为知笔记
[http://blog.wiz.cn/downloads-mac-linux.html][3]

## wineQQ
[http://www.ubuntukylin.com/application/show.php?lang=cn&id=279][4]

## WPS
[http://www.ubuntukylin.com/application/show.php?lang=cn&id=278][5]

## 正常挂载exfat分区
`sudo apt-get install exfat-utils`

## 搜狗输入法
[http://pinyin.sogou.com/linux/?r=pinyin][6]

## ffmpeg package
[https://launchpad.net/~mc3man/+archive/ubuntu/trusty-media][7]

## nodejs&&hexo
[https://nodejs.org/en/][8]
默认的NPM太慢，可以转投淘宝镜像

## 优秀的markdown编辑器
现在转用这个了：https://typora.io

[remarkableapp.github.io][9]

## git可视化比较工具
[External-Merge-and-Diff-Tools][10]

## 局域网同步神器BitTorrent Sync

[软件主页](https://www.getsync.com/) 
[扫盲](https://program-think.blogspot.com/2015/01/BitTorrent-Sync.html) 
需要注意的几个设置选项如图
![DeepinScrot-5830.png](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/png/2015/11/410402d76bcd052e7393eb449cdcbea6.png)

[1]: http://ohmyz.sh/
[2]: https://github.com/LiuLang/bcloud
[3]: http://blog.wiz.cn/downloads-mac-linux.html
[4]: http://www.ubuntukylin.com/application/show.php?lang=cn&amp;amp;id=279
[5]: http://www.ubuntukylin.com/application/show.php?lang=cn&amp;amp;id=278
[6]: http://pinyin.sogou.com/linux/?r=pinyin
[7]: https://launchpad.net/~mc3man/+archive/ubuntu/trusty-media
[8]: https://nodejs.org/en/
[9]: https://remarkableapp.github.io/linux/download.html
[10]: https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration#External-Merge-and-Diff-Tools
