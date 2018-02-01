---
title: "联想Newifi mini Y1三网接入配置"
date: 2018-02-01T13:40:26+08:00
tags: ['OPENWRT', 'LINUX']
comments: true
---

> 不得不说这款路由真是神器，可玩性很高

## 三种接入

1. 有线WAN口接上级路由，网关跃点30
2. 2.4G无线中继上级AP，网关跃点20
3. USB 4G网卡接入联通4G网络，网关跃点10

## 固件

LEDE官网的固件识别不出USB，于是继续使用OPENWRT

http://downloads.openwrt.org/chaos_calmer/15.05/ramips/mt7620/openwrt-15.05-ramips-mt7620-Lenovo-y1-squashfs-sysupgrade.bin

捅菊花安装后没有5G驱动，需要装一下

`opkg update && opkg install kmod-mt76`

## ZTE MF823网卡驱动

`opkg install kmod-scsi-core kmod-usb-storage kmod-usb-net-cdc-ether kmod-usb-net`

直接会认出`usb0`网卡，正常联网

## 测试

只要有一条链路能够正常联网，路由下的设备就可以上网，非常稳定。

根据跃点设置，流量优先级3>2>1，USB网卡优先级最高。

## 参考

[Guide to ZTE MF 823 USB dongles with OpenWrt and Gargoyle Routers](https://www.tbdproductions.com.au/telstra4gzte823/)

[Newifi Mini 安装 OpenWrt](https://linuxtoy.org/archives/install-openwrt-on-newifi-mini.html)

[HOWTO use a Huawei E3372 on OpenWRT](https://gist.github.com/bjoern-r/1345e8a17f4acf41006330e688af1441)