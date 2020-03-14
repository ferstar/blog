---
title: "Ubuntu禁用自动挂载USB设备"
date: "2020-03-14T09:17:59+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-03-14T09:17:59+08:00

> update_date: 2020-03-14T09:20:07+08:00

> comment_url: https://github.com/ferstar/blog/issues/18

> 18.04.4有效，有的帖子说禁用`udisks2.service`服务这招并不靠谱

```shell
sudo apt install dconf-editor
```
配置如图：
![image](https://user-images.githubusercontent.com/2854276/76678989-8f23f200-6617-11ea-8ef2-668854c64bb4.png)

