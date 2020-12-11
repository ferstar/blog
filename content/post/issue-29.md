---
title: "对PostgreSQL jsonb部分key进行索引"
date: "2020-12-11T21:22:57+08:00"
tags: ['Default']
comments: false
---

> created_date: 2020-12-11T21:22:57+08:00

> update_date: 2020-12-11T21:22:57+08:00

> comment_url: https://github.com/ferstar/blog/issues/29

由于是在已有的项目上添加一点新的功能，比如需要支持模糊搜索，但不凑巧的是有几个key是存在一个jsonb col里的，`like`无法命中缓存，所以查询速度略慢。

一番搜索发现`pg_trgm`模块提供函数和操作符测定字母，数字，文本基于三元模型匹配的相似性， 还有支持快速搜索相似字符串的索引操作符类，于是实测了下，确实可以命中缓存。

