---
title: "把指定目录下所有源码汇集到一个md文件的脚本"
date: "2015-09-04T22:22:15+08:00"
tags: ['PYTHON', 'LINUX']
comments: 
---

一个用来把指定目录下所有文本文件内容汇集到一个md文件的python脚本

```
import os
import os.path


rootdir = '/the_path_to_your_src'

for parent, dirnames, filenames in os.walk(rootdir):
    for filename in filenames:
        peer_path = os.path.join(parent,filename)
        with open(peer_path, "r") as src:
        	data = src.read()
        with open("out.md", "a+") as out
            out.write("# " + peer_path)
            out.write("\n\n```\n")
            out.write(data)
            out.write("\n```\n")

```

效果图![我是图](http://7xivdp.com1.z0.glb.clouddn.com/blog/image/2015-09-04%2023%3A03%3A58.png/xyz) 

代码审核时可能会用到:-)
