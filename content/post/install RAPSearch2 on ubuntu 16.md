---
date = "2016-06-15T19:23:00+08:00"
title = "install RAPSearch2 on ubuntu 16.04"
tags = ['OTHERS']
---

要被3850x6这个破机子折腾疯了, biolinux8也就是ubuntu14.04装在上面不停的crash, 查log也没什么头绪, 基本就是什么hardware not ready 之类无营养的提示, boss说装个高版本的试试, 于是果断上16.04, 安装过程很美好, 完美识别了显卡驱动, 换句人话说就是可以自适应分辨率了, 好激动,![](~/19-41-19.jpg) 
于是开始安装`surpi`的pipeline, 然后噩梦从`RAPSearch2`开始...
## 报了这么个错
```
rm -f .o rapsearch prerapsearch
g++ -c -O3 -w HashSearch.cpp -o HashSearch.o -I ./
g++ -c -O3 -w BlastStat.cpp -o BlastStat.o -I ./
g++ -c -O3 -w Seg.cpp -o Seg.o -I ./
g++ -c -O3 -w mergeUnit.cpp -o mergeUnit.o -I ./
g++ -O3 -w -o rapsearch main.cpp HashSearch.o BlastStat.o Seg.o mergeUnit.o -I ./ -L ./ -lboost_serialization -lpthread -lboost_thread -lboost_system -lboost_chrono -lrt
ld: library not found for -lrt
collect2: ld returned 1 exit status
make: *** [rapsearch] Error 1
mv: rename Src/rapsearch to bin/rapsearch: No such file or directory
mv: rename Src/prerapsearch to bin/prerapsearch: No such file or directory
```
## 蛋疼3小时
...各种找方案...

## 找到方案
```
wget --no-check-certificate "https://github.com/zhaoyanswill/RAPSearch2/archive/master.zip" -O RAPSearch2-master.zip
unzip RAPSearch2-master.zip
cd RAPSearch2-master
# 我本来在辛苦的手动编译着boost, 守着跳动的终端, 忽然灵光一现
# 找找看这玩意在系统里面有没有
# find / -type f -iname "libboost_system.a" 2>>/dev/null
# 果然有, 好激动, 死马当活马医
# 立马把RAPSearch2这货需要的几个静态链接库全扣过来
cp /usr/lib/x86_64-linux-gnu/libboost_system.a .
cp /usr/lib/x86_64-linux-gnu/libboost_chrono.a .
cp /usr/lib/x86_64-linux-gnu/libboost_serialization.a .
cp /usr/lib/x86_64-linux-gnu/libboost_thread.a .
# 见证奇迹的时刻
# 终于通过了
./install
```
## THE END
此刻脑海里浮现出这么一副画面: 上学时百思不得其解的一道题, 忍不住一翻答案:"我靠, 怎么这么简单, 我TM怎么没想到! 啊啊啊..."
卒~