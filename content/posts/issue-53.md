---
title: "撸了个甲骨文ARM(4C24G200G)的机子"
slug: "oracle-cloud-arm-vps-experience"
date: "2022-03-13T13:17:06+08:00"
tags: ['Linux']
comments: true
---

> 2022年04月28日更新：垃圾甲骨文，又莫须有删我实例，告辞。

后知后觉入了甲骨文坡县的账号, 发现正经建免费 ARM 实例几乎不可能, 于是就随便找了篇[抢购教程](https://www.daniao.org/14121.html), 具体过程不细表, 只说几个关键的点:

1. 网传的 Python 啊 Go 的啥脚本基本没啥用, 还容易被甲骨文封 IP;
2. 为了增加抢购成功率, 可以先**不配公网IP; 选个中低配/不要一下子拉满; 使用官方 OCI cli 工具来刷(基本不会被封 IP)**
3. 官方 OCI 工具也是个 Python 脚本, 视网络情况不同可能执行一次需要几秒甚至几十秒不等

贡献一个自用的脚本(依赖`at`程序做定时运行)

```shell
#!/bin/bash
  
oci compute instance launch --availability-domain LyQn:AP-SINGAPORE-1-AD-1 \
    --image-id ocid1.image.oc1.ap-singapore-1.xxx \
    --subnet-id ocid1.subnet.oc1.ap-singapore-1.ooo \
    --shape VM.Standard.A1.Flex \
    --assign-public-ip false \
    --metadata '{"ssh_authorized_keys": "ssh-rsa xxx+yyy+hHrDIzDuudkARI7/zzz/WbQYN+0sGVt096LnU8gf2VE+kPIf6hbeTcQYcZC89l4Nn0z+G5VlF1J1H15MZrVzl2XIdv2egqQXEclYtgnUT5WkDumW6A7NCWXM/9y+qqq ssh-key-2022-02-07"}' \
    --compartment-id ocid1.tenancy.oc1..zzzz \
    --shape-config '{"ocpus": 2, "memory_in_gbs": 12, "boot_volume_size_in_gbs": 50}'
# 我这用的是中配

# 执行完两分钟以后继续运行
at $(date -d "$(date) + 2 minutes" +"%H:%M %Y-%m-%d") < ~/oracle.cron.sh
```

我是挂了大概 12 小时左右就抢到两台(超免费账户限额后就不能创建新的, 所以不用担心脚本会重建一堆实例然后甲骨文把你扣到底裤不剩), **然后删掉一台, 再对剩下的一台做扩容操作(CPU/RAM/DISK 都拉满), 再上公网 IP, 再上 ipv6**

PS: 注意甲骨文的 OS 比较恶心的一点是预置了一堆 iptables 规则, 最好提前干掉(我换了`ufw`来管理, 有效降低了心智负担)

```shell
# 开放所有
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -F
# 持久化
iptables-save > /etc/iptables/rules.v4
```

默认 Ubuntu 系统内核版本已经很高了, 早就内置了`bbr`拥塞协议, 所以简单配置一下就能开启

```shell
# /etc/sysctl.conf 增加一行
net.ipv4.tcp_congestion_control=bbr
# 应用即可, 无需重启
# sysctl -p
```



```
# NOTE: I am not responsible for any expired content.
create@2022-03-13T13:17:06+08:00
update@2022-04-28T10:22:24+08:00
comment@https://github.com/ferstar/blog/issues/53
```
