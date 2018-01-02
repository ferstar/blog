---
title: "Deploy Frp on Openwrt"
date: 2018-01-02T17:47:52+08:00
tags: ['LINUX', 'OPENWRT', 'FRP']
comments: true
---

老家的路由偶尔会出状况，为了出门在外能够方便控制调试，找到[frp](https://github.com/fatedier/frp)这个神器。

1. 服务端配置参考官方说明，需要注意的是要在VPS中配置防火墙开放相应端口

2. 客户端选择对应芯片方案的二进制，家里网络不稳，所以使用`protocol = kcp`协议

3. 后台运行使用`screen`：`screen -dmS frps frps -c frps_full.ini`

4. 路由器开机运行，修改/etc/rc.local

   ```shell
   sleep 30
   screen -dmS frpc /root/frpc -c /root/frpc.ini
   exit 0
   ```

在家里的路由器和邻居路由器各部署一个，互为灾备。回单位后测试表现良好。

frps自建了http监控，可以方便地查看路由在线状态。

![设备在线状态](http://p0.cdn.img9.top/ipfs/QmdhpZUNtTsuJt26GwWZ7uX6vYfwDAyUzooQMp6gg7RL36?0.png)