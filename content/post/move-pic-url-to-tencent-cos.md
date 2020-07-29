---
title: "将图床从七牛云迁移到腾讯COS"
date: "2018-11-30T12:34:00+08:00"
tags: ['OTHERS']
comments: true
---

七牛云的免费域名现在有了生命周期, 才一个月有效期就会被收回, 所以是时候给博客图床挪个窝了

看了下腾讯COS免费额度还不错, 嗯还带HTTPS, 真香, 速度迁移

迁移过程参考这篇文章:

http://robotkang.cc/2018/11/pic/

简单记录如下

```shell
# 1. 把原 bucket 中需要下载的内容清单用 qshell 拖下来
qshell listbucket <原 bucket> | grep -v '_log' | awk "{print $1}" > list.txt
# 2. 新建一个 bucket 如 new, 然后内容转移到 new
qshell batchcopy <old> <new> -i list.txt
# 3. 从 new 批量下载到本地
qshell qdownload batch_download.conf

# batch_download.conf 内容如下
{
    "dest_dir" : "/xxx/xxx/Downloads/qiniu",
    "bucket" : "new", （新建的 bucket 的名称）
    "prefix" : "",
    "suffixes" : "",
    "cdn_domain" : "http://pgiolcvny.bkt.clouddn.com",（新建的 bucket 的测试域名）
    "referer" : "",
    "log_file" : "download.log",
    "log_level" : "info",
    "log_rotate" : 1,
    "log_stdout" : false
}

# 4. 上传下载的文件到腾讯COS, 这个纯浏览器就能操作

# 5. 批量替换博文中七牛云链接为腾讯COS链接
sed -i 's#http://xxx.z0.glb.clouddn.com#https://blog-xxxx.cos.ap-chengdu.myqcloud.com#g' *.md
```

大功告成~