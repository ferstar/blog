---
date = "2016-01-24T21:50:20+08:00"
title = "Simiki-个人 wiki 搭建记录"
tags = ['LINUX', 'SHELL', 'WIKI']
---

## Simiki

> A simple wiki framework

官方的 [Quick Start](http://simiki.org/quickstart.html) 
也有中文文档 [http://simiki.org/zh-docs/](http://simiki.org/zh-docs/) 

本来想在 Windows 系统上折腾，不过作者并不建议，而且我尝试后发觉实在好多坑，所以转向 Ubuntu 系统

我用的是 Python 3.4.3，以下是大致操作记录

- 安装 simiki `sudo pip3 install simiki`

- 安装 ghp-import  `sudo pip3 install ghp-import`

- 安装 fabric3 `sudo pip3 install fabric3`
> 不要用 fabric，并不支持 Python 3.x

- Github 新建一个`repository`，假设名字叫 wiki

- 新建`master`、`gh-pages`两分支

- `clone`项目到本地目录，如 wiki

- 初始化 `cd wiki && simiki init`

- 新建`output`目录 `mkdir output`

- 域名绑定 新建`CNAME`文件，内容为域名地址如：wiki.ferstar.org

- Generate `simiki g`

- Preview `simiki p`

- 发布内容到 Github `fab cd`
> 用我修改后的 [fabfile.py](https://github.com/ferstar/wiki/blob/master/fabfile.py) 替换原有才可以用上面的发布命令。
> 此指令作用类似`hexo d -g`，将生成的静态页面内容推送到 Github Pages 分支`gh-pages`，源文件配置等推送到 `master`分支，以作备份。