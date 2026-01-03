---
title: "Using COUNT(*) OVER() in current query with SQLAlchemy over PostgreSQL"
slug: "postgresql-sqlalchemy-window-function"
date: "2021-02-19T02:56:17+08:00"
tags: ['Linux', 'PostgreSQL', 'Python']
comments: true
---

> via https://stackoverflow.com/a/5215028

So I could not find any examples in the SQLAlchemy documentation, but I found these functions:

- [`count()`](http://docs.sqlalchemy.org/en/latest/core/metadata.html?highlight=label#sqlalchemy.schema.Column.label)
- [`over()`](http://docs.sqlalchemy.org/en/latest/core/metadata.html?highlight=label#sqlalchemy.schema.Column.label)
- [`label()`](http://docs.sqlalchemy.org/en/latest/core/metadata.html?highlight=label#sqlalchemy.schema.Column.label)

And I managed to combine them to produce exactly the result I was looking for:

```
from sqlalchemy import func
query = session.query(Guest, func.count(Guest.id).over().label('total'))
query = query.filter(Guest.deleted == None)
query = query.order_by(Guest.id.asc())
query = query.offset(0)
query = query.limit(50)
result = query.all()
```

Cheers!

P.S. I also found this [question on Stack Overflow](https://stackoverflow.com/questions/27510382/python-sqlalchemy-query-using-labeled-over-clause-with-orm), which was unanswered.



```
# NOTE: I am not responsible for any expired content.
create@2021-02-19T02:56:17+08:00
update@2021-02-19T02:56:31+08:00
comment@https://github.com/ferstar/blog/issues/37
```
