---
title: "Sci-Hub Spider"
date: 2017-12-18T15:22:02+08:00
tags: ['PYTHON']
comments: true
---

众所周知，科研神器`SciHub`近来并不稳定，频繁更换域名，为了方便单位科研同学，上周写了SCI文献下载器，并在朋友圈发布，反响颇佳。周末又重新理了一遍逻辑，现在论文下载能力应该是得到了进一步增强。

工具原理很简单，主要利用了爬虫技术。PMID/PMCID/Manuscript ID/DOI ID转换是通过爬取`NCBI`主站获得。

拿到DOI号后即开始检索文献真实下载地址，优先从[libgen.io](libgen.io)爬取，爬取失败再去`sci-hub`目前可用的镜像站点爬取。

爬取成功则将文章保存在用户桌面。

全程只需打开软件，复制要下载文章的PMID/PMCID/Manuscript ID/DOI等任一ID，程序可以自动从复制内容中解析出ID信息进行检索，找到文章即下载到桌面。

程序运行信息如下：

```shell
 ________________
| Sci-Hub Spider |
 ----------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\-
                ||----w |
                ||     ||
                written by ferstar with love

usage: copy a DOI or any content that contains a valid DOI and bubble a cup of tea
btw:   PMID/PMCID/Manuscript ID also supported but not recommended
       Please note that not all papers can be downloaded successfully
blog:  https://blog.ferstar.org

I need to check if scihub is available locally
it may take a few seconds, please wait

fetching available sci-hub mirrors
sci-hub mirror list updated

check site status "https://sci-hub.sci-hub.tw"...ok
check site status "https://www.sci-hub.cn"...ok
check site status "https://sci-hub.sci-hub.tv"...ok
check site status "https://sci-hub.ws"...ok
check site status "https://sci-hub.sci-hub.mn"...ok
check site status "https://sci-hub.hk"...ok
check site status "https://sci-hub.is"...ok
check site status "https://sci-hub.tw"...ok
check site status "https://sci-hub.tv"...ok
check site status "https://sci-hub.la"...ok
check site status "https://sci-hub.name"...ok
check site status "https://sci-hub.sci-hub.hk"...ok
check site status "https://sci-hub.mn"...ok

DOI detected:10.1111/1744-9987.12606,fetching...
try to fetch on "libgen.io"
paper found, will download
[Role of Plasmapheres...] download completed 233.66 KB / 233.66 KB
paper has been saved on you Desktop

press enter key to continue or click the close button to exit

ID detected:29229651,need convert to DOI...
DOI converted:10.1126/science.aao4134,fetching...
try to fetch on "libgen.io"
paper not found on "libgen.io"
try to fetch on "https://sci-hub.sci-hub.hk"
paper not found on "https://sci-hub.sci-hub.hk"
sorry, paper not found

DOI detected:10.1126/science.aao4134,fetching...
try to fetch on "libgen.io"
paper not found on "libgen.io"
try to fetch on "https://sci-hub.hk"
paper found, will download
[10.1126@science.aao4...] download completed 1150.47 KB / 1150.47 KB
paper has been saved on you Desktop

press enter key to continue or click the close button to exit

ID detected:29229651,need convert to DOI...
DOI converted:10.1126/science.aao4134,fetching...
try to fetch on "libgen.io"
paper found, will download
[In situ measurements...] download completed 1150.47 KB / 1150.47 KB
paper has been saved on you Desktop

press enter key to continue or click the close button to exit
```

