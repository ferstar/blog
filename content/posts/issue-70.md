---
title: "AX3600 终极改造：ShellClash 替换 Clash-Meta 核心，完美支持 Hysteria 2"
slug: "ax3600-clash-meta-upgrade"
date: "2023-01-24T01:17:09+08:00"
tags: ['Linux']
comments: true
description: "针对小米 AX3600 存储不足难题，详解利用 UPX 压缩技术替换 Clash-Meta 核心，实现对 Hysteria 2、TUIC 等新协议的完美支持，让老路由重焕青春。"
series: ["Network & Security"]
---
这个路由的 root 包括安装 shellclash 这个帖子介绍的很清楚：https://qust.me/post/ax3600_shellclash/

我自然懒得赘述，下面主要提一下如何替换 clash-meta 核心以支持 hysteria 以及 tuic 这种非主流代理协议的方法 #66 

1. 当然是先下载 clash 的啦（选 arm64 ）：https://github.com/MetaCubeX/Clash.Meta/releases，我用 Alpha，就是这么头铁
2. 解压&塞到路由器里

悲剧的事情发生了：clash-meta 这玩意解压完近 20MB，你看了下折腾完 shellclash 的路由根分区：只剩不到 8MB，灵机一动，掏出加壳压缩大法 upx，同样，先从官网下载 https://github.com/upx/upx

压缩之：`upx -9 clash`，最后 7MB 不到的样子，可以轻松塞进路由，替换掉原有 clash

```shell
root@XiaoQiang:~# du -sh /data/clash/clash
6.6M    /data/clash/clash
root@XiaoQiang:~# file /data/clash/clash
/data/clash/clash: ELF 64-bit LSB executable, ARM aarch64, version 1 (SYSV), statically linked, corrupted section header size
root@XiaoQiang:~# /data/clash/clash -v
Clash Meta alpha-096bb8d linux arm64 with go1.19.5 Mon Jan 23 06:08:40 UTC 2023
```

你以为这就完了？naive，默认固件有个地方乱拉屎 `/data/usr/log`，莫名其妙就会被 log 文件塞满，导致网络不定时卡顿，所以得弄个任务定时清一波

```shell
root@XiaoQiang:/data/usr/log# crontab -l
*/15 * * * * /usr/sbin/ntpsetclock 60 log >/dev/null 2>&1
#* * * * * /usr/sbin/startscene_crontab.lua `/bin/date "+%u %H:%M"`
0 12 * * * /usr/sbin/recordscene_crontab.lua
45 23 * * * /usr/sbin/points_sysset_pro.lua >/dev/null 2>&1
#*/1 * * * * /usr/sbin/wwdog
0 20 * * * /usr/bin/stat_lan
0 5 * * 3 /etc/init.d/web_filter_record restart >/dev/null 2>&1
0 3 * * * /etc/init.d/sysapihttpd restart >/dev/null 2>&1
0 8,19 * * * /usr/sbin/netdig.sh >/dev/null 2>&1
*/2 * * * * sh /usr/sbin/xqwhc_push.cron >/dev/null 2>&1
#*/1 * * * * /sbin/trafficd_cpucheck_wifisync.sh
0 3 * * * /usr/sbin/rmportscanresult.sh >/dev/null 2>&1
30 3 * * 1~7 /data/clash/start.sh restart >/dev/null 2>&1 #每周1~7的3点30分重启clash服务
*/3 * * * * rm -rf /data/usr/log/*  # 清垃圾日志
*/10 * * * * test -n "$(pidof clash)" && /data/clash/start.sh web_save #每10分钟保存节点配置
```

看着上面这一坨定时任务不禁有想把这玩意刷个原生 openwrt 的冲动，但回想 N 年前折腾 openwrt 孱弱的无线驱动浪费的青春，算了放弃，又不是不能用，要啥自行车。

One more thing，hysteria 这个协议比较吃 CPU，建议适当限制下行参数以降低路由负载，我一般用 100 mbps 足够用了。



```
# NOTE: I am not responsible for any expired content.
create@2023-01-24T01:17:09+08:00
update@2023-01-24T17:19:55+08:00
comment@https://github.com/ferstar/blog/issues/70
```
