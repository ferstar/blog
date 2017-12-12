---
title: "fix surpi on biolinux8"
date: "2016-06-13T15:50:00+08:00"
tags: ['OTHERS']
comments: true
---


原有的部署脚本年久失修, 所以花了点时间修复下:
- pipeline: 
surpi <https://github.com/ferstar/surpi>
- what I have done: 
<https://github.com/ferstar/surpi/commit/af6c8a830cb55444e82d973946c74548bef89c0f>
- addition

1. SRA Toolkit
<http://www.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=software>
2. aspera connect
A small test by using ascp
```
ascp -T -i /home/ferstar/.aspera/connect/etc/asperaweb_id_dsa.openssh --host ftp-private.ncbi.nlm.nih.gov --user anonftp --mode recv /1GB ./
1GB                                           100% 1025MB  6.9Mb/s    08:18    
Completed: 1049600K bytes transferred in 499 seconds
 (17226K bits/sec), in 1 file.
 ```
 much more faster than traditional download tools such as curl and wget