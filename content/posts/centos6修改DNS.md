---
title: "rocks cluster6.2修改DNS"
slug: "rocks-cluster-6-modify-dns"
date: "2016-06-17T04:46:00+08:00"
tags: ['OTHERS']
comments: true
---


- OS Rocks Cluster 6.2
- /etc/resolv.conf
- 原有的不能注释
- 只能在下面追加
- 不然会出现普通用户ssh连接需要密码的情况
- 目前原因不知
- 百度 180.76.76.76
- 阿里 223.5.5.5/223.6.6.6
- 腾讯 119.29.29.29
- 114 114.114.114.114
- 改完保存
- 不需要重启network服务, 即时生效
