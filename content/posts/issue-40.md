---
title: "Find the row count for all tables in Postgres"
slug: "postgresql-all-tables-row-count"
date: "2021-05-07T04:03:57+08:00"
tags: ['Linux', 'PostgreSQL']
comments: true
---

> via https://stackoverflow.com/a/2611745

- total count

```SQL
SELECT
  sum(reltuples)
FROM pg_class C
LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
WHERE
  nspname NOT IN ('pg_catalog', 'information_schema') AND
  relkind='r';
```

- summary details

```SQL
SELECT
  nspname AS schemaname,relname,reltuples
FROM pg_class C
LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
WHERE
  nspname NOT IN ('pg_catalog', 'information_schema') AND
  relkind='r'
ORDER BY reltuples DESC;
```



```
# NOTE: I am not responsible for any expired content.
create@2021-05-07T04:03:57+08:00
update@2021-05-07T04:04:24+08:00
comment@https://github.com/ferstar/blog/issues/40
```
