---
date = "2017-07-18T09:27:00+08:00"
title = "mongodb对类型为list的字段值进行统计"
tags = ['MONGODB', 'PYTHON']

---

mongodb中有一个字段为list类型, 经常有个需求就是要对list内的元素进行计数统计, 所以记录下此种问题的解决方法(如果是用pymongo来测试, 务必要用双引号把操作符包起来如: "$set")

先新建一个数据源例子

```sql
db.getCollection('test').insert([
{
    'tags':['a','b','d']
},
{
    'tags':['a','d']
},
{
    'tags':['b','d']
}
])
```

我们期望的结果是能够统计tags标签中的元素个数, 比如类似这样的结果

```sql
/* 1 */
{
    "_id" : "d",
    "count" : 3.0
}

/* 2 */
{
    "_id" : "b",
    "count" : 2.0
}

/* 3 */
{
    "_id" : "a",
    "count" : 2.0
}
```

SQL

```sql
db.getCollection('test').aggregate([
    {$unwind: "$tags"},
    {$group: {_id: "$tags", count: {$sum: 1}}},
]);
```

你可能想把"_id"这个key替换成别的什么名字, 比如"name", 只需要给上面的SQL加一条

```sql
db.getCollection('test').aggregate([
    {$unwind: "$tags"},
    {$group: {_id: "$tags", count: {$sum: 1}}},
    {$project: {name: "$_id", count: "$count"}}
])
```

于是得到了如下的结果

```sql
/* 1 */
{
    "_id" : "d",
    "name" : "d",
    "count" : 3.0
}

/* 2 */
{
    "_id" : "b",
    "name" : "b",
    "count" : 2.0
}

/* 3 */
{
    "_id" : "a",
    "name" : "a",
    "count" : 2.0
}
```

那个"_id"太讨厌, 去掉行不行? 当然行

```sql
db.getCollection('test').aggregate([
    {$unwind: "$tags"},
    {$group: {_id: "$tags", count: {$sum: 1}}},
    {$project: {name: "$_id", count: "$count"}, _id: 0}
])
```

所以最终的结果长这样

```sql
/* 1 */
{
    "name" : "d",
    "count" : 3.0
}

/* 2 */
{
    "name" : "b",
    "count" : 2.0
}

/* 3 */
{
    "name" : "a",
    "count" : 2.0
}
```

如果还想要更屌的操作, 这几个操作符可以好好查文档看看

`$unwind`, `$group`, `$project`

https://docs.mongodb.com/manual/reference/operator/aggregation/unwind/

https://docs.mongodb.com/manual/reference/operator/aggregation/group/

https://docs.mongodb.com/manual/reference/operator/aggregation/project/