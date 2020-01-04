---
title: "利用 GitHub Issues 持续写博灌水"
date: "2020-01-02T11:41:46+08:00"
tags: ['Git', 'Idea', 'TODO']
comments: false
---

> created_date: 2020-01-02T11:41:46+08:00

> update_date: 2020-01-04T06:20:50+08:00

> comment_url: https://github.com/ferstar/blog/issues/12

如题，有好的想法随时开`issue`写一发，然后借助`CI`自动把同一`issue`下的`comments`都拼接到一起，生成`post`。

每次想到什么写什么，不论多少，没有一定要写完的压力，日积月累，应该会能形成一些起码篇幅不小的博文，想想都好激动的说。

基本思路就是：

1. 新建一个issue，或者评论一个issue
2. 触发一个issue event
3. 利用webhook将这个event推送到vps
4. 解析event中的issue id
5. 通过issue id调用github api获得issue及comments正文
6. 拼装成hugo post
7. 提交到blog repo
8. 触发push event
9. vps收到push event后拉取blog repo最新提交
10. 调用hugo命令重新生成blog页面

其实就是issue+comments到hugo post的一个转换过程，对应关系如下：

```
issue label --> hugo tags
issue + comments --> hugo article(post)
issue create date --> hugo post time
issue or comments update date --> hugo post update date
comments --> hugo post comments
```

除`1`需要人肉参与外，剩余流程都可以自动进行，也即所谓的`CI`（实现这样一个流程想想其实还是有一定的技术门槛的）

> _整个流程详解及代码待续_

测试翻车了，删除comment没反应，原来是策略失误，github webhook 推送日志如下

```json
Headers

Request URL: https://api.ferstar.org/postreceive
Request method: POST
content-type: application/json
Expect: 
User-Agent: GitHub-Hookshot/a6f2714
X-GitHub-Delivery: 3f5b10d2-2eae-11ea-9f6f-23c8940b9838
X-GitHub-Event: issue_comment

Payload

{
  "action": "deleted",
...
```