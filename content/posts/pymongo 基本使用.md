---
title: "pymongo 基本使用"
slug: "python-pymongo-basic-usage-tutorial"
date: "2017-07-24T16:11:00+08:00"
tags: ['PYTHON', 'PYMONGO']
comments: true
---


> 转自[pymongo 基本使用](http://funhacks.net/2016/03/26/pymongo%20%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8/)

[pymongo](https://api.mongodb.org/python/current/tutorial.html) 是在 `python` 中操作 `mongodb` 的一个包，使用方法跟 `mongodb` 的 `shell` 命令行类似。本文使用的`pymongo` 版本是 `3.2.1`。

# 连接数据库

```python
# -*- coding: utf-8 -*-
# pymongo 版本 3.2.1

import re
from pymongo import MongoClient
from bson.objectid import ObjectId

def con_mongo():
    """连接数据库"""
    # 建立连接
    client = MongoClient(host='127.0.0.1', port=27017)
    return client
```

# 插入数据

```python
def insert_data():
    """插入数据

    :return:
    """
    client = con_mongo()

    # 文档数据
    record_list = []
    dict1 = {"name": "lucy", "sex": "female", "job": "Nurse", "age": 23}
    dict2 = {"name": "peter", "sex": "male", "job": "Teacher", "age": 22}
    dict3 = {"name": "Jay", "sex": "male", "job": "Engineer", "age": 28}
    dict4 = {"name": "layr", "sex": "male", "job": "Engineer", "age": 29}
    record_list.append(dict1)
    record_list.append(dict2)
    record_list.append(dict3)
    record_list.append(dict4)

    # insert data to db:test/collection: user
    client.test.user.insert_many(record_list)
```

# 更新数据

```Python
def update_data():
    """更新数据

    :return:
    """
    client = con_mongo()

    # 更新 lucy 的年龄
    new_age = {'age': 25}
    client.test.user.update_one({'name': 'lucy'}, {'$set': new_age})
    client.test.user.update_one({'name': 'lucy'}, {'$set': {'age': 26}})

    # 所有记录
    record = client.test.user.find()
    # 添加国家信息
    coutry_info = {'country': 'China'}
    # 每条记录都添加
    for item in record:
        _id = ObjectId(item.get('_id'))
        client.test.user.update_one({'_id': _id}, {'$set': coutry_info})

    # 新的记录
    new_record = {"name": "john", "sex": "male", "job": "Student"}
    new_record2 = {"name": "Tom", "job": "Hacker"}

    # 使用 upsert(update+insert), 根据条件判断有无记录，有的话就更新记录，没有的话就插入一条记录
    client.test.user.update_one({'job': 'Student'}, {'$set': new_record}, upsert=False)
    client.test.user.update_one({'job': 'Student'}, {'$set': new_record2}, upsert=True)
```

# 查找数据

```Python
def search_data():
    """ search data

    :return:
    """
    client = con_mongo()

    # 年龄大于 25 且小于 30 且不等于 29
    age_res = client.test.user.find({"age": {'$gt': 25, '$lt': 30, '$ne': 29}})
    for item in age_res:
        age = item.get('age', '')
        print "expected age info: ", age

    pattern_string1 = '^l'
    pattern_string2 = 'r$'
    regx1 = re.compile(pattern_string1, re.IGNORECASE)
    regx2 = re.compile(pattern_string2, re.IGNORECASE)
    regx_list = [regx1, regx2]

    # name 以 'l' 开头且以 'r' 结尾
    res_and = client.test.user.find({"name": {'$all': regx_list}})
    for item in res_and:
        name = item.get('name', '')
        print "name that begins with 'l' and ends with 'r' are ", name

    # name 以 'l' 开头或以 'r' 结尾
    res_or = client.test.user.find({"name": {'$in': regx_list}})
    for item in res_or:
        name = item.get('name', '')
        print "name that begins with 'l' or ends with 'r' are ", name

    # name 以 'l' 开头或以 'r' 结尾 -- 第 2 种方法
    pattern_strings = ['^l', 'r$']
    pattern_string = '|'.join(pattern_strings)
    regx = re.compile(pattern_string, re.IGNORECASE)
    res = client.test.user.find({"name": regx})

    for item in res:
        name = item.get('name', '')
        print "name that begins with 'l' or ends with 'r' are ", name
```

## 查询常用语句

- 比较运算

```Python
# 年龄大于 20
db.collection.find({"age": {'$gt': 20}})
# 年龄小于 20
db.collection.find({"age": {'$lt': 20}})
# 年龄大于等于 20
db.collection.find({"age": {'$gte': 20}})
# 年龄小于等于 20
db.collection.find({"age": {'$lte': 20}})
# 年龄大于 20 且 小于 30 且不等于 25
db.collection.find({"age": {'$gt': 20, '$lt': 30, '$ne': 25}})
```

- `$exists` 字段是否存在

```Python
# name 字段存在或不存在
db.collection.find({'name': {'$exists': True}})
db.collection.find({'name': {'$exists': False}})
```

- `$or` 查询

```Python
# 查找 a=1 或 b=2
db.collection.find({'$or': [{a: 1}, {b: 2}]})
```

- `$in` 查询

```Python
# a 属于 [1,2,3]中的任何一个
db.collection.find({a: {'$in': [1,2,3]}})
# a 不属于 [1,2,3]中的任何一个
db.collection.find({a: {'$nin': [1,2,3]}})
```

- `$all` 查询

```Python
# 全部属于
db.collection.find({a: {'$all': [1,2,3]}})
```

# Reference

1. [PyMongo 3.2.2 documentation](https://api.mongodb.org/python/current/tutorial.html)
