---
date = "2016-07-27T09:27:00+08:00"
title = "模拟xorg视窗环境的神器Xvfb"
tags = ['OTHERS']
---

via <http://www.puritys.me/docs-blog/article-262-%E5%AE%89%E8%A3%9D-XVFB-%E5%81%9A-Selenium-%E6%B8%AC%E8%A9%A6.html>
常在终端走, 差点忘了有的程序是要X视窗环境才能跑的, 所以这就是这个玩意的价值所在, 安装很简单, centos下
`yum install xorg-x11-server-Xvfb`
然后就可以愉快的玩耍了
运行需要X视窗环境的程序前先把他开启, 用完再kill掉, 嗯, 很完美
```
...
source activate my_root
Xvfb :99 &  # 指定视窗编号为99
xvfb_pid=$!  # 记下进程pid
export DISPLAY=:99  # 指定程序输出视窗编号, 对应上面99
ete3 view -t outTree.v3 -i outTree.pdf
kill -9 $xvfb_pid  # 用完kill掉
tar cf outTree.tar.bz2 --use-compress-prog=pbzip2 outTree.pdf
bypy upload outTree.tar.bz2
```