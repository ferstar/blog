+++
date = "2016-12-06T17:02:00+08:00"
title = "利用python-docx更新word中的表格内容"
tags = ['PYTHON', 'WORD']

+++

收到实验组小妹妹一个需求, 希望把一个巨大word文档中所有表格里的所有一位小数随机添加一位数变成两位小数, 从学术角度我开始是拒绝的, 但是, 妹子需求哪有不满足的道理, so...

记录下我解决这个问题的流程:
1. 听取妹子需求, 然后大概评估这个活应该可以用`Python`来做
2. 需求准确归纳: 给所有文档中表格内一位小数后加一位随机数使之变成两位小数
3. 商量一个deadline: 因为没做过, 不能打包票, 所以暂定第二天上班给结果
4. 拿到原始数据开始找轮子撸
5. Google 找到 python-docx 这个 package 可以做这件事
6. 问题分解
- 解析 docx
- 遍历所有表格
    - 正则匹配一位小数
    - 生成随机小数补位
    - 保存
7. 交给妹子, 收获膝盖

## 放码

> 找到靠谱轮子就是爽, 几行代码解决战斗, 十分钟完成任务
```python
import random
import re

from docx import Document
# 源文件 test.docx
doc = Document("test.docx")
# 正则匹配所有一位小数
p = re.compile("^[0-9]+\.[0-9]{1}$")
# 遍历所有表格
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            if re.search(p, cell.text):
                # 匹配小数并在后面补齐一位小数
                cell.text += str(random.randint(0, 9))

doc.save("test_update.docx")
```