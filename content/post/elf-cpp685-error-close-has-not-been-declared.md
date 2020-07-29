---
title: "close has not been declared"
date: "2013-11-06T11:32:49+08:00"
tags: ['LINUX', 'OPENWRT']
comments: true
---


[http://www.openwrt.org.cn/bbs/forum.php?mod=viewthread&amp;tid=12675](http://www.openwrt.org.cn/bbs/forum.php?mod=viewthread&amp;tid=12675)

<!--more-->参考trunk的源码和此问题"https://dev.openwrt.org.cn/ticket/45"

修改 ./build_dir/host/mklibs/src/mklibs-readelf/elf.cpp
<div>
<div id="code_ftf">

1.2.  #include "elf_data.hpp"
3.4.  #include &lt;stdexcept&gt;
5.6.  #include &lt;fcntl.h&gt;
7.  #include &lt;sys/mman.h&gt;
8.  #include &lt;sys/stat.h&gt;
  </div>
  复制代码

</div>
下面添加一行"#include &lt;unistd.h&gt;"成：
<div>
<div id="code_U9o">

1.2.  #include "elf_data.hpp"
3.4.  #include &lt;stdexcept&gt;
5.6.  #include &lt;fcntl.h&gt;
7.  #include &lt;sys/mman.h&gt;
8.  #include &lt;sys/stat.h&gt;
9.  #include &lt;unistd.h&gt;
  </div>
  复制代码

</div>
解决问题。
