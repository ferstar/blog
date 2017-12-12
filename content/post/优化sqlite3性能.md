---
date = "2016-06-18T08:45:00+08:00"
title = "优化sqlite3数据插入性能"
tags = ['OTHERS']

---

需要序列化个略大的文本文件到数据库
关键的几个点
- 用executemany代替execute
- 开启此参数 PRAGMA synchronous = OFF
- 放垃圾码
```
import os
import sqlite3
import time


def exeTime(func):
    def newFunc(*args, **args2):
        t0 = time.time()
        print "@%s, {%s} start" % (time.strftime("%X", time.localtime()), func.__name__)
        back = func(*args, **args2)
        print "@%s, {%s} end" % (time.strftime("%X", time.localtime()), func.__name__)
        print "@%.3fs taken for {%s}" % (time.time() - t0, func.__name__)
        return back

    return newFunc


@exeTime
def func():
    # Create names_nodes_scientific.db
    print ("Creating names_nodes_scientific.db...")
    conn = sqlite3.connect('names_nodes_scientific.db')
    c = conn.cursor()
    c.execute("CREATE TABLE names (taxid INTEGER PRIMARY KEY, name TEXT)")
    c.execute("PRAGMA synchronous = OFF")
    c.execute("BEGIN TRANSACTION")
    with open('test.dmp', 'r') as map_file:
        lst = []
        for line in map_file:
            line = line.split("|")
            taxid = line[0].strip()
            name = line[1].strip()
            lst.append((taxid, name))
    c.executemany("INSERT INTO names VALUES (?,?)", lst)
    conn.commit()
    conn.close()


class Main(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    os.remove("names_nodes_scientific.db")
    func()
```
截取80兆左右的文件做测试, 测试结果比优化前时间缩短了一半(12s降低到5.48s), 下一步考虑利用linux tmpfs的特性