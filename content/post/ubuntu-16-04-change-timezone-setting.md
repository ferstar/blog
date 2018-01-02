---
title: "Ubuntu 16.04变更时区设定"
date: 2018-01-02T15:58:08+08:00
tags: ['LINUX', 'UBUNTU']
comments: true
---

以前常用**timedatectl**，先取得timezone列表

`timedatectl list-timezones`

然而列表很长，所以`grep`下

`timedatectl list-timezones | grep Asia`

找到希望的区域设定即可

`timedatectl set-timezone Asia/Hong_Kong`

设定好后可以用timedatectl命令检查时区设定是否正确

```shell
# timedatectl 
      Local time: Tue 2018-01-02 16:06:52 CST
  Universal time: Tue 2018-01-02 08:06:52 UTC
        RTC time: Tue 2018-01-02 08:06:52
       Time zone: Asia/Chongqing (CST, +0800)
 Network time on: yes
NTP synchronized: yes
 RTC in local TZ: no
```

以上是Linux通用方法，有没有简单点的呢？还真有

`dpkg-reconfigure tzdata`

巨简单