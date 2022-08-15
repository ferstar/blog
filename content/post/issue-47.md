---
title: "拥抱 WSLg"
date: "2021-11-02T22:47:57+08:00"
tags: ['Windows', 'WSL2']
comments: true
---

好了，我宣布WSLg就是个锤锤，投奔Linux怀抱

---

> 开个坑, 慢慢填

0. 垃圾WSL IO巨慢

这里喷IO慢的仔细一看基本都是项目在Windows里, 然后 runtime 在 WSL, 这他喵跨着9p不卡才怪

解决方法也很简单, runtime IDE什么的一股脑统统丢 WSL 里不就完了, 啥? 嫌空间不够用? WSL挂载磁盘了解下? 直接就是原生磁盘IO的性能

1. ~~PyCharm 全局搜索框调不出来或者一闪而逝~~`此坑已填: https://youtrack.jetbrains.com/issue/IDEA-265390`

~~这个[issue](https://github.com/microsoft/wslg/issues/96#issuecomment-858257113)里找到了神仙解法: 狂按快捷键, 直到全局搜索框出来为止, 然后 pin 住, 就欧了...~~

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

8. 偶尔 WSLg GUI 没有响应, 一般发生在长时间睡眠的唤醒时, 不频繁

~~shutdown掉子系统, 卸载重装 WSLg 再开子系统即可~~

后来定位到其实是 AMD 核显驱动的问题, 换`独显直通`用 NVIDIA 独显就没事了

9. 某次更新后发现没法完全关闭Windows defender了?

用这个工具关闭: [dControl.zip](https://github.com/ferstar/blog/files/8218101/dControl.zip)

或者随便选择装一个安全软件, 比如`火绒`即可

10. 某次更新以后网卡地球仪图标, 显示无网络?

[https://docs.microsoft.com/zh-cn/windows/privacy/manage-connections-from-windows-operating-system-components-to-microsoft-services](https://docs.microsoft.com/zh-cn/windows/privacy/manage-connections-from-windows-operating-system-components-to-microsoft-services#14-%E7%BD%91%E7%BB%9C%E8%BF%9E%E6%8E%A5%E7%8A%B6%E6%80%81%E6%8C%87%E7%A4%BA%E5%99%A8)

[现成的注册表备份: NoActiveProbe.zip](https://github.com/ferstar/blog/files/8339080/NoActiveProbe.zip)

11. 系统更新后 Scoop Apps 内应用图标丢失?

见: https://github.com/ScoopInstaller/Scoop/issues/3941

```shell
scoop reset *
```

12. zsh 粘贴又卡又慢?

看这里: https://github.com/zsh-users/zsh-autosuggestions/issues/238#issuecomment-389324292

```shell
# 粘贴到.zshrc再source一下即可
# This speeds up pasting w/ autosuggest
# https://github.com/zsh-users/zsh-autosuggestions/issues/238
pasteinit() {
  OLD_SELF_INSERT=${${(s.:.)widgets[self-insert]}[2,3]}
  zle -N self-insert url-quote-magic # I wonder if you'd need `.url-quote-magic`?
}

pastefinish() {
  zle -N self-insert $OLD_SELF_INSERT
}
zstyle :bracketed-paste-magic paste-init pasteinit
zstyle :bracketed-paste-magic paste-finish pastefinish
```

13. 微软输入法选字框消失?

> 设置〉时间和语言〉语言和区域〉选项〉微软拼音〉常规〉兼容性〉使用以前版本的微软拼音输入法

14. 开启 SSH

> 从这抄的: http://dancingline.cn/%E8%BF%9C%E7%A8%8B%E8%BF%9E%E6%8E%A5WSL2/

> 为防 404, 摘抄一份

据说自带的OpenSSH有问题，需要先卸后装

```shell
sudo apt remove openssh-server
sudo apt install openssh-server
```

修改 sshd 配置文件

```shell
Port 2222   #设置ssh的端口号, 由于22在windows中有别的用处, 尽量不修改系统的端口号
PermitRootLogin yes   # 可以root远程登录
PasswordAuthentication yes     # 允许密码验证登录
AllowUsers dancingline # 远程登录时的用户名
```

重启服务

```shell
sudo service ssh --full-restart
```

Windows端口转发(保存为.ps1 后缀, 直接运行即可, 会自动申请管理员权限)

> 防火墙配置就不多说, 我是直接关掉

```powershell
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))  
{  
  $arguments = "& '" +$myinvocation.mycommand.definition + "'"
  Start-Process powershell -Verb runAs -ArgumentList $arguments
  Break
}
# 找到WSL2的IP
$ip = bash.exe -c "ifconfig eth0 | grep 'inet '"
$found = $ip -match '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}';
if( $found ) {
$ip = $matches[0];
echo "Found IP $ip"
# 端口转发，listenport和listenaddress表示监听的端口和IP，connectport和connectaddress表示转发到的端口和IP
iex "netsh interface portproxy add v4tov4 listenport=2222 listenaddress=* connectport=2222 connectaddress=$ip";
# 展示已有的
iex "netsh interface portproxy show all;"
}
else { echo "The ip address of WSL2 cannot be found!"; }
```

完事以后就可以从局域网 or 外网直接 ssh 链接了

```shell
ssh root@x.x.x.x -p 2222
```

```
# NOTE: I am not responsible for any expired content.
create@2021-11-02T22:47:57+08:00
update@2022-08-15T06:46:18+08:00
comment@https://github.com/ferstar/blog/issues/47
```
