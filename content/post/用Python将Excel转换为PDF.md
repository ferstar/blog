---
date = "2016-12-20T17:01:00+08:00"
title = "用Python将Excel转换为PDF"
tags = ['PYTHON', 'PDF', 'EXCEL']

---

有一堆Excel需要转成PDF, 所以启动 copy from stackoverflow 大法

via <http://stackoverflow.com/questions/20854840/xlsx-and-xlslatest-versions-to-pdf-using-python>

```python
from win32com import client
xlApp = client.Dispatch("Excel.Application")
books = xlApp.Workbooks.Open('C:\\excel\\trial.xls')
ws = books.Worksheets[0]
ws.Visible = 1
ws.ExportAsFixedFormat(0, 'C:\\excel\\trial.pdf')
```

把上段东东塞到一个函数里, 然后用`os.walk`遍历`*.xlsx`, 另外也可以加上`multiprocessing.dummy`跑多线程装装逼, 哈哈