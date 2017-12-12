---
title: "从Bitcron迁移到Hugo"
date: 2017-12-12T17:08:07+08:00
tags: ['PYTHON', 'HUGO']
comments: true
---

跟随老大的[脚步](https://tech.crandom.com/post/2017/switch-to-hugo/)，拥抱hugo，拥抱CI。原来的水文都是在Bitcron写的，文件头信息格式不太一样，于是写脚本转换了下。

```python
import os
import sys
from chardet.universaldetector import UniversalDetector

if len(sys.argv) != 3:
    sys.exit("Usage: {} source_dir dest_dir".format(sys.argv[0]))

src_dir = sys.argv[1]
new_dir = sys.argv[2]

if not os.path.exists(new_dir):
    os.mkdir(new_dir)


def detect(fp):
    detector = UniversalDetector()
    with open(fp, 'rb') as fh:
        for line in fh:
            detector.feed(line)
            if detector.done: break
    detector.close()
    return detector.result['encoding']


def get_files(dp):
    for root, dirs, files in os.walk(dp):
        return map(lambda x: os.path.join(root, x), files)


def convert_article(fp):
    file_name = os.path.basename(fp).split('.')[:-1][0]
    new_fp = os.path.join(new_dir, file_name) + ".md"
    encoding = detect(fp)
    tags_line = ''
    status = 'draft'
    with open(fp, 'r', encoding=encoding) as fh:
        # hexo header metadata
        while True:
            line = fh.readline()
            if line.startswith("---"):
                break
        while True:
            line = fh.readline()
            if line.startswith("---"):
                break
            if line.startswith("date"):
                _date = 'T'.join(line.strip().split(" ")[1:])
                if len(_date) == 16:
                    date_line = _date + ':00+08:00'
                else:
                    date_line = _date + '+08:00'
            if line.startswith("title"):
                title_line = line.strip().replace("'", "").replace('"', '').split(':')[-1].strip()
                if title_line.startswith('"'):
                    title_line = title_line.replace('"', '')
            if line.startswith('status'):
                status = line.strip().split(' ')[-1]
            if line.startswith('tags'):
                tags_line = str(line.strip().replace("'", "").replace(' ', '').split(':')[-1].split(',')).upper()
        if status == 'draft':
            return
        with open(new_fp, 'w', encoding='utf-8') as out:
            # bitcron header metadata
            out.write("---\n")
            out.write('title: "{}"\n'.format(title_line))
            out.write('date: "{}"\n'.format(date_line))
            if tags_line:
                out.write('tags: {}\n'.format(tags_line))
            else:
                out.write("tags: ['OTHERS']\n")
            out.write("comments: true\n")
            out.write("---\n\n")
            # copy the rest lines
            while 1:
                line = fh.readline()
                if not line:
                    break
                out.write(line)


list(map(convert_article, get_files(src_dir)))

```