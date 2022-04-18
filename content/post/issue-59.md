---
title: "一个简单计算PDF页数的方法"
date: "2022-04-08T02:51:14+08:00"
tags: ['Python', 'Snippet']
comments: true
---

> 还是老老实实用现成的轮子吧

```python
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import resolve1


def count_pdf_pages(data: bytes) -> int:
    """
    :param data: pdf data
    :return: page count
    """
    parser = PDFParser(BytesIO(data))
    doc = PDFDocument(parser)
    parser.set_document(doc)
    pages = resolve1(doc.catalog['Pages'])
    return pages.get('Count', 0)
```

> 翻车了, 下面的代码仅适用于 PDF1.4 及以下版本

```python
import re


def count_pages(path):
    count_pages_p = re.compile(rb"/Type\s*/Page([^s]|$)", re.MULTILINE | re.DOTALL)
    with open(path, 'rb') as fp:
        return len(count_pages_p.findall(fp.read()))
```



```
# NOTE: I am not responsible for any expired content.
create@2022-04-08T02:51:14+08:00
update@2022-04-18T11:41:56+08:00
comment@https://github.com/ferstar/blog/issues/59
```
