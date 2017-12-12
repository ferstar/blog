---
date = "2014-12-22T21:59:04+08:00"
title = "利用手头设备搞定ss翻墙~"
tags = ['OPENWRT', 'LINUX']
---

设备1:Buffalo WZR-HP-G300NH2 现运行固件:<a title="关于">DD-WRT v24-sp2 (03/29/14) giga</a>

设备2:Linksys EA6500 现运行固件:OpenWrt Attitude Adjustment 12.09-beta

起先用设备2刷dd-wrt折腾ss两天无果，后来发现固件iptables和dnsmasq缺失转发参数支持，ss能够运行但无法穿墙，遂放弃，转投设备1，挑现成openwrt方案，问题主要集中在给这货刷openwrt上面，刷好openwrt后，按部就班非常顺利，几个关键字google，goagent，shadowsocks，chinadns……

贴几个折腾过程中的链接，不分先后（大部分是google+wiki获得）：

http://www.right.com.cn/forum/thread-117225-1-1.html

https://github.com/posborne/wzr-hp-g300nh2-openwrt-flasher

http://sourceforge.net/projects/openwrt-dist/files/shadowsocks-libev/1.6.1-1e3ecb2/

http://hong.im/2014/03/16/configure-an-openwrt-based-router-to-use-shadowsocks-and-redirect-foreign-traffic/

……

最后总结下，非主流方案比如dd-wrt+ss的组合最好少试，吃力不讨好；
