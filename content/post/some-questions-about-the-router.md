---
title: "HG255D路由常见问题解决方法"
date: "2013-10-02T13:47:54+08:00"
tags: ['OTHERS']
comments: 
---


> **手机浏览本文推荐UC浏览器，如发现显示不全的图片，只需要在图片上长按，点击查看图片即可看到全图，可双指缩放**
打开wifi连接到路由器，然后手机浏览器登陆192.168.1.1，如图<!--more-->

![](http://wp-ferstar.bcs.duapp.com/2013/10/Screenshot_2013-10-02-13-32-12.png)

<span style="color: #ff0000;">**问题一：手机能连到路由，却不能上网**</span>

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E6%B2%A1%E6%9C%89%E7%99%BB%E5%BD%95%E7%9A%84%E7%8A%B6%E6%80%81.png)

解决方法：依次点击“服务”-“校园网认证”如图，填入你的上网账号密码，只需一次以后都不用填，然后点击保存应用即可

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E5%AE%A2%E6%88%B7%E7%AB%AF%E7%99%BB%E5%BD%95%E9%A1%B5%E9%9D%A2.png)

返回到总览页面，查看路由联网状态

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E6%AD%A3%E5%B8%B8%E8%81%94%E7%BD%91%E7%8A%B6%E6%80%81.png)

<span style="color: #ff0000;">**问题二：手机连不到路由器，老是获取不到ip地址**</span>

解决方法：这是由于路由器DHCP服务（就是自动分配ip地址的作用）没有正常启动，所以需要手动分配ip地址连接路由去启动它（这里以安卓手机为例，其他手机大同小异）

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E6%89%8B%E6%9C%BA%E7%AB%AF%E4%BF%AE%E6%94%B9%E7%BD%91%E7%BB%9C.png)

在弹出的菜单里选择高级设置，把ip获取策略改为静态

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E9%AB%98%E7%BA%A7%E7%BD%91%E7%BB%9C%E8%AE%BE%E7%BD%AE.png)

ip地址手动设置一般是192.168.1.x (x是大于100小于254的整数)，网关：192.168.1.1具体如图所示：

[caption id="" align="alignnone" width="480"]![](http://wp-ferstar.bcs.duapp.com/2013/10/%E8%AF%A6%E7%BB%86ip%E8%AE%BE%E7%BD%AE.png) 设置好后点连接[/caption]

然后你的手机就可以正常连接路由了，可以开浏览器进入管理界面，如图设置

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E9%87%8D%E5%90%AFdhcp%E6%9C%8D%E5%8A%A1.png)

什么都不用更改，直接点击右下角保存应用，dhcp服务即可恢复正常，联网设备即可正常自动获取到ip。

最后附一张正常工作状态图

![](http://wp-ferstar.bcs.duapp.com/2013/10/%E6%AD%A3%E5%B8%B8%E8%BF%90%E8%A1%8C%E7%8A%B6%E6%80%81.png)
