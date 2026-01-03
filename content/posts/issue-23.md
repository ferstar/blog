---
title: "利用GitHub Actions改善MatterMost安卓客户端的消息推送"
slug: "github-actions-mattermost-push"
date: "2020-07-13T15:37:46+08:00"
tags: ['Idea', 'Linux', 'Python']
comments: true
---

MatterMost是一款非常好用的团队沟通工具，但是这货的安卓客户端推送服务非常的垃圾，夸张到昨天的消息今天才可能收到，就算挂梯子也不行。有时候团队有啥要紧事的时候就很蛋疼，只能在微信群里at某某某，体验很不好。所幸他的API非常详细，通过一番组合加上GitHub Actions服务完全可以拯救糟糕的消息推送。

### 1. 利用到的服务

- AlertOver: https://www.alertover.com
- GitHub Actions: https://github.com/features/actions

### 2. 用到的API

> 就是遍历所有频道，拿到未读消息计数，利用AlertOver进行推送

1. 公开频道未读消息 `/api/v4/users/me/teams/unread`
2. 列出所有频道 `/api/v4/users/me/teams/<channel_id>/channels`
3. 列出频道未读消息 `/api/v4/users/me/channels/<channel_id>/unread`
4. 推送AlertOver `https://api.alertover.com/v1/alert`

### 3. 配置AlertOver服务&安装客户端

> 这个没啥好说的，注册账号，下载安装客户端，比较开心的是，客户端支持 MIPush，不用单独给他留后台服务。然后再新建一个组织，如图
![image](https://user-images.githubusercontent.com/2854276/87322778-6b8a9d00-c560-11ea-9e7b-180247f5c0a5.png)

### 4. 配置GitHub Actions

1. 代码部分：https://github.com/ferstar/blog/blob/master/static/mm_notify.py
2. workflow：https://github.com/ferstar/blog/blob/master/.github/workflows/mm_notify.yml
3. secrets配置：敏感信息，如cookie等可以配置到这里，如图
![image](https://user-images.githubusercontent.com/2854276/87323301-2e72da80-c561-11ea-95a0-895f81144984.png)

### 5. 最终效果

> 一番折腾后，手机上可以比较及时的收到MatterMost中的未读消息提示，飒！

![image](https://user-images.githubusercontent.com/2854276/87391930-345ad100-c5de-11ea-9213-43a3c891fe8a.png)

> 当然你完全可以把脚本扔到自己的VPS上，然后AlertOver也可以替换成类似的服务，比如IFTTT之类，条条大路通罗马~

PS: cookie如图示
![image](https://user-images.githubusercontent.com/2854276/102732042-86b1d200-4374-11eb-9b66-215ed7a20fea.png)

白嫖的action服务越来越不守时了，只好把脚本改改放自己vps上，crontab安排起，也是蛮香的😌

> mattermost 有私人聊天信息api吗。官网好像没看到

这个我也没看到, 另外 MatterMost 在iOS上的推送挺及时的, 不需要折腾

```
# NOTE: I am not responsible for any expired content.
create@2020-07-13T15:37:46+08:00
update@2021-04-25T06:36:21+08:00
comment@https://github.com/ferstar/blog/issues/23
```
