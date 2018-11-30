---
title: "Use multiple CPU Cores with your Linux commands"
date: "2016-07-04T18:17:00+08:00"
tags: ['OTHERS']
comments: true
---


via <http://www.rankfocus.com/use-cpu-cores-linux-commands/>

bzip2确实有速度提升, 不过别的因为磁盘IO瓶颈所以实际花费时间甚至更长, 不太好用. 不过如果是处理多个文件, 确实好用

## sed
```
sed "s/\(>gi|[0-9]*|\).*/\1/g" $fasta_file_to_index > $prefix.nt
# 并行后
cat $fasta_file_to_index | parallel -q --pipe sed 's/\(>gi|[0-9]*|\).*/\1/g' > $prefix.nt
```
