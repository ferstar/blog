---
title: "Send Email When New Mailgun Messages Fail Delivery"
date: 2018-07-20T15:06:26+08:00
tags: ['SAAS']
comments: true
---

SaaS 服务用着就是舒服，更换 Mailgun 后邮件投送率大大提高，不过还是有漏网之鱼，比如网易企业邮箱，会标记垃圾邮件拒收，没办法必须给上个发送失败的通知了 。

通过几个 SaaS 服务组合来完成这个需求：

1. Mailgun webhook
2. Zapier Zaps
3. IFTTT webhook
4. Telegram Group Message

最终效果是如果信件被拒收会受到一封电报消息，如图：

![效果图](http://7xivdp.com1.z0.glb.clouddn.com/jpg/2018/7/908e33b33c9229b67fa7200786af69f2.jpg)

实施步骤：

Mailgun Webhooks：<https://app.mailgun.com/app/webhooks> 

![mailgun](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/7/4d2f5ed1c682031b72d72504c913578e.png)

Zapier integrations：<https://zapier.com/apps/mailgun/integrations> 

![zapier](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/7/f1d1df86d861f83e307ae7cd6bc79c98.png)

IFTTT：<https://ifttt.com/maker_webhooks>

![ifttt](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/7/01aeb6e3e7fdc6ae1a1efbbc3c69dacc.png)

Telegram Bot：IFTTT

![notification](http://7xivdp.com1.z0.glb.clouddn.com/png/2018/7/8d6d50ca797209341f06396fa6e06961.png)

美中不足的是 Zapier 免费版每月仅能触发100次，不过暂时也够了，被拒收的情况很少。