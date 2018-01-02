---
title: "OpenWRT下配置仅交换加AP模式"
date: 2018-01-02T16:28:46+08:00
tags: ['LINUX', 'OPENWRT']
comments: true
---

元旦放假回老家，邻居叫帮忙整整家庭网络。由于电信已经升级了百兆光纤，所以原来的newifi mini肯定是跑不动了，测试了下5G撑死跑到70Mbps。于是试了试邻居才淘的TP TL-WDR6300，一番测试除了几无可玩性以外，其他完胜newifi mini，百兆宽带基本能跑满，只好淘汰当AP扩展使了，农村地方大，一个AP很难满足全方位覆盖。

重刷了PandoraBox固件，进luci配置界面-->网络-->接口-->LAN-->禁用DHCP服务器即可将其变为AP+交换机模式

为了让这种模式下该路由可以正常联网，需要指定上级路由为网关，并设置合适的DNS服务器，如图

![LAN配置](http://p2.cdn.img9.top/ipfs/QmS7CiFMnjH6pAQSuzeBsZroeCRSvc7KeSqF9hzQbZFXom?2.png)

另外，newifi mini只有3个RJ45物理接口（2LAN+1WAN），为了多出一个LAN，接下来需要把WAN当LAN口使，配置很简单，如图，就是划分VLAN

![VLAN配置图](http://p2.cdn.img9.top/ipfs/QmYdiUW19WWZ2dMH8BoC4V6Z7YPsnHBXzwQUSv3zW3STF6?2.png)

“端口4”即WAN口，VLAN ID 1选择“不关联”，VLAN ID 2选择“关”，这样LAN1/LAN2/WAN口就都相当于LAN口了。