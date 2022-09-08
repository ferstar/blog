---
title: "Git常用操作"
date: "2020-01-02T10:51:58+08:00"
tags: ['Git']
comments: true
---

1. 强行抹掉远程commit log

> 不小心把不该提交的东西提交了, 可以用这招救命, **团队协作慎用**

```shell
git reset --hard <需要回退到的commit tag>
git push --force
```

2. 强制同步远端代码

> 不小心把本地搞乱, 除了`rm and clone again`大法外, 还可以这样

```shell
git fetch origin master
git reset --hard origin/master
git pull -r
```

3. git clone xxx --depth=x 后遗症

> 包括不仅限于: 看不到太多 commit log 以及无法查看/切换远程分支

> 解决办法要么直接删了 repo 重新 clone, 这属于大力出奇迹的方案

> 要么:

```shell
git fetch --unshallow
git remote set-branches origin '*'
git fetch -v
```

> 算了，没什么好写的，官方文档很清楚，遇事不决直接查就是。

```
# NOTE: I am not responsible for any expired content.
create@2020-01-02T10:51:58+08:00
update@2022-09-08T04:45:18+08:00
comment@https://github.com/ferstar/blog/issues/10
```
