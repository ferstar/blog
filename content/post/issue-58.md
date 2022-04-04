---
title: "薅大厂羊毛之改善MatterMost安卓客户端的消息推送"
date: "2022-04-04T13:23:51+08:00"
tags: ['Python']
comments: true
---

> #23 之前这里用的`Alertover`服务最近正式扑街没法用, 只好再挪个别的法子

用到的推送工具: [PushDeer](https://github.com/easychen/pushdeer)

脚本运行环境: 腾讯云函数

代码基本还是原来的, 只不过通过`Alertover`服务推送消息变成了使用`PushDeer`, 对应的方法改造也很简单, 就不放码了: [发送示例](https://github.com/easychen/pushdeer#%E5%8F%91%E9%80%81%E5%AE%9E%E4%BE%8B)

至于云函数, 网上一堆教程, 这也不啰嗦, 我配置了**每五分钟**运行一次, 主动调低了实例内存要求至`64MB`

当然节假日最好是不要推送的, 这就需要另一个 API 服务: http://tool.bitefu.net/jiari/ 检测消息前判断一下是否工作日, 是工作日才检查&发通知, 完美!



```
# NOTE: I am not responsible for any expired content.
create@2022-04-04T13:23:51+08:00
update@2022-04-04T13:24:00+08:00
comment@https://github.com/ferstar/blog/issues/58
```
