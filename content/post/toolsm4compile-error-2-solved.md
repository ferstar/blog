---
date = "2013-11-06T11:15:34+08:00"
title = "*** [tools/m4/compile] Error 2 solved"
tags = ['OTHERS']
---

[http://www.openwrt.org.cn/bbs/forum.php?mod=viewthread&amp;tid=13909&amp;page=1#pid102019](http://www.openwrt.org.cn/bbs/forum.php?mod=viewthread&amp;tid=13909&amp;page=1#pid102019)

解决方法如下：
先进入：`/home/jopark/Documents/openwrt-dreambox/build_dir/host/m4-1.4.15/lib'此路径。<!--more-->
<div>
<div id="code_jc5">

1.  cd /home/jopark/Documents/openwrt-dreambox/build_dir/host/m4-1.4.15/lib
</div>
复制代码

</div>
对应路径自行修改自己对应的。

然后再在命令行输入：
<div>
<div id="code_ggv">

1.  sed -i -e '/gets is a security/d' ./stdio.in.h
</div>
复制代码

</div>
再重新编译即可。

或者手动打开stdio.in.h文件编辑，删除下面那行即可。
<div>
<div id="code_aDh">

1.  _GL_WARN_ON_USE (gets, "gets is a security hole - use fgets instead");
</div>
复制代码

</div>
