+++
date = "2015-09-24T22:30:28+08:00"
title = "python数据分析"
tags = ['OTHERS']

+++
直接放码：
> 现在可以只执行一次就可以把`text`目录下所有符合条件的文件数据格式化输出到`excel`里面，不符合的文件会有提示，程序并不会中断

<!--more-->

```python
#!/usr/bin/env python3

import os
import os.path
import sys
import re
import xlwt

def get_file_list(root_dir):
    # 获得指定目录下所有文件路径，返回一个包含路径集合的列表
    file_list = []
    for parent, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            peer_path = os.path.join(parent,filename)
            file_list.append(peer_path)
    return file_list

def split_on_separators(original, separators):
    # 以特定字符为标记，分隔已知字符串为列表
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
    # 格式化数据类型
    try:
        with open(file, 'r') as pf_file:
            line_result = pf_file.readline()
            column = split_on_separators(line_result, pattern)
    except Exception as e:
        print('%s not found!' %file)
        sys.exit(1)
    
    # print(column, type(column), len(column))
    with open(file, 'r') as pf_file:
        if len(column) == 4:
            time0 = float(column[0])
            for file_line in pf_file.readlines():
                file_result = split_on_separators(file_line, pattern)
                time = float(file_result[0]) - time0
                rssi = 0 - int(file_result[1])
                count = int(file_result[2])
                epc = int(file_result[3][-2:])
                my_list = []
                my_list.append(time)
                my_list.append(rssi)
                my_list.append(count)
                my_list.append(epc)
                list.append(my_list)
                    
        elif len(column) == 3:
            for file_line in pf_file.readlines():
                file_result = split_on_separators(file_line, pattern)
                rssi = 0 - int(file_result[0])
                count = int(file_result[1])
                epc = int(file_result[2][-2:])
                my_list = []
                my_list.append(rssi)
                my_list.append(count)
                my_list.append(epc)
                list.append(my_list)
        
        elif len(column) == 2:
            for file_line in pf_file.readlines():
                file_result = split_on_separators(file_line, pattern)
                rssi = 0 - int(file_result[0])
                count = int(file_result[1])
                my_list = []
                my_list.append(rssi)
                my_list.append(count)
                list.append(my_list)
        else:
            print('我不认识这个文件：%s！' %file)
            # list = []
            # sys.exit(1)
        
    return list

def print_into_excel(list, excel):
    # 将处理后的数据写入excel中，行列自适应
    if list != []:
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

def loop_files(rootdir, string_pattern):
    # 遍历指定目录下所有文件数据，输出excel到上级目录中
    log_files = get_file_list(rootdir)
    for log_file in log_files:
        total_list  = []
        excel_file = split_on_separators(log_file, "/.")[1] + '.xls'
        data = change_data_type(log_file, string_pattern, total_list)
        # print(excel_file, log_file)
        print_into_excel(data, excel_file)
        
if __name__ == "__main__":
    path = 'text'
    pattern = '-,\n'
    try:
        loop_files(path, pattern)
    except Exception as e:
        print('oops, error happened!')
        sys.exit(1)
```