---
title: "parallel-meta"
slug: "parallel-meta"
date: "2016-07-14T11:16:00+08:00"
tags: ['OTHERS']
comments: true
---


vi <http://www.computationalbioenergy.org/parallel-meta.html>
需要R依赖, 然而Base源里面没有,只能从别处安装
当然万事都可以从源码上, 但是这样太麻烦
作为一个懒人, 需要用一种优雅的方式来安装
`yum install  epel-release`
装完此包后还要启用epel
`vi /etc/yum.repos.d/epel.repo`
把enable=0改成1, 保存退出, 就可以使用yum大法了
`yum install R`

环境变量很重要
```
Configure the environment variables
export ParallelMETA=Path to Parallel-META
export PATH=”$PATH:$ParallelMETA/bin”
Rscript parallel-meta/Rscript/PM_Config.R
```
测试用例
```
20
|-- meta.txt
|-- seq
|   |-- S9066B.fa
|   |-- S9066I.fa
|   |-- S9138B.fa
|   |-- S9138I.fa
|   |-- S9155B.fa
|   |-- S9155I.fa
|   |-- S9170B.fa
|   |-- S9170I.fa
|   |-- S9182B.fa
|   |-- S9182I.fa
|   |-- S9202B.fa
|   |-- S9202I.fa
|   |-- S9296B.fa
|   |-- S9296I.fa
|   |-- S9307B.fa
|   |-- S9307I.fa
|   |-- S9320B.fa
|   |-- S9320I.fa
|   |-- S9412B.fa
|   `-- S9412I.fa
`-- seq.list
```
一条龙命令
`pipeline -i seq.list -m meta.txt`
不指定输出目录默认是`default_out`
