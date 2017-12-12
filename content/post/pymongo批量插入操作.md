---
title: "pymongo批量插入操作"
date: "2017-07-17T15:07:00+08:00"
tags: ['PYTHON', 'MONGODB', 'BIO']
comments: true
---


向数据库新增大量数据是经常性的需求, pymongo 支持 [insert_many](http://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.insert_many). 然而主键是我们自定义的, 并非默认"_id", 这样批量插入, 并且实现更新记录的目的就有点困难.

> insert_many用法
>
> ```shell
> insert_many(documents, ordered=True, bypass_document_validation=False)
> ```

这个方法只能用来插入集合中不存在的记录, 并不会对已有的数据进行更新, 如果插入重复数据, 便会报错

搜索一番后发现万能的sf早有解决方法, 使用[Bulk Operations API](http://api.mongodb.org/python/current/api/pymongo/bulk.html) 

[Is there a way to skip over existing _id's for insert_many in Pymongo 3.0?](https://stackoverflow.com/questions/31375606/is-there-a-way-to-skip-over-existing-ids-for-insert-many-in-pymongo-3-0)

具体解决方法如下:

*源答案并不能在主键存在的情况下对数据进行更新*

```python
def insert_many(collection, docs=None, update=True):
    if not docs:
        return
    # $set 的时候, 会更新数据, setOnInsert只插入不更新
    update_key = "$set" if update else "$setOnInsert"
    bulk = pymongo.bulk.BulkOperationBuilder(collection, ordered=False)
    for i in docs:
        if i.get(index_name):
            bulk.find({index_name: i[index_name]}).upsert().update_one({update_key: i})
        else:
            bulk.insert(i)
    result = bulk.execute()
    return result
	modify_count = result.get("nModified")  # 更新条目数
    insert_count = result.get("nUpserted") + result.get("nInserted")  # 总插入条数
```

另有一方法是[pymongo.collection.Collection.bulk_write](http://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.bulk_write)