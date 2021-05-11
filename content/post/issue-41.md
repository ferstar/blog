---
title: "Git lfs将某个文件回退到任意历史oid"
date: "2021-05-11T04:11:25+08:00"
tags: ['Default']
comments: true
---

> 最近对项目做了一个比较大的架构调整, 某个dev分支的一个单元测试数据乱入到stable分支, 导致单元测试失败, 所以需要把stable分支的测试样例bin回退到以前旧的版本

我们二进制数据是用lfs管理的, 所以并不能通过简单的git revert处理, 最终Google一通解决, 简单记录下.

假定这个文件叫`data/tests/test.bin`, 需要回退的commit id是`074bf35a`, 那么首先需要获取他的`lfs oid`

`git cat-file -p '074bf35a:data/tests/test.bin`输出如下: 

```shell
version https://git-lfs.github.com/spec/v1
oid sha256:ed60a8c13728a47db0e8789ce9b20dc212a92fd0d0fb306fd4007b9aa6dd6b57
size 32731432
```

拿到oid以后, 从lfs缓存中把旧数据拷贝出来

`cp .git/lfs/objects/ed/60/ed60a8c13728a47db0e8789ce9b20dc212a92fd0d0fb306fd4007b9aa6dd6b57 data/tests/test.bin`

然后把这个旧数据重新push到repo即可

可能的问题:

1. 本地环境可能没有旧的oid缓存, 需要从远端拉取一下: `git lfs fetch --include=data/tests/test.bin`
2. 远端环境(CI)可能取不到这个oid, 这就需要从本地重推一次: `git lfs push origin --object-id ed60a8c13728a47db0e8789ce9b20dc212a92fd0d0fb306fd4007b9aa6dd6b57`



```
# NOTE: I am not responsible for any expired content.
create@2021-05-11T04:11:25+08:00
update@2021-05-11T04:11:25+08:00
comment@https://github.com/ferstar/blog/issues/41
```
