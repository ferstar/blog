---
title: "_csv.Error: field larger than field limit (131072)"
slug: "csv-field-larger-than-field-limit"
date: "2019-12-16T23:17:00+08:00"
tags: ['PYTHON']
comments: true
---

数据库部分翻车, 写了点脚本搞恢复

导出脚本大概长这样

```python
def temp_dump_answer():
    """
    导出部分数据
    """

    def write(data):
        with gzip.open('dump_answer.csv.gz', 'wt', newline='') as file_obj:
            writer = csv.writer(file_obj)
            for key, value in data.items():
                writer.writerow([key, json.dumps(value)])

    def export(conn):
      ...我是导出...
      write(data)
```

恢复的脚本免不了要`read`一下这个csv文件

```python
  def restore():
      with gzip.open('dump_answer.csv.gz', 'rt', newline='') as file_obj:
          for qid, ans in csv.reader(file_obj):
              pass
```

一顿骚操作, 报错如题, 于是放狗, 解决~

```shell
# fix "_csv.Error: field larger than field limit (131072)"
# via https://stackoverflow.com/a/15063941
csv.field_size_limit(sys.maxsize)
```
