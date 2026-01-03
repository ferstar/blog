---
title: "Import Csv to Postgresql With Duplicated Items Removed"
slug: "import-csv-to-postgresql-with-duplicated-items-removed"
date: 2018-12-09T15:51:13+08:00
tags: ['OTHERS', 'SQL']
comments: true
---

碰到个业务需求: 把一大坨`csv`文件原样导入`PostgreSQL`中, 于是速查官方文档, 手撸`SQL`

```sql
COPY des_table (name, age, id_no)
FROM '/path/to/src/csv' DELIMITER ',' CSV HEADER;
```

然而可耻报错:

```shell
ERROR: duplicate key value violates unique constraint "uq_des_table_id_no"
key (id_no)=(3.141592653) already exists.
```

原来是目标`des_table`中`id_no`是索引, `csv`文件中有重复记录, 那么问题来了, 需要把重复的去掉, 两个思路, 要么写脚本提前把`csv`过滤一遍, 要么直接用`SQL`去排除重复, 看了下文件有两百多万行, 我选择用`SQL`直撸

Google一番, 基本思路就是先建个临时表, 然后把记录拷过去, 然后再把临时表中的记录拷到目标`table`中, 利用`PostgreSQL`新版本的一个特性`ON CONFLICT DO NOTHING`即冲突啥也不做

```sql
-- 建临时表
CREATE TEMP TABLE tmp_table
	AS
		SELECT *
		FROM des_table
WITH NO DATA;

-- 数据导入临时表
COPY tmp_table (name, age, id_no)
FROM '/path/to/src/csv' DELIMITER ',' CSV HEADER;

-- 从临时表导入数据
INSERT INTO des_table (name, age, id_no)
SELECT name, age, id_no
FROM tmp_table
ON CONFLICT DO NOTHING;

-- 导入完毕, 删掉tmp_table
DROP TABLE tmp_table;
```

