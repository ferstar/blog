---
date = "2015-09-15T09:48:00+08:00"
title = "ubuntu14.04设置静态ip"
tags = ['UBUNTU']
---

## Desktop with NetworkManager installed
1. 鼠标流 
桌面版比较方便的就是点通知栏网络图标后编辑喽, 这个比较简单
2. 终端流
NetworkManager配置文件位置`/etc/NetworkManager/system-connections`
- 有线
```shell
[802-3-ethernet]
duplex=full
mac-address=B8:27:EB:14:E0:BF

[connection]
id=eth0
# 这个uuid并没有任何含义, 可以随便用uuidgen产生的新值替换
uuid=512de3e4-5bb7-11e5-8cbe-b827eb14e0bf
type=802-3-ethernet
timestamp=1442327046

[ipv6]
# ipv6一般是关的, 除非是幸福的高校用户
method=ignore

[ipv4]
# 自动ip这里填auto, 静态如下
method=manual
dns=192.168.1.1;223.5.5.5;
address1=192.168.1.22/24,192.168.1.1
```
- 无线
```shell
[connection]
id=tars-2.4G
uuid=fbc73a26-94f4-49aa-9c72-93e7e8db6655
type=802-11-wireless
timestamp=1442228433

[802-11-wireless]
ssid=tars-2.4G
mode=infrastructure 
mac-address=E8:4E:06:29:06:52
# 无线ap的mac地址
seen-bssids=04:A1:51:AE:0A:6F;
security=802-11-wireless-security

[802-11-wireless-security] 
# 无线安全部分
key-mgmt=wpa-psk
psk=tarsbot.702

[ipv4] 
method=manual
dns=192.168.1.1;223.5.5.5;
address1=192.168.1.33/24,192.168.1.1

[ipv6]
method=ignore
```
## Server
Setting up a static ip address is useful for a lot of things, especially if you run a web server for example and don’t want to change the port forwarding rules on your router each time it allocates a different ip to your Ubuntu server.

Only use this guide if you already know the working network configuration (ip, mask, gateway and dns servers).

First of all, open a terminal window and edit the network interfaces file:
```shell
sudo nano /etc/network/interfaces
```
You will find here something like this:
```shell
auto eth0
iface eth0 inet dhcp
```
Edit that file accordingly and replace with your own ip configuration. The dns nameservers are actually Google’s dns servers so if you don’t know your own ISP ones, you can use those:
```shell
auto eth0
iface eth0 inet static
address 192.168.100.2
netmask 255.255.255.0
gateway 192.168.100.1
dns-nameservers 8.8.4.4 8.8.8.8
```
Restart the interface:
```shell
sudo ifdown eth0 && sudo ifup eth0
```
That’s it!