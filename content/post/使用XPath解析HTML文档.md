---
title: "使用XPath解析HTML文档"
date: "2017-07-24T17:48:00+08:00"
tags: ['XPATH', 'PYTHON', 'HTML']
comments: true
---


> 转自: [使用 XPath 解析 HTML 文档](http://funhacks.net/2016/05/08/%E4%BD%BF%E7%94%A8XPath%E8%A7%A3%E6%9E%90HTML%E6%96%87%E6%A1%A3/)

# XPath 简介

[XPath](https://www.w3.org/TR/xpath/) 的全称是 XML Path Language，即 XML 路径语言，它是一种在结构化文档（比如 XML 和 HTML 文档）中定位信息的语言，关于 XPath 的介绍可以参考 [https://www.w3.org/TR/xpath/。](https://www.w3.org/TR/xpath/%E3%80%82)

# 语法

## HTML 实例文档

后面我们将以下面的 HTML 文档介绍 XPath 的使用。

```
<html>
    <head>
        <base href='http://example.com/' />
        <title>Example website</title>
    </head>
    <body>
        <div id='images'>
            <a href='image1.html'>Name: My image 1 <br/><img src='image1_thumb.jpg'/></a>
            <a href='image2.html'>Name: My image 2 <br/><img src='image2_thumb.jpg'/></a>
            <a href='image3.html'>Name: My image 3 <br/><img src='image3_thumb.jpg'/></a>
            <a href='image4.html'>Name: My image 4 <br/><img src='image4_thumb.jpg'/></a>
            <a>Name: My image 5 <br/><img src='image5_thumb.jpg'/></a>
        </div>
    </body>
</html>
```

## 选取节点

下表是 XPath 常用的语法，实例对应的是上面的 HTML 文档。

| 表达式      | 描述              | 实例                       | 结果                                 |
| -------- | --------------- | ------------------------ | ---------------------------------- |
| nodename | 选取此节点的所有子节点     | body                     | 选取 body 元素的所有子节点                   |
| /        | 从根节点选取          | /html                    | 选取根元素 html                         |
| //       | 匹配选择的当前节点，不考虑位置 | //img                    | 选取所有 img 元素，而不管它们在文档的位置            |
| .        | 选取当前节点          | ./img                    | 选取当前节点下的 img 节点                    |
| ..       | 选取当前节点的父节点      | ../img                   | 选取当前节点的父节点下的 title                 |
| @        | 选取属性            | //a[@href=”image1.html”] | 选取所有 href 属性为 “image1.html” 的 a 节点 |
|          |                 | //a/@href                | 获取所有 a 节点的 href 属性的值               |

## 谓语

> 谓语用来查找某个特定的节点或者包含某个指定的值的节点，谓语嵌在方括号中。

| 路径表达式                    | 结果                                  |
| ------------------------ | ----------------------------------- |
| //body//a[1]             | 选取属于 body 子元素的第一个 a 元素              |
| //body//a[last()]        | 选取属于 body 子元素的最好一个 a 元素             |
| //a[@href]               | 选取所有拥有名为 href 的属性的 a 元素             |
| //a[@href=’image2.html’] | 选取所有 href 属性等于 “image2.html” 的 a 元素 |

# 在 Python 中使用

在 `python` 中使用 `XPath` 需要安装相应的库，这里推荐使用 [lxml](http://lxml.de/) 库。

代码示例：

```
# -*- coding: utf-8 -*-

from lxml import etree

html = """
<html>
    <head>
        <base href='http://example.com/' />
        <title>Example website</title>
    </head>
    <body>
        <div id='images'>
            <a href='image1.html'>Name: My image 1 <br/><img src='image1_thumb.jpg'/></a>
            <a href='image2.html'>Name: My image 2 <br/><img src='image2_thumb.jpg'/></a>
            <a href='image3.html'>Name: My image 3 <br/><img src='image3_thumb.jpg'/></a>
            <a href='image4.html'>Name: My image 4 <br/><img src='image4_thumb.jpg'/></a>
            <a>Name: My image 5 <br/><img src='image5_thumb.jpg'/></a>
        </div>
    </body>
</html>
"""

page_source = etree.HTML(html.decode('utf-8'))

title = page_source.xpath("//title/text()")
all_href = page_source.xpath("//a/@href")
a_image1_text = page_source.xpath("//body//a[1]/text()")
a_image1_src = page_source.xpath("//a[@href='image1.html']/img/@src")
a_image3_href = page_source.xpath("//a[contains(@href, '3')]/@href")
a_last = page_source.xpath("//body//a[last()]/img/@src")
all_img_src = page_source.xpath("//img/@src")

print "Title", title
print "all href", all_href
print "a_image1_text", a_image1_text
print "a_image1_src", a_image1_src
print 'a_image3_href', a_image3_href
print "a_last", a_last
print "all_img_src", all_img_src
```

输出结果如下：

```
Title ['Example website']
all href ['image1.html', 'image2.html', 'image3.html', 'image4.html']
a_image1_text ['Name: My image 1 ']
a_image1_src ['image1_thumb.jpg']
a_image3_href ['image3.html']
a_last ['image5_thumb.jpg']
all_img_src ['image1_thumb.jpg', 'image2_thumb.jpg', 'image3_thumb.jpg', 'image4_thumb.jpg', 'image5_thumb.jpg']
```

要注意的是，如果 xpath() 找到了匹配的数据，返回的结果是一个数组，不管是一个还是多个，比如结果中的 `Title`。

# 参考资料

- [XML Path Language (XPath)](https://www.w3.org/TR/xpath/)
- [lxml - Processing XML and HTML with Python](http://lxml.de/)
- [XPath 语法](http://www.w3school.com.cn/xpath/xpath_syntax.asp)
- [XPath、XQuery 以及 XSLT 函数](http://www.w3school.com.cn/xpath/xpath_functions.asp)
- [xpath提取HTML // Astray Linux](http://astraylinux.com/2014/08/21/server-xpath-pick-html/)
- [选择器(Selectors) — Scrapy 1.0.5 文档](http://scrapy-chs.readthedocs.io/zh_CN/1.0/topics/selectors.html)