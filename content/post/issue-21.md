---
title: "记一次迁移postgresql数据库的过程"
date: "2020-05-21T02:15:07+08:00"
tags: ['Linux', 'PostgreSQL']
comments: false
---

> created_date: 2020-05-21T02:15:07+08:00

> update_date: 2020-05-21T02:15:28+08:00

> comment_url: https://github.com/ferstar/blog/issues/21

主要照抄这个gist https://gist.github.com/brock/7a7a70300096632cec30

以往小数据直接scp大法走起就可以，但是这次比较大，裸SQL大概有30GB，gzip压完都有3.6GB，现有网络环境下，scp传不了多少就异常关闭，就算不关闭，因为是跨区域机房迁移，速度也是非常龟速，所以选择了一个有cdn加持的[临时文件中转服务](https://app.tmp.link)来迁移，实际效果也是非常棒，Local 机器上传基本跑满带宽，Remote 机器下载能稳定维持在5MB/s，一次成功，共耗时半小时左右。

1. Local 导出`直接压成gzip，能节省巨量的存储空间`

    `pg_dump -d <db_name> -p <port> -U <db_user> -Z9 -f <dump_file.sql.gz>`

2. 加密`因为要通过中转服务传输`

    `zip -e -1 <dump_file.sql.gz.zip> <dump_file.sql.gz>`

3. md5sum

    `md5sum <dump_file.sql.gz.zip> > <dump_file.sql.gz.zip.md5sum>`

4. 上传至中转服务器`tmp.link`

    `curl -k -F "file=@<dump_file.sql.gz.zip>" -F "token=kzzzzaypns" -F "model=0" -F "utoken=sCH066OaaaC" -X POST "https://connect.tmp.link/api_v2/cli_uploader2"`

5. 从中转服务器下载`先在浏览器打开临时链接，拿到真实下载地址，去 Remote 服务器下载`

    `wget <tmp_down_link>`

6. Remote 解压&恢复数据库

    ```shell
    unzip <dump_file.sql.gz.zip>
    dropdb <database> && createdb <database>
    gunzip <dump_file.sql.gz> | psql -d <db_name> -p <port> -U <db_user>
    ```

