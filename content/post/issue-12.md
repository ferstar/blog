---
title: "利用 GitHub Issues 持续写博灌水"
date: "2020-01-02T11:41:46+08:00"
tags: ['Idea', 'Git', 'TODO']
comments: true
---

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

搭配 GitHub Actions 食用似乎味道更佳~

> 不知不觉 Actions 积累了一大堆 runs, 貌似目前为止(2022年01月07日) GitHub 无法批量删除这些无用的 runs, 所以写了个脚本处理下

> 更舒服的使用姿势是, 随便找个云服务商建个账号, 撸一下函数服务, 设好定时执行即可, 非常舒服

https://gist.github.com/ferstar/972623e6a7af464d5437d4a3b710ade2

```
# NOTE: I am not responsible for any expired content.
create@2020-01-02T11:41:46+08:00
update@2022-01-07T01:29:40+08:00
comment@https://github.com/ferstar/blog/issues/12
```
