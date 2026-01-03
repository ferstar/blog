---
title: "Remove Duplicates in Postgresql"
slug: "remove-duplicate-rows-in-postgresql"
date: 2018-12-09T16:40:41+08:00
tags: ['OTHERS', 'SQL']
comments: true
---

```sql
DELETE
FROM des_table
WHERE id IN (SELECT id
            FROM des_table
            WHERE dup_col IN (SELECT dup_col FROM des_table GROUP BY dup_col HAVING count(dup_col) > 1))
	AND id NOT IN (SELECT min(id)
                  FROM des_table
                  WHERE dup_col IN (SELECT dup_col FROM des_table GROUP BY dup_col HAVING count(dup_col) > 1));
```

效果就是保留了重复记录`dup_col`中`id`最小的那个

想到个更简单的

```sql
DELETE
FROM dst_table
WHERE id NOT IN (SELECT max(id) FROM dst_table GROUP BY dup_col);
```
