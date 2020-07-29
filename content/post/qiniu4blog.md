---
title: "使用七牛云存储创建自己的图床,用于写博客"
date: "2015-11-16T23:16:33+08:00"
tags: ['OTHERS']
comments: true
---


如题，静态博客图片等多媒体资源需要有个窝，目前在用七牛，看到有人写了`qiniu4blog`，蛮好用的，拿来小改了下，以适应个人需求

- fork from：
[https://github.com/bluesky4485/qiniu4blog](https://github.com/bluesky4485/qiniu4blog) 

- source：
[https://github.com/wzyuliyang/qiniu4blog](https://github.com/wzyuliyang/qiniu4blog) 

- modified：
[https://github.com/ferstar/qiniu4blog](https://github.com/ferstar/qiniu4blog) 

## 使用流程

1. 启动脚本监控指定文件夹
`qiniu4blog`
> 配置文件`qiniu.cfg`放在～目录下，注意监控目录路径需要指明绝对路径，自定义地址后面不要漏`/`

2. 使用任意截图工具将截图保存到指定监控目录

3. 剪贴板即可生成图片地址
![DeepinScrot-2442.png](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/png/2015/11/8b265710971e64014657a9788f0b99dc.png)
