---
title: "解决ssh终端CentOS后中文显示乱码"
date: "2016-06-17T03:30:00+08:00"
tags: ['OTHERS']
comments: true
---


先装中文语言支持
`yum -y groupinstall chinese-support`
然后编辑
`/etc/sysconfig/i18n`
`LANG="en_US.UTF-8"`
有人说要改成`zh_CN.UTF-8`我觉得并不需要, 我只希望能显示中文即可, 又不需要系统软件的help都是中文, 太别扭
source一下
`source /etc/sysconfig/i18n`
完成~
如果SSH终端还是乱码,那么需要对终端软件的编码进行配置
统一选择UTF8即可~
