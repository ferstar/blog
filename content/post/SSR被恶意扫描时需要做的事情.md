---
title: "SSR被恶意扫描时需要做的事情"
date: "2017-09-07T14:18:00+08:00"
tags: ['LINUX', 'IPTABLES']
comments: true
---


 两月前买了个DO5刀的VPS，建了个SSR方便自己爬墙，早上发现连接有点问题，就登录看了下，系统负载正常，不过SSR log显示有不明IP在恶意扫描SSR端口，所以需要着手block掉这些垃圾IP

1. 查log

   ```shell
   less /var/log/shadowsocksr.log
   2017-09-06 14:10:03 ERROR    tcprelay.py:1093 can not parse header when handling connection from ::ffff:203.94.12.157:64531
   2017-09-06 14:10:03 WARNING  common.py:238 unsupported addrtype 69, maybe wrong password or encryption method
   2017-09-06 14:10:03 WARNING  tcprelay.py:521 Protocol ERROR, TCP ogn data 474554202f20485454502f312e310d0a0d0a from ::ffff:203.94.12.157:18833 via port 443 by UID 443
   2017-09-06 14:10:03 ERROR    tcprelay.py:1093 can not parse header when handling connection from ::ffff:203.94.12.157:18833
   2017-09-06 14:10:05 WARNING  common.py:238 unsupported addrtype 69, maybe wrong password or encryption method
   2017-09-06 14:10:05 WARNING  tcprelay.py:521 Protocol ERROR, TCP ogn data 474554202f20485454502f312e310d0a0d0a from ::ffff:203.94.12.157:18915 via port 443 by UID 443
   2017-09-06 14:10:05 ERROR    tcprelay.py:1093 can not parse header when handling connection from ::ffff:203.94.12.157:18915
   2017-09-06 14:11:14 WARNING  common.py:238 unsupported addrtype 69, maybe wrong password or encryption method
   2017-09-06 14:11:14 WARNING  tcprelay.py:521 Protocol ERROR, TCP ogn data 474554202f20485454502f312e310d0a0d0a from ::ffff:203.94.12.157:32581 via port 443 by UID 443
   ```

   如上，可以看到类似`203.94.12.157`这个IP在疯狂的连接，下一步需要把这些IP挑出来

2. 筛选IP

   > 筛选出所有试错的IP，存储到`ip_list.txt`文件中

   ```shell
   grep 'can not parse header' /var/log/shadowsocksr.log | awk -F: '{print $(NF - 1)}' > ip_list.txt
   ```

3. 查询恶意IP归属地并计数排序

   之前写过[查询最近暴力破解服务器密码的IP归属地](https://ferstar.org/post/root/cha-xun-zui-jin-bao-li-po-jie-fu-wu-qi-mi-ma-de-ipgui-shu-di)的脚本，所以直接拿过来用，跑一跑

   | ip             | count | country | isp  | area | region | city |
   | -------------- | ----- | ------- | ---- | ---- | ------ | ---- |
   | 203.94.12.157  | 10564 | 中国      | 电信   | 华东   | 上海市    | 上海市  |
   | 183.131.67.233 | 1757  | 中国      | 电信   | 华东   | 浙江省    | 金华市  |
   | 118.193.31.222 | 311   | 中国      |      | 华中   | 河南省    |      |
   | 50.123.186.209 | 123   | 美国      |      |      |        |      |

   可以看到扫描次数在三位数以上的IP有4个

4. iptables ban之

   ```shell
   iptables -I INPUT -s 203.94.0.0/16 -j DROP
   iptables -I INPUT -s 183.131.0.0/16 -j DROP
   iptables -I INPUT -s 118.193.0.0/16 -j DROP
   ```

5. iptables的常见用法

   ```shell
   linux下使用iptables封ip段的一些常见命令：

   封单个IP的命令是：
   iptables -I INPUT -s 211.1.0.0 -j DROP

   封IP段的命令是：
   iptables -I INPUT -s 211.1.0.0/16 -j DROP
   iptables -I INPUT -s 211.2.0.0/16 -j DROP
   iptables -I INPUT -s 211.3.0.0/16 -j DROP

   封整个段的命令是：
   iptables -I INPUT -s 211.0.0.0/8 -j DROP

   封几个段的命令是：
   iptables -I INPUT -s 61.37.80.0/24 -j DROP
   iptables -I INPUT -s 61.37.81.0/24 -j DROP

   解封的话：
   iptables -D INPUT -s IP地址 -j REJECT
   iptables -F 全清掉了

   如果想开机就自动封锁某个IP，那就编辑/etc/sysconfig/iptables文件，添加一行
   -I INPUT -s IP地址 -j DROP
   然后执行/etc/init.d/iptables restart重启iptables
   ```

   ​