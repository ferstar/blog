---
title: "install ubuntu 16.04 on 3850x6 server"
date: "2016-06-15T14:52:00+08:00"
tags: ['OTHERS']
comments: true
---


这破机子开机自检一大堆, 得等好久, 完了按F12选择DVD驱动器启动

安装过程没什么好讲的, 一路next

## 配置固定IP
`sudo vi /etc/network/interfaces`
网卡名称比较奇葩, 不再是`ethx`
```
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto ens9f3
#iface ens9f3 inet dhcp
iface ens9f3 inet static
address 192.168.100.99
netmask 255.255.255.0
broadcast 192.168.100.255
network 192.168.100.0
gateway 192.168.100.1
```
## 挂载nfs
`sudo apt-get install nfs-common -y`
`sudo systemctl start nfs-utils.service`
`sudo systemctl enable nfs-utils.service`
`sudo mkdir -p /media/ngs`
`sudo chmod 777 /media/ngs`
`sudo mount 192.168.100.98:/volume1/ngs /media/ngs`
开机挂载
`sudo vi /etc/fstab`
增加内容
`192.168.100.98:/volume1/ngs /media/ngs nfs defaults 0 0`

