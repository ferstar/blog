---
title: "HEXO文章迁移到Bitcron"
date: "2017-07-03T18:32:00+08:00"
tags: ['HEXO', 'BITCRON', 'LINUX', 'WINDOWS', 'PYTHON']
comments: 
---


前半年都没怎么搭理HEXO博客，升级主题以后居然升挂了，刚好收到Farbox迁移到Bitcron的邮件通知，就打算直接把HEXO写的一些东东迁移过来，文章维护一份放在Dropbox里面就可以。
HEXO文章头几行跟Bitcron略有不同，我简单粗暴只保留 title 和 date 信息， 所以处理很简单，写个 Python 脚本就可以啦，下面是具体转换步骤

## 先统一转一下格式，避免编码问题

> 有时候在win写有时候又在Linux写，所以这些文章的编码有可能是gbk，也有可能是utf-8，懒得一个个看，直接上`dos2unix`这个小工具批量转

```shell
# HEXO文章都在_posts文件夹内
for i in $(ls _posts/*); do dos2unix -k -o ${i}; done
```

## 比较文章结构，写脚本批量转换之

hexo2bitcron.py

```python
import os
import sys

if len(sys.argv) != 3:
    sys.exit("Usage: {} source_dir dest_dir".format(sys.argv[0]))

src_dir = sys.argv[1]
new_dir = sys.argv[2]

if not os.path.exists(new_dir):
    os.mkdir(new_dir)


def get_files(dp):
    for root, dirs, files in os.walk(dp):
        return map(lambda x: os.path.join(root, x), files)


def convert_article(fp):
    new_fp = "/".join([new_dir, fp.split("/")[-1]])
    with open(fp, 'r') as fh, open(new_fp, 'w') as out:
        # hexo header metadata
        while 1:
            line = fh.readline()
            if line.startswith("---"):
                break
            if line.startswith("title"):
                title_line = line
            if line.startswith("date"):
                date_line = line
        # bitcron header metadata
        out.write("---\n")
        out.write(date_line)
        out.write("status: public\n")
        out.write(title_line)
        out.write("---\n")
        # copy the rest lines
        while 1:
            line = fh.readline()
            if not line:
                break
            out.write(line)


list(map(convert_article, get_files(src_dir)))
```

用法：`python hexo2bitcron.py _posts bitcron`

> 脚本在CentOS上测试通过:-)