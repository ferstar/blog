---
title: "对PostgreSQL jsonb部分key进行索引"
date: "2020-12-11T21:22:57+08:00"
tags: ['PostgreSQL']
comments: false
---

> created_date: 2020-12-11T21:22:57+08:00

> update_date: 2020-12-11T21:31:46+08:00

> comment_url: https://github.com/ferstar/blog/issues/29

由于是在已有的项目上添加一点新的功能，比如需要支持模糊搜索，但不凑巧的是有几个key是存在一个jsonb col里的，`like`无法命中缓存，所以查询速度略慢。

一番搜索发现`pg_trgm`模块提供函数和操作符测定字母，数字，文本基于三元模型匹配的相似性， 还有支持快速搜索相似字符串的索引操作符类，于是实测了下，确实可以命中缓存。

![image](https://user-images.githubusercontent.com/2854276/101956219-287d4480-3c3a-11eb-93e6-bd34b5d7e3db.png)

记录下启用gin index的SQL:

```sql
create extension if not exists pg_trgm;
create extension if not exists btree_gin;
create index idx_file_meta on file using gin ((meta ->> 'name'), (meta ->> 'alias') gin_trgm_ops);
```

ORM查询

```python
key = 'name'
value = 'sample'
cond = File.meta[key].astext.like(f'%{value.replace("%", "")}%')
...
# 转成实际的SQL语句就是
meta ->> 'name' like '%sample%'
```

