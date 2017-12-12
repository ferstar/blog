---
date = "2015-09-22T20:54:00+08:00"
title = "RFID数据分析"
tags = ['OTHERS']

---

`log`文件内容类似
```
-12,788
-11,889
-12,788
-12,788
-12,788
```
脚本作用: 把`log`文件内数据拆分成两列输出到`excel`中供数据分析
```python
#!/usr/bin/env python3

import sys
import re
import xlwt

def split_on_separators(original, separators):
    # 这个是用正则实现的，可能不满足要求
    # return filter(lambda x:x.strip(), re.split(r"[%s]" % separators, original))
     
    result = [original]
    for sep in separators:
        temp = []
        for r in result:
            temp.extend(filter(lambda x:x.strip(), r.split(sep)))
        result = temp
    return result

def change_data_type(file, pattern, list):
    # 转换数据类型, 并交换时间和信号强度位置
    try:
        pf_file = open(file, 'r')
    except Exception as e:
        print('%s not found!' %file)
        sys.exit(1)
    for file_line in pf_file.readlines():
        file_result = split_on_separators(file_line, pattern)
        if file_result is not None:
            time = int(file_result[1])
            rssi = int(file_result[0])
            my_list = []
            my_list.append(time)
            my_list.append(rssi)
            list.append(my_list)

    return list

def print_into_excel(list, excel, file_name):
    wb = xlwt.Workbook()
    ws = wb.add_sheet("ferstar")

    heading_xf = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
    rowx = 0
    ws.set_panes_frozen(True)
    ws.set_horz_split_pos(rowx+1)
    ws.set_remove_splits(True)
    for i, row in enumerate(list):
        for j, col in enumerate(row):
            ws.write(i, j, col)
    #ws.col(0).width = 256 * max([len(row[0]) for row in list])
    wb.save(excel)


log_file = 'log'
total_list  = []
string_pattern = ",\n"
excel_file = log_file + '.xls'
data = change_data_type(log_file, string_pattern, total_list)
print_into_excel(data, excel_file, log_file)

```