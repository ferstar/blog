---
title: "让python的json.dumps输出中文"
date: "2015-09-18T09:54:00+08:00"
tags: ['OTHERS']
comments: true
---


python的json.dumps方法默认会输出成这种格式
`"\u535a\u5ba2\u56ed"`
要输出中文需要指定ensure_ascii参数为False，如下代码片段：
`json.dumps({'text':"中文"},ensure_ascii=False,indent=2)`