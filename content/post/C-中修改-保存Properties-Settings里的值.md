---
date = "2015-08-31T23:07:56+08:00"
title = "C#中修改&保存Properties.Settings里的值"
tags = ['C#']
---
打算在`Properties.Settings`中存一个不太短也不太长的string, 一直存不了, 程序退出, 就回到默认值, 着实蛋疼, google之发现算是一个低级错误, 其实就漏了一句: `Properties.Settings.Default.Save();` set完毕后save()一下就ok了


<!--more-->


存完后忽然想到这个string长度该不会有啥限制, 别溢出就糗大了, 于是查了下, 哦, 有个蛋疼的外国友人还真的自己测试了下,[跳转查看][1] 发现能存很长很长(32767个字符)

然后我默默算了下我这个小程序的list容量, 一个item大概150长, 也就是说可以存200多条数据, 呵呵, 足够了~


[1]: http://stackoverflow.com/questions/20457089/is-there-a-maximum-size-for-application-settings
