---
title: "以openpyxl为例, 不要太信任你所使用的库"
date: "2022-03-16T22:41:01+08:00"
tags: ['Python', 'TODO']
comments: true
---

> 最近在使用`openpyxl`时踩了个小坑: 遍历 Excel 时`openpyxl`可能会由于对行数的误判而提前终止

测试 Excel: [sample.xlsx](https://github.com/ferstar/blog/files/8274837/sample.xlsx) 这个 Excel 实际只有 10 行

代码(分别使用了`openpyxl/pylightxl/xlrd`来计算示例文件的行数): 

```python
import openpyxl
import pylightxl
import xlrd


def openpyxl_count(path):
    """
    Counts the number of rows in an Excel file with openpyxl.
    """
    wb = openpyxl.load_workbook(path)
    sheet = wb.active
    return sheet.max_row


def pylightxl_count(path):
    """
    Counts the number of rows in an Excel file with pylightxl.
    """
    db = pylightxl.readxl(path)
    ws = db.ws(db.ws_names[0])
    return ws.maxrow


def xlrd_count(path):
    """
    Counts the number of rows in an Excel file with xlrd.
    """
    wb = xlrd.open_workbook(path)
    sheet = wb.sheet_by_index(0)
    return sheet.nrows


if __name__ == '__main__':
    excel_path = 'sample.xlsx'
    print(openpyxl_count(excel_path))
    print(pylightxl_count(excel_path))
    print(xlrd_count(excel_path))
```

结果很奇怪, `openpyxl`得出`14`行的结论, 其他两个工具结论正确`10`, 实际上使用 MS office 打开也确实显示只有`10`行

哪里出问题了呢? 我拆开这个文档, 查了下`xml`文件, 发现后四行确实是存在的, 只不过没有内容

也就是说从视觉上看`openpyxl`是错的, 但从真实数据上看他又是对的

甲方客户可不管真实底层数据的情况, 他只关心他给你了 N 行数据, 结果你给人整了 M 行, 此为坑也

排坑无非两个方案: 要么换库, 要么把源文件改造一下

我选改造源文件, 即遍历 Excel 前先把`xml`中隐藏的空值行全干掉, 这样就欧了, 同时也提了个 issue 给`openpyxl`项目: https://foss.heptapod.net/openpyxl/openpyxl/-/issues/1806



```
# NOTE: I am not responsible for any expired content.
create@2022-03-16T22:41:01+08:00
update@2022-03-16T22:43:59+08:00
comment@https://github.com/ferstar/blog/issues/55
```
