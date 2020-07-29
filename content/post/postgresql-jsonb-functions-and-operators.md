---
title: "Postgresql Jsonb Functions and Operators"
date: 2018-11-30T15:14:14+08:00
tags: ['OTHERS', 'SQL']
comments: false
---

PG 对 json 的支持真是美如画

https://www.postgresql.org/docs/9.5/functions-json.html

比如 hello 表有个 result 字段长这样

```json
"result": {
        "items": [
            "warrants",
            "convertiables"
        ],
        "warrants": {
            "index": 10
        }
}
```

需要把`index`大于`0`的记录找出来

```sql
SELECT *
FROM hello
WHERE (result -> 'warrants' ->> 'index') :: INT > 0
```

爽的很啊