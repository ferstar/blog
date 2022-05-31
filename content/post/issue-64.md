---
title: "指定第三方工具加速下载AUR包"
date: "2022-05-31T07:35:23+08:00"
tags: ['Linux']
comments: true
---

> 众所周知的原因，一些位于github上的AUR包不挂梯子默认是很难直接下载成功的，哪怕仅仅就几百KB。简单搜了下网友的解决方案，自己糊了个脚本，基本满足需求

1. 修改`/etc/makepkg.conf`，将pacman默认下载工具指向自己写的脚本

```shell
# DLAGENTS=('file::/usr/bin/curl -qgC - -o %o %u'
#           'ftp::/usr/bin/curl -qgfC - --ftp-pasv --retry 3 --retry-delay 3 -o %o %u'
#           'http::/usr/bin/curl -qgb "" -fLC - --retry 3 --retry-delay 3 -o %o %u'
#           'https::/usr/bin/curl -qgb "" -fLC - --retry 3 --retry-delay 3 -o %o %u'
#           'rsync::/usr/bin/rsync --no-motd -z %u %o'
#           'scp::/usr/bin/scp -C %u %o')
DLAGENTS=('file::/home/ferstar/.local/bin/lftp_wrapper.sh %u %o'
          'ftp::/home/ferstar/.local/bin/lftp_wrapper.sh %u %o'
          'http::/home/ferstar/.local/bin/lftp_wrapper.sh %u %o'
          'https::/home/ferstar/.local/bin/lftp_wrapper.sh %u %o'
          'rsync::/usr/bin/rsync --no-motd -z %u %o'
          'scp::/usr/bin/scp -C %u %o')
```

2. 写脚本处理URL&调起第三方下载工具下载文件

```shell
#!/usr/bin/env bash


LFTP_BIN=/usr/bin/lftp
AXEL_BIN=/usr/bin/axel

USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
PROCESS_COUNT=$(($(nproc)+1))
URL=$1
OUT_PATH=$2

# 可以自行使用其他镜像站点替换
# replace "github.com" with "hub.fastgit.xyz" mirror
URL=${URL//github.com/hub.fastgit.xyz}
# replace "raw.githubusercontent.com" with "raw.fastgit.org" mirror
URL=${URL//raw.githubusercontent.com/raw.fastgit.org}

# $LFTP_BIN -e \
#     "set ssl:verify-certificate false;
#     set net:idle 10;
#     set net:max-retries 3;
#     set net:reconnect-interval-base 3;
#     set net:reconnect-interval-max 3;
#     set http:user-agent '$USER_AGENT';
#     pget -n $PROCESS_COUNT -c $URL -o $OUT_PATH;
#     quit;"
$AXEL_BIN --max-redirect=3 -n $PROCESS_COUNT -a -k -U "$USER_AGENT" $URL -o $OUT_PATH
```

脚本里用到的`lftp`和`axel`都需要单独安装，实测网络实在垃圾的情况下，`lftp`比`axel`要靠谱一些，基本上不会失败；但网络还可以的话，大部分情况`axel`是要快一倍左右，平均`2MB/s`上下的速度，基本也够用了。

---

> 参考

[机智的解决arch/manjaro安装AUR软件时github下载软件包慢或不可获得的问题](https://zhuanlan.zhihu.com/p/176987140)



```
# NOTE: I am not responsible for any expired content.
create@2022-05-31T07:35:23+08:00
update@2022-05-31T07:35:23+08:00
comment@https://github.com/ferstar/blog/issues/64
```
