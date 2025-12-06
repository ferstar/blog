---
title: "Hacking Kankun Smart Wifi Plug"
date: "2017-06-20T11:13:00+08:00"
tags: ['LINUX', 'OPENWRT', 'SHELL']
comments: true
---


闲鱼买了两kk-sp3插座，准备搭配`shairport-sync`把吃灰的有线音箱用起来

请点击此处查看说明 https://github.com/yurt-page/Kankun_KK-SP3

hack link：<http://www.anites.com/2015/01/hacking-kankun-smart-wifi-plug.html>
ssid：0K_SP3
管理IP：192.168.10.253
先telnet进去修改密码（telnet默认密码为空）

## 磁盘信息：

```
root@OpenWrt:~# df -h
Filesystem                Size      Used Available Use% Mounted on
rootfs                    1.0M    296.0K    728.0K  29% /
/dev/root                 2.0M      2.0M         0 100% /rom
tmpfs                    14.2M     60.0K     14.1M   0% /tmp
/dev/mtdblock3            1.0M    296.0K    728.0K  29% /overlay
overlayfs:/overlay        1.0M    296.0K    728.0K  29% /
tmpfs                   512.0K         0    512.0K   0% /dev
```

## 内存信息：

```shell
root@OpenWrt:~# free
			total         used         free       shared      buffers
Mem:         29060        20224         8836            0         1736
-/+ buffers:              18488        10572
Swap:            0            0            0
```

## CPU信息：

```shell
root@OpenWrt:~# cat /proc/cpuinfo 
system type                : Atheros AR9330 rev 1
machine                        : TP-LINK TL-WR703N v1
processor                : 0
cpu model                : MIPS 24Kc V7.4
BogoMIPS                : 265.42
wait instruction        : yes
microsecond timers        : yes
tlb_entries                : 16
extra interrupt vector        : yes
hardware watchpoint        : yes, count: 4, address/irw mask: [0x0000, 0x0ff8, 0x0ff8, 0x0ff8]
isa                        : mips1 mips2 mips32r1 mips32r2
ASEs implemented        : mips16
shadow register sets        : 1
kscratch registers        : 0
core                        : 0
VCED exceptions                : not available
VCEI exceptions                : not available
```

## 开关：

```shell
turn relay on 
echo 1 > /sys/class/leds/tp-link:blue:relay/brightness  
turn relay off 
echo 0 > /sys/class/leds/tp-link:blue:relay/brightness
```
## 网络配置

```shell
root@OpenWrt:~# vi /etc/config/wireless
config wifi-device 'radio0'
        option type 'mac80211'
        option channel '11'
        option hwmode '11ng'
        option path 'platform/ar933x_wmac'
        option htmode 'HT20'
        list ht_capab 'SHORT-GI-20'
        list ht_capab 'SHORT-GI-40'
        list ht_capab 'RX-STBC1'
        list ht_capab 'DSSS_CCK-40'
        option disabled '0'
        option noscan '1'

config wifi-iface
        option device 'radio0'
        option mode 'sta'
        option ssid 'your ssid'
        option encryption 'psk2+ccmp'
        option network 'wwan'
        option key '***'

root@OpenWrt:~# vi /etc/config/network
config interface 'loopback'
        option ifname 'lo'
        option proto 'static'
        option ipaddr '127.0.0.1'
        option netmask '255.0.0.0'

config globals 'globals'
        option ula_prefix 'fd12:b015:a426::/48'

config interface 'lan'
        option ifname 'eth0'
        option type 'bridge'
        option proto 'static'
        option ipaddr '192.168.10.253'
        option netmask '255.255.255.0'
        option ip6assign '60'

config interface 'wwan'
        option proto 'dhcp'
```

## kankun-json

> https://github.com/homedash/kankun-json
```shell
安装opkg
tar xz -C / -f /root/opkg-rc3.tar.gz
安装at
opkg update && opkg install at
root@OpenWrt:~# /etc/init.d/atd enable
root@OpenWrt:~# /etc/init.d/atd start
```
## 更改开关指示灯默认状态

```shell
For the stock firmware, you can configure the LEDs to act on certain events. Blink blue with network traffic:
uci set system.@led[0].name=wwan-link
uci set system.@led[0].trigger=netdev
uci set system.@led[0].dev=wlan0
uci set system.@led[0].mode='link tx rx'
uci commit system
/etc/init.d/led restart
The relay is tied to the red LED, so setting the LED to default ON will make the relay ON after bootup:
uci set system.@led[1].default=1
uci commit system
/etc/init.d/led restart
```

## 国际友人写的一个安卓应用

> [WidgetKK for SmartPlug & LIFX ](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&uact=8&ved=0ahUKEwi-g8rSmsvUAhVGxmMKHWXCDkYQFggqMAA&url=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.blogspot.choplabalagun.widgetkkforsmartplug%26hl%3Dzh_CN&usg=AFQjCNEWFeH6RMntaYElYJmR7TfNqm3MpQ&sig2=otU8wL_j5qDVNfU_PVtO3A)

```shell
Current Features:
-Voice Commands, Integrated with Google Now.
-HomeScreen Widgets for Lollipop and Marshmellow. (They should work now) (6/13/2015)
-System Alarm Clock Integration.        
-WIFI Triggers (6/7/2015)
-SSH Integration (6/13/2015) (Bug fixes 7/8/2015)
-DIMMER option for KK version 2. .(6/13/2015)
-Android Wear Integration (voice commands and wifi triggers)
-You can send custom SSH commands.(7/8/2015)
-You can deploy the JSON script from the app to any KK plug.(7/8/2015)
-AutoReboot script (pings a specific IP, if not available the plug will reboot) useful to ping router.
-Follow Me Script (pings a specific IP, if not available the plug will shutdown) useful to autoshutdown when you leave the house(Using the your phone IP).
-Floating Widget to access the KK's.
-Install OPKG bins into your KK.
-Deploy micropython bins into your KK
-LIFX Bulbs integration with all triggers (08/Oct/2016)
-WOL integration with all Triggers (09/16/2016)
```
安装 kankun-json 很方便

## 自动更改插座IP地址脚本

https://gist.github.com/ferstar/6ebad5e70e17a9f4c05dabed7bf79d7b

插座IP发生改变后会自动将kankun-json插件配置文件更新为当前IP

> 其中json解析用到了jq，关于这个神器的编译稍后再说明
