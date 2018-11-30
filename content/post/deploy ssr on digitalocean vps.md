---
title: "deploy ssr on digitalocean vps"
date: "2017-07-19T16:22:00+08:00"
tags: ['VPS', 'SSR', 'UBUNTU']
comments: true
---


感觉买的`ss`账号越来越慢,  刚好本月到期, 就干脆撸个DO账号自己搭, 就选那个`5$`的配置, 挺划算的.

发现网上很多好人[写好的脚本](https://github.com/iMeiji/shadowsocks_install/wiki/shadowsocksR-%E4%B8%80%E9%94%AE%E5%AE%89%E8%A3%85), 随便拿一个开撸

## 一键ssr

```shell
wget --no-check-certificate https://raw.githubusercontent.com/iMeiji/shadowsocks_install/master/shadowsocksR.sh
chmod +x shadowsocksR.sh
./shadowsocksR.sh 2>&1 | tee shadowsocksR.log
```

## 一键bbr

[Debian/Ubuntu TCP BBR 改进版/增强版](https://ferstar.org/post/root/Debian/Ubuntu%20TCP%20BBR%20%E6%94%B9%E8%BF%9B%E7%89%88/%E5%A2%9E%E5%BC%BA%E7%89%88)

```shell
wget --no-check-certificate -qO 'BBR.sh' 'https://moeclub.org/attachment/LinuxShell/BBR.sh' && chmod a+x BBR.sh && bash BBR.sh -f
# 上命令执行完后会自动重启
wget --no-check-certificate -qO 'BBR.sh' 'https://moeclub.org/attachment/LinuxShell/BBR.sh' && chmod a+x BBR.sh && bash BBR.sh -f
```

### 完整代码

```shell
#!/bin/bash
 
[ "$EUID" -ne '0' ] && echo "Error,This script must be run as root! " && exit 1
[ $# -gt '1' ] && [ "$1" == '-f' ] && tmpKernelVer="$2" || tmpKernelVer='';
[ -z "$(dpkg -l |grep 'grub-')" ] && echo "Not found grub." && exit 1
which make >/dev/null 2>&1
[ $? -ne '0' ] && {
echo "Install make..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq make >/dev/null 2>&1
which make >/dev/null 2>&1
[ $? -ne '0' ] && {
echo "Error! Install make. "
exit 1
}
}
which awk >/dev/null 2>&1
[ $? -ne '0' ] && {
echo "Install awk..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gawk >/dev/null 2>&1
which awk >/dev/null 2>&1
[ $? -ne '0' ] && {
echo "Error! Install awk. "
exit 1
}
}
which gcc >/dev/null 2>&1
[ $? -ne '0' ] && {
echo "Install gcc..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gcc >/dev/null 2>&1
which gcc >/dev/null 2>&1
[ $? -ne '0' ] && {
echo "Error! Install gcc. "
echo "Please 'apt-get update' and try again! "
exit 1
}
}
GCCVER="$(readlink `which gcc` |grep -o '[0-9].*')"
GCCVER1="$(echo $GCCVER |awk -F. '{print $1}')"
GCCVER2="$(echo $GCCVER |awk -F. '{print $2}')"
[ "$GCCVER1" -gt '4' ] && CheckGCC='0' || CheckGCC='1'
[ "$CheckGCC" == '1' ] && [ -n "$GCCVER2" ] && [ "$GCCVER2" -ge '9' ] && CheckGCC='0'
[ "$CheckGCC" == '1' ] && {
echo "The gcc version require gcc-4.9 or higher. "
echo "You can try apt-get install -y gcc-4.9 or apt-get install -y gcc-6"
echo "Please upgrade it manually! "
exit 1
}
KernelVer='';
KernelBitVer='';
MainURL='http://kernel.ubuntu.com/~kernel-ppa/mainline'
[ -n "$tmpKernelVer" ] && {
wget -qO /dev/null "$MainURL/$tmpKernelVer"
[ $? -ne '0' ] && echo 'Please input a vaild kernel version! exp: v4.11.9.' && exit 1
KernelVer="$tmpKernelVer"
}
[ -z "$tmpKernelVer" ] && {
KernelVerBIG="$(wget -qO- "$MainURL" |awk -F '/">|href="' '{print $2}' |sed '/rc/d;/^$/d' |tail -n1)"
[ -n "$KernelVerBIG" ] && KernelVer="$(wget -qO- "$MainURL" |awk -F '/">|href="' '{print $2}' |sed '/rc/d;/^$/d' |grep ''${KernelVerBIG}'' |sort -n |tail -n1)"
}
[ -z "$KernelVer" ] && echo 'Error,Get Kernel fail! ' && exit 1
ReleaseURL="$(echo -n "$MainURL/$KernelVer")"
KernelBit="$(getconf LONG_BIT)"
[ "$KernelBit" == '32' ] && KernelBitVer='i386'
[ "$KernelBit" == '64' ] && KernelBitVer='amd64'
[ -z "$KernelBitVer" ] && echo "Error! " && exit 1
HeadersFile="$(wget -qO- "$ReleaseURL" |awk -F '">|href="' '/generic.*.deb/{print $2}' |grep 'headers' |grep "$KernelBitVer" |head -n1)"
[ -n "$HeadersFile" ] && HeadersAll="$(echo "$HeadersFile" |sed 's/-generic//g;s/_'${KernelBitVer}'.deb/_all.deb/g')"
[ -z "$HeadersAll" ] && echo "Error! Get Linux Headers for All." && exit 1
echo "$HeadersFile" | grep -q "$(uname -r)"
[ $? -ne '0' ] && echo "Error! Header not be matched by Linux Kernel." && exit 1
echo -ne "Download Kernel Headers for All\n\t$HeadersAll\n"
wget -qO "$HeadersAll" "$ReleaseURL/$HeadersAll"
echo -ne "Install Kernel Headers for All\n\t$HeadersAll\n"
dpkg -i "$HeadersAll" >/dev/null 2>&1
echo -ne "Download Kernel Headers\n\t$HeadersFile\n"
wget -qO "$HeadersFile" "$ReleaseURL/$HeadersFile"
echo -ne "Install Kernel Headers\n\t$HeadersFile\n"
dpkg -i "$HeadersFile" >/dev/null 2>&1
echo -ne "Download BBR POWERED Source code\n"
[ -e ./tmp ] && rm -rf ./tmp
mkdir -p ./tmp && cd ./tmp
[ $? -eq '0' ] && {
wget --no-check-certificate -qO- 'https://moeclub.org/attachment/LinuxSoftware/bbr/tcp_bbr_powered.c.deb' >./tcp_bbr_powered.c
echo 'obj-m:=tcp_bbr_powered.o' >./Makefile
make -s -C /lib/modules/$(uname -r)/build M=`pwd` modules CC=`which gcc`
echo "Loading TCP BBR POWERED..."
[ -f ./tcp_bbr_powered.ko ] && [ -f /lib/modules/$(uname -r)/modules.dep ] && {
cp -rf ./tcp_bbr_powered.ko /lib/modules/$(uname -r)/kernel/net/ipv4
depmod -a >/dev/null 2>&1
}
modprobe tcp_bbr_powered
[ ! -f /etc/sysctl.conf ] && touch /etc/sysctl.conf
sed -i '/net.core.default_qdisc.*/d' /etc/sysctl.conf
sed -i '/net.ipv4.tcp_congestion_control.*/d' /etc/sysctl.conf
echo "net.core.default_qdisc = fq" >>/etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control = bbr_powered" >>/etc/sysctl.conf
}
lsmod |grep -q 'bbr_powered'
[ $? -eq '0' ] && {
sysctl -p >/dev/null 2>&1
echo "Finish! "
exit 0
} || {
echo "Error, Loading BBR POWERED."
exit 1
}
```

## 改配置

`vi /etc/shadowsocks.json`

```python
{
    "server":"0.0.0.0",
    "server_ipv6":"::",
    "server_port":443,  # 常用端口据说比较稳
    "local_address":"127.0.0.1",
    "local_port":1080,
    "password":"passwd",
    "timeout":120,
    "method":"chacha20",  # chacha20据说比较快
    "protocol":"origin",
    "protocol_param":"",
    "obfs":"plain",
    "obfs_param":"",
    "redirect":"",
    "dns_ipv6":false,
    "fast_open":true,  # 开了这个据说也比较快
    "workers":1
}
```

## 防火墙开端口

这个可以在DO控制面板上编辑防火墙规则, 添加`ssr`端口(我用的`443`)

## 客户端

https://github.com/shadowsocksr/shadowsocksr-csharp/releases

## 测试

一般都是开油管跑`1080p`, 试了下, 能稳定在`20Mbps`, 延迟`200ms`左右, 表现还是蛮不错的, 比之前买的`ss`账号快多了(应该是树大招风, 被干扰的原因)
