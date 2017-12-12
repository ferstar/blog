---
date = "2017-07-24T16:16:00+08:00"
title = "mongoengine 基本使用"
tags = ['PYTHON', 'MONGOENGINE']
---

> 转自 [mongoengine 基本使用](http://funhacks.net/2016/04/03/mongoengine_%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8/)

[上一篇博文](http://funhacks.net/2016/03/26/pymongo%20%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8/)介绍了 `pymongo`的基本使用，本文则介绍 [mongoengine](http://mongoengine.org/) 的基本使用，`mongoengine` 底层使用的是`pymongo` 库。

本文所使用的 `mongoengine` 版本是 0.10.6。

# 定义文档模式

与`pymongo`不同的是，使用`mongoengine`需要先定义文档模式，比如，我们定义一个`Student`的文档：

```Python
class Student(DynamicDocument):
    meta = {
        'collection': 'student',
        'strict': False
    }
    stu_id = IntField()
    age = IntField()
    name = StringField()
    gender = StringField()
```

# 基本操作

下面的代码主要介绍了 `mongoengine` 的基本操作: 插入数据，更新数据，查找数据，删除数据。

```Python
# -*- coding: utf-8 -*-
# mongoengine==0.10.6

from mongoengine import *

# 定义文档模式
class Student(DynamicDocument):
    meta = {
        'collection': 'student',
        'strict': False
    }
    stu_id = IntField()
    age = IntField()
    name = StringField()
    gender = StringField()

def insert_data():
    """ 插入数据 """
    # 一种方法
    peter = Student()
    peter.stu_id = 101
    peter.name = 'Peter'
    peter.gender = 'male'
    peter.save()

    # 另一种方法
    john = Student(stu_id=102, name="John Smith", gender='male').save()

def update_data():
    """ 更新数据 """
    # 年龄,注意用双下划线
    Student.objects(stu_id=101).update_one(set__age=23)
    Student.objects(stu_id=102).update_one(set__age=26)

    # 新增联系方式
    peter_contact = dict(phone='13238985676', email='peter@example.com')
    john_contact = dict(phone='18034567890', email='john@example.com')

    # peter
    Student.objects(stu_id=101).update_one(set__contact=peter_contact, upsert=True)
    # john
    Student.objects(stu_id=102).update_one(set__contact=john_contact, upsert=True)

def search_data():
    """ 查找数据 """
    # 查找全部
    result_all = Student.objects().all()
    print "count of all records is : ", result_all.count()

    # 查找 stu_id 为 101 的学生
    result_1 = Student.objects(stu_id=101).first()
    print "result_1.name is : ", result_1.name
    print "result_1.gender is : ", result_1.gender

    # 查找性别为男, 手机号为 18034567890, 注意用双下划线
    result_2 = Student.objects(gender='male', contact__phone='18034567890').first()
    print "result_2.name is : ", result_2.name

    # 查找年龄大于 25, 注意用双下划线
    result_3 = Student.objects(age__gt=25).all()
    for element in result_3:
        print element.name

def delete_data():
    """ 删除数据 """
    # 删除 stu_id 为 101 的联系方式, 注意用双下划线
    Student.objects(stu_id=101).update(unset__contact=1)

if __name__ == '__main__':
    # 连接数据库 'people', 没有则创建
    connect('people', host='127.0.0.1', port=27017)
    insert_data()
    update_data()
    search_data()
    delete_data()
```

## 常用查询操作符

- gt 大于，如 `Student.objects(age__gt=18)`
- gte 大于等于
- ne 不等于
- lt 小于
- lte 小于等于
- mod 取模
- not 取反，用在其他操作符前面，如 `Student.objects(age__not__mod=5)`
- in 值在列表中，如 `Blog.objects(authors__in=[peter, john])`
- nin 值不在列表中
- all 与列表的值相同，如 `Blog.objects(authors__all=[peter, john])`
- size 数组的大小
- exists 字段是否存在，如 `Student.objects(age__exists=1)`

## 高级查询

有时我们需要进行 `与查询` 和 `或查询`，也就是对多个条件进行查询，这时可以使用 [MongoEngine 的 Q 类 (Q class)](http://docs.mongoengine.org/guide/querying.html)

```Python
from mongoengine.queryset.visitor import Q

# 查找性别为男, 且手机号为 18034567890 的记录
result = Student.objects(Q(gender='male') & Q(contact__phone='18034567890'))
# 查找性别为男, 或者手机号为 18034567890 的记录
result = Student.objects(Q(gender='male') | Q(contact__phone='18034567890'))
# 查找性别为男, 且手机号为 18034567890 的记录 或者 性别为女的记录
result = Student.objects((Q(gender='male') & Q(contact__phone='18034567890')) | Q(gender='female'))
```

## 常用更新操作符

这里我们以一个 `Blog` 的文档为例，定义如下：

```Python
class Blog(Document):
    title = StringField()
    authors = ListField()
    content = StringField()
```

- `set` 设置某个值，如 `Blog.objects(id=...).update_one(set__title='my first blog')`
- `unset` 删除某个值
- `push` 将某个值添加到列表中，如 `Blog.objects(id=...).update_one(push__authors='john')`
- `push_all` 将某些值添加到列表中
- `pull` 将某个值从列表移除，如 `Blog.objects(id=...).update_one(pull__authors='john')`
- `pull_all` 将某些值从列表移除
- `add_to_set` 当某个值不在列表中的时候，将其添加到列表，如果存在则不添加，如
  `Blog.objects(id=...).update_one(add_to_set__authors='john')`

# 连接多个数据库

假设有两个数据库 `people` 和 `course`，定义如下的两个文档模式：

```Python
class Student(DynamicDocument):
    meta = {
        'db_alias': 'people-db',
        'collection': 'student',
        'strict': False
    }
    stu_id = IntField()
    age = IntField()
    name = StringField()
    gender = StringField()
```

```Python
class Math(DynamicDocument):
    meta = {
        'db_alias': 'course-db',
        'collection': 'math',
        'strict': False
    }
    math_id = IntField()
    math_name = StringField()
    teacher = StringField()
```

如果要连接这两个数据库，可以这么使用：

```Python
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    # 连接数据库 people
    register_connection('people-db', 'people')
    # 连接数据库 course
    register_connection('course-db', 'course')

    math_records = Math.objects().all()
    student_records = Student.objects().all()
```

# 参考资料

- [MongoEngine](http://docs.mongoengine.org/tutorial.html)
- [MongoEngine 查询](http://docs.mongoengine.org/guide/querying.html)