---
title: "命令行下载进度条"
slug: "python-cli-download-progress-bar"
date: 2018-01-22T15:36:41+08:00
tags: ['PYTHON']
comments: true
---

之前写的SciHub Spider需要有下载进度提示功能，于是就撸了发，基本上是东拼西凑大法。

```python
class ProgressBar:
    # 下载进度条
    def __init__(self, title, count=0.0, run_status=None, fin_status=None, total=100.0, unit='', sep='/',
                 chunk_size=1.0):
        super(ProgressBar, self).__init__()
        self.info = "[%s...] %s %.2f %s %s %.2f %s"
        self.title = title
        self.count = count
        self.total = total
        self.chunk_size = chunk_size
        self.status = run_status or ""
        self.fin_status = fin_status or " " * len(self.status)
        self.unit = unit
        self.sep = sep

    def __get_info(self):
        _info = self.info % (
            self.title, self.status, self.count / self.chunk_size, self.unit, self.sep,
            self.total / self.chunk_size, self.unit)
        return _info

    def refresh(self, count=1, status=None):
        self.count += count
        self.status = status or self.status
        end_str = "\r"
        if self.count >= self.total:
            end_str = "\n"
            self.status = status or self.fin_status
        print(self.__get_info(), end=end_str)
```

写个下载函数试试效果：

```python
import requests
from contextlib import closing


def download(url, name=None):
    with closing(requests.request("GET", url, stream=True, verify=False)) as response:
        chunk_size = 1024
        content_size = int(response.headers.get('content-length'))
        progress = ProgressBar(name, total=content_size, unit="KB", chunk_size=chunk_size,
                               run_status="downloading", fin_status="download completed")
        with open(name, "wb") as fh:
            for data in response.iter_content(chunk_size=chunk_size):
                fh.write(data)
                progress.refresh(count=len(data))

download("http://localhost:8000/test.rar", "test")

```

终端输出（懒得上动图了）：

```shell
C:\Users\fer_s\Anaconda3\envs\py36\python.exe D:/backup/scihub_spider/xxx.py
[test...] download completed 23968.74 KB / 23968.74 KB
```

