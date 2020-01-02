---
title: "Ubuntu优化"
date: "2020-01-02T11:29:24+08:00"
tags: ['Linux']
comments: false
---

> created_date: 2020-01-02T11:29:24+08:00

> update_date: 2020-01-02T11:37:41+08:00

> comment_url: https://github.com/ferstar/blog/issues/11

##### 1. 关闭错误报告

> 可以选择直接卸载`apport`这个软件包, 但最好还是改配置

```shell
# 看说明
sudo vi /etc/default/apport
```

> 贴个图

![DeepinScreenshot_select-area_20200102193713](https://user-images.githubusercontent.com/2854276/71665297-49d18180-2d97-11ea-81d5-ce927479c346.png)

