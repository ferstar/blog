---
date = "2016-12-20T16:36:00+08:00"
title = "用 openpyxl 处理 xlsx 文件"
tags = ['OTHERS']
---

`openpyxl` 是一个用来处理 excel 文件的 python 代码库, 安装什么略过不提, 只说一个简单操作的例子

1. 例子

   有这么一个表

   | 高压/低压(实验组) | 高压/低压(对照组) |
   | ---------- | ---------- |
   | 156/99     | 110/70     |
   | 124/83     | 119/71     |
   | 103/78     | 100/60     |
   | 150/100    | 114/78     |
   | 150/100    | 109/74     |
   | 100/76     | 112/65     |
   | 130/90     | 130/77     |
   | 174/105    | 121/72     |
   | 109/85     | 129/84     |
   | 140/100    | 128/80     |
   |            | 120/80     |
   |            | 122/73     |
   |            | 120/70     |
   |            | 107/80     |
   |            | 110/70     |
   |            | 115/73     |
   |            | 110/61     |
   |            | 127/80     |
   |            | 110/70     |
   |            | 108/79     |
   |            | 114/78     |
   |            | 118/71     |

   需要把高压低压分开两列来整, 手动写要累死狗, 上万的数据, 于是祭出Python大法

2. 烂码

```python
import re

import openpyxl

file = "工作簿2.xlsx"
wb = openpyxl.load_workbook(file)
ws = wb.get_sheet_by_name("Sheet1")

rows = ws.max_row
cols = ws.max_column

p = re.compile("[0-9]+/[0-9]+")

for row in range(1, rows + 1):
    i = 0
    for col in range(1, cols + 1):
        v = str(ws.cell(row=row, column=col).value)
        if re.search(p, v):
            lst = v.split("/")
            ws.cell(row=row, column=col + i + cols).value = int(lst[0])
            i += 1
            ws.cell(row=row, column=col + i + cols).value = int(lst[1])
        else:
            i += 1

ws = wb.get_sheet_by_name("Sheet2")

for row in range(1, rows + 1):
    i = 0
    for col in range(1, cols + 1):
        v = str(ws.cell(row=row, column=col).value)
        if re.search(p, v):
            lst = v.split("/")
            ws.cell(row=row, column=col + i + cols).value = int(lst[0])
            i += 1
            ws.cell(row=row, column=col + i + cols).value = int(lst[1])
        elif re.search(re.compile("[0-9+/.+]"), v):
            lst = v.split("/")
            # print(lst)
            ws.cell(row=row, column=col + i + cols).value = int(lst[0])
            i += 1
            ws.cell(row=row, column=col + i + cols).value = lst[1]
        elif v == "未记录":
            ws.cell(row=row, column=col + i + cols).value = "未记录"
            i += 1
            ws.cell(row=row, column=col + i + cols).value = "未记录"
        else:
            i += 1

wb.save("test.xlsx")

```

享受生活即可

结果长这样

| 高压/低压(实验组) | 高压/低压(对照组) | 高压(实验) | 低压(实验) | 高压(对照) | 低压(对照) |
| ---------- | ---------- | ------ | ------ | ------ | ------ |
| 156/99     | 110/70     | 156    | 99     | 110    | 70     |
| 124/83     | 119/71     | 124    | 83     | 119    | 71     |
| 103/78     | 100/60     | 103    | 78     | 100    | 60     |
| 150/100    | 114/78     | 150    | 100    | 114    | 78     |
| 150/100    | 109/74     | 150    | 100    | 109    | 74     |
| 100/76     | 112/65     | 100    | 76     | 112    | 65     |
| 130/90     | 130/77     | 130    | 90     | 130    | 77     |
| 174/105    | 121/72     | 174    | 105    | 121    | 72     |
| 109/85     | 129/84     | 109    | 85     | 129    | 84     |
| 140/100    | 128/80     | 140    | 100    | 128    | 80     |
|            | 120/80     |        |        | 120    | 80     |
|            | 122/73     |        |        | 122    | 73     |
|            | 120/70     |        |        | 120    | 70     |
|            | 107/80     |        |        | 107    | 80     |
|            | 110/70     |        |        | 110    | 70     |
|            | 115/73     |        |        | 115    | 73     |
|            | 110/61     |        |        | 110    | 61     |
|            | 127/80     |        |        | 127    | 80     |
|            | 110/70     |        |        | 110    | 70     |

