---
title: "OpenWRT配置双线叠加(有线拨号+无线中继)及负载均衡"
date: 2018-01-02T16:57:37+08:00
tags: ['LINUX', 'OPENWRT']
comments: true
---

> 路由: Newifi mini
>
> 固件: PandoraBox r1024
>
> 无线: 电信20Mbps
>
> 有线: 广电10Mbps

1. 正常拨号，**网关跃点设为40**
2. 虚拟WAN接口创建两个虚拟WAN口，**选中断线自动重拨，最低在线接口数设为1**
3. 无线配置界面点搜索，选中需要中继的无线信号，**新建接口名称命名为“VWAN2”**
4. 负载均衡策略选balance

放几张图

![无线概况](http://p2.cdn.img9.top/ipfs/QmZVHaLUjNAkhXRAXfe4GQWzu3yBj9ePryk4AipqjboimU?2.png)

![接口](http://p3.cdn.img9.top/ipfs/QmZ4rJrfHmHuMRK8g76gVhbfLJpGWPCdebwrTa9wy11CLQ?3.png)

![负载均衡配置](http://p0.cdn.img9.top/ipfs/QmcZEqU4wtMNz6e7KRfANvrovDjLksHJ6yRcFUyMBuMkZS?0.png)

用speedtest测速显示上传下载带宽均提升了一倍多~well done！
