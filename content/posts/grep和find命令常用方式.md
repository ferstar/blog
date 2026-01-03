---
title: "grep和find命令常用方式"
slug: "grep-find"
date: "2015-11-16T23:04:43+08:00"
tags: ['LINUX', 'SHELL']
comments: true
---

find和grep的使用权限是**所有用户**

## find命令的作用是在目录中根据文件名搜索文件

find 列出当前目录及其子目录的所有文件和文件夹的完整路径。
find -name Help.java 在当前目录及其子目录中搜索文件名为Help.java的文件。
find . -name Help.java 在当前目录及其子目录中搜索文件名为Help.java的文件(同上)。
find / -name Help.java 在整个硬盘中搜索文件名为Help.java的文件。
find -perm 755 在当前目录及其子目录中查找指定权限的文件
find -type b 在当前目录及其子目录下查找块设备文件。
find -type d 在当前目录及其子目录下查文件夹。
find -type c 在当前目录及其子目录下查找字符设备文件。
find -type p 在当前目录及其子目录下查找管道文件。
find -type l 在当前目录及其子目录下查找符号链接文件。
find -type f 在当前目录及其子目录下查找普通文件。
find -type d -exec ls -l {} \; 查找当前目录及其子目录下的文件夹，并将查找结果以ls -l的方式展现。
find -type d -ok rm -rf {} \;查找当前目录及其子目录下的文件夹，并将查找结果依次执行rm -rf命令，但是在执行命令前会有确认提示。

## grep命令的作用是在目录中根据文件内容搜索文件

grep Clock * 查找当前目录下的所有文件中包含Clock字符串的文件，不查找子目录
grep -r Clock * 查找当前目录下的所有文件中包含Clock字符串的文件，查找子目录
grep -nr Clock * 查找当前目录下的所有文件中包含Clock字符串的文件，查找子目录，并显示行号
