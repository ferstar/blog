---
title: "检查某列是否在某表中"
date: "2019-12-25T23:17:00+08:00"
tags: ['PYTHON']
comments: true
---

> 某次数据库升级漏了几个commit, 得修一下, 还是写个alembic, 到时候upgrade就自动修复, 爽歪歪

因为主要就是丢失了几个col, 但又不确定线上哪几个表丢了哪些col, 那么就需要根据数据库实际情况来判断要不要加col, 主要就一句SQL:

```sql
select xxx in (
    select column_name
    from information_schema.columns
    where table_name = 'xxx_table'
      and table_schema = 'public')
```

转成alembic就是这么个func:

```python
def is_col_in(conn, table, col):
    sql = f"""
        select '{col}' in (
            select column_name
            from information_schema.columns
            where table_name = '{table}'
              and table_schema = 'public')
    """
    return conn.execute(sql).fetchone()[0]


def upgrade():
    conn = op.get_bind()
    for table, col in missing_tables:
        if not is_col_in(conn, table, col):
            pass
    ...
```
 
 怀疑哪些col丢了就轮一遍, 再搞一次, 没毛病
