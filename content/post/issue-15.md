---
title: "JetBrains全家桶升级到2019.3无法使用输入法的解决方法"
date: "2020-01-15T08:24:42+08:00"
tags: ['Python']
comments: false
---

> created_date: 2020-01-15T08:24:42+08:00

> update_date: 2020-03-27T01:35:05+08:00

> comment_url: https://github.com/ferstar/blog/issues/15

我用的是PyCharm，也遇到这个问题，后来在官方论坛找到了解决方法：

https://intellij-support.jetbrains.com/hc/en-us/community/posts/360006740379/comments/360001272440

> Hello everyone!
> 
> Please use the following VM option -Dauto.disable.input.methods=false to resolve the problem.

我的`pycharm64.vmoptions`文件内容如下：

```shell
-Xms1024m
-Xmx4096m
-XX:ReservedCodeCacheSize=1024m
-XX:+UseCompressedOops
-XX:+UseConcMarkSweepGC
-XX:SoftRefLRUPolicyMSPerMB=50
-ea
-XX:CICompilerCount=2
-Dsun.io.useCanonPrefixCache=false
-Djava.net.preferIPv4Stack=true
-Djdk.http.auth.tunneling.disabledSchemes=""
-XX:+HeapDumpOnOutOfMemoryError
-XX:-OmitStackTraceInFastThrow
-Djdk.attach.allowAttachSelf
-Dkotlinx.coroutines.debug=off
-Djdk.module.illegalAccess.silent=true
-Dawt.useSystemAAFontSettings=lcd
-Dsun.java2d.renderer=sun.java2d.marlin.MarlinRenderingEngine
-Dsun.tools.attach.tmp.only=true
-Dauto.disable.input.methods=false
```

