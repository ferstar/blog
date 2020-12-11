---
title: "记一次公众号后台删库不需跑路的过程"
date: "2020-12-11T22:12:02+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-12-11T22:12:02+08:00

> update_date: 2020-12-11T22:12:16+08:00

> comment_url: https://github.com/ferstar/blog/issues/30

我digital ocean的5刀丐版vps上面放了个人公众号的服务，就是些许python脚本拼凑起来的，还是科研狗的时候偷懒搞的[东西](https://blog.ferstar.org/post/scihub_spider/)，不小心维护到现在。

前几日因为数据源站更新，需要更新爬虫策略，开vscode登上去改代码，不小心手贱删掉了工作目录，蛋疼啊，火急火燎关掉vps，
刚关完就有粉丝反馈公众号故障，所以临时挂了个维护的通知，开始苦逼恢复数据。

1. git、备份恢复 - 扑街，因为很多功能调整都是断断续续加的，没有及时的备份，拿到的旧代码相当于没用

2. extundelete大法

这个网上一堆教程，比较有用的一个参数是`after`，因为我知道确切的删文档时间点，那么只需要恢复删档时间以后的资料就可以

```shell
mount -o remount,ro /dev/sdX1
# 举个栗子，恢复一小时内删除的资料
extundelete --restore-all --after $(date -d "-1 hours" +%s) /dev/sdX1
find RECOVERED_FILES/
```
3. uncompyle6恢复丢失的py代码

extundelete恢复后，悲剧的发现py代码几乎全丢了，但神奇的是`__pycache__`居然完整恢复，于是赶紧用`uncompyle6`反编译pyc试试

```shell
for i in $(ls | awk -F . '{print $1}'); do uncompyle6 $i.cpython-36.pyc > ../$i.py; done
```

跑完效果好的出奇，基本上完美还原

4. 重启&恢复服务 - 一切正常

5. 复盘 - crontab rsync + git code 走起来，可保江山永固

> 从手欠删工作目录到恢复完成耗时1.5h，能完美恢复的关键是发现问题需要立即把盘离线（避免覆写，神仙难救）

> 大概就是损失了午休的时间，于是公众号卖惨求红包，果然收到几个热心粉丝老板的红包打赏，开心。。。

