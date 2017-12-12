---
title: "比较两台centos已安装程序的异同"
date: "2016-08-03T15:56:00+08:00"
tags: ['OTHERS']
comments: 
---


嗯, 一台计算节点硬件故障终于修好, 是时候把这货加入集群了, 然而比较悲催的是集群已经运行很久, 上面新安装了啥软件包我自己也记不清, 所以就需要挑一个正常运行的节点把上面已安装的程序找出来, 然后把新加入的节点默认安装的软件也列出来, 最后两者取差集即可得到需要在新节点上额外安装的程序列表, 机智如我...
## 第一步 找出目标机器已经安装的软件包列表
```
yum list installed | awk '{print $1}' | grep -v "^@" | grep "^[^0-9]" | awk -F. '{print $1}'
```
稍微解释下, 先列出已安装的软件列表, 然后简单修饰下输出, 因为我们只关心程序包名, 至于版本, 架构, 描述什么的统统不要, 所以就有了这么长的一个管道命令
假设新机为new, 旧机为old, 用以上命令分别在new old上执行, 输出结果分别保存为new.lst和old.lst
## 第二步 取新旧软件包列表的差集
其实就是找出old.lst里面有而new.lst里没有的, 这时候需要上 Python 大法
```
# 取差集
with open("new.lst", "r") as n, open("old.lst", "r") as o:
    new_lst = [i.strip() for i in n]
    old_lst = [i.strip() for i in o]
    lst = list(set(old_lst) - set(new_lst))
# 输出结果, 空格分隔, 方便第三步处理
with open("packages.lst", "w") as f:
    map(lambda x:f.write(x + " "), lst)
```
## 第三步 在新节点上安装差集软件列表
```
yum install $(cat packages.lst)
```
## 第四步 扫尾
不出意外肯定有部分是repo list里面没有的, 这些数量比较少, 可以自己人肉安装解决
比如, bcl2fastq2就需要人肉安装

> 也许有更优雅的解决方案, 不过目前这个方法比较简单粗暴, 对我来说可操作