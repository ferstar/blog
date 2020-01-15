---
title: "JetBrains全家桶升级到2019.3无法使用输入法的解决方法"
date: "2020-01-15T08:24:42+08:00"
tags: ['Python']
comments: false
---

> created_date: 2020-01-15T08:24:42+08:00

> update_date: 2020-01-15T08:25:00+08:00

> comment_url: https://github.com/ferstar/blog/issues/15

我用的是PyCharm，也遇到这个问题，后来在官方论坛找到了解决方法：

https://intellij-support.jetbrains.com/hc/en-us/community/posts/360006740379/comments/360001272440

> Hello everyone!
> 
> Please use the following VM option -Dauto.disable.input.methods=false (https://intellij-support.jetbrains.com/hc/en-us/articles/206544869-Configuring-JVM-options-and-platform-properties) to resolve the problem.

