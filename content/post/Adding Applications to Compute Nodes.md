+++
date = "2016-06-20T13:18:00+08:00"
title = "Adding Applications to Compute Nodes"
tags = ['OTHERS']

+++

两种方法
## 1. 将要共享的二进制应用程序放在NFS存储, 指定全局搜索PATH即可
## 2. rocks cluster 6.0以后有一个专门的目录可以共享应用程序 /share/apps
官方手册原文如下, 基本上也是利用NFS存储来达到共享的目的
```
If you have code you’d like to share among the compute nodes, but your code isn’t in an RPM (or in a roll), then
this procedure describes how you can share it with NFS.
On the frontend, go to the directory /share/apps.
# cd /share/apps
Then add the files you’d like to share within this directory.
All files will also be available on the compute nodes under: /share/apps. For example:
# cd /share/apps
# touch myapp
# ssh compute-0-0
# cd /share/apps
# ls
myapp
```
> 以上注意要合理分配权限, 避免普通用户无法运行程序的尴尬
> 同时计算节点的存储部分也应该放在NFS存储位置
