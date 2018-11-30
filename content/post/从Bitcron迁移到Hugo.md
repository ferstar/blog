---
title: "从Bitcron迁移到Hugo"
date: 2017-12-12T17:08:07+08:00
tags: ['PYTHON', 'HUGO']
comments: true
---

> 跟随老大的[脚步](https://tech.crandom.com/post/2017/switch-to-hugo/)，拥抱hugo，拥抱CI。

## Caddy && Hugo with Docker

安装Docker什么的暂且不表，基本都是拿来主义。

`docker run -d -p 2015:2015 muninn/hugo-caddy`

docker会自动把这个镜像拖下来。

## GitHub托管Hugo站点

按照Hugo官网手册把站点搞起，然后托管到GitHub上

https://github.com/ferstar/blog

## VPS端Caddy配置

```shell
mkdir ~/.caddy
vi ~/.caddy/Caddyfile
# 这货配置文件比Nginx简约太多。。。
blog.ferstar.org {
    root /www/public
    timeouts 10m
    gzip
    tls fer_star@qq.com
    tls {
        protocols tls1.0 tls1.2
    }
    # sync the repo and then gen public site
    git {
        repo {$REPO}
        path ../src
        hook /webhook
        args --recurse-submodules
        then hugo --destination=/www/public
    }

    # write log to stdout for docker
    log stdout
    errors stdout
}

ferstar.org {
    redir https://blog.ferstar.org
}
```

## docker-compose配置

用Docker自然少不了这货，配个适用于自己站点的`docker-compose.yml`

```shell
version: '2'
services:
    hugo:
        image: muninn/hugo-caddy
        volumes:
            - /root/.caddy/Caddyfile:/etc/Caddyfile
            - /root/.caddy:/root/.caddy
        ports:
            - 80:80
            - 443:443
        environment:
            - REPO=github.com/ferstar/blog
        restart: unless-stopped
```

因为要用`Let's Encrypt`的证书给网站上小绿锁，所以需要把`80`和`443`端口交给Caddy，另外需要指定存放认证的路径。

## 持续集成(GitHub Webhooks)

所谓`CI`在这里就是利用GitHub的Webhooks服务，每次接受推送`push`（貌似还可以指定别的事件类型）事件时，给VPS站点发一个`POST`通知，然后VPS收到通知后会自动执行拉取GitHub指定分支内容，然后Hugo自动生成静态页面，最后重启Caddy服务，整个过程如丝顺滑~

![微信截图_20171226164109](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/png/2017/12/405b246b70f9de2c4bd98c93afaaa007.png)

## 转换旧文章

原来的水文都是在Bitcron写的，文件头信息格式不太一样，于是写脚本转换了下。

```python
import os
import sys
from chardet.universaldetector import UniversalDetector

if len(sys.argv) != 3:
    sys.exit("Usage: {} source_dir dest_dir".format(sys.argv[0]))

src_dir = sys.argv[1]
new_dir = sys.argv[2]

if not os.path.exists(new_dir):
    os.mkdir(new_dir)


def detect(fp):
    detector = UniversalDetector()
    with open(fp, 'rb') as fh:
        for line in fh:
            detector.feed(line)
            if detector.done: break
    detector.close()
    return detector.result['encoding']


def get_files(dp):
    for root, dirs, files in os.walk(dp):
        return map(lambda x: os.path.join(root, x), files)


def convert_article(fp):
    file_name = os.path.basename(fp).split('.')[:-1][0]
    new_fp = os.path.join(new_dir, file_name) + ".md"
    encoding = detect(fp)
    tags_line = ''
    status = 'draft'
    with open(fp, 'r', encoding=encoding) as fh:
        # hexo header metadata
        while True:
            line = fh.readline()
            if line.startswith("---"):
                break
        while True:
            line = fh.readline()
            if line.startswith("---"):
                break
            if line.startswith("date"):
                _date = 'T'.join(line.strip().split(" ")[1:])
                if len(_date) == 16:
                    date_line = _date + ':00+08:00'
                else:
                    date_line = _date + '+08:00'
            if line.startswith("title"):
                title_line = line.strip().replace("'", "").replace('"', '').split(':')[-1].strip()
                if title_line.startswith('"'):
                    title_line = title_line.replace('"', '')
            if line.startswith('status'):
                status = line.strip().split(' ')[-1]
            if line.startswith('tags'):
                tags_line = str(line.strip().replace("'", "").replace(' ', '').split(':')[-1].split(',')).upper()
        if status == 'draft':
            return
        with open(new_fp, 'w', encoding='utf-8') as out:
            # bitcron header metadata
            out.write("---\n")
            out.write('title: "{}"\n'.format(title_line))
            out.write('date: "{}"\n'.format(date_line))
            if tags_line:
                out.write('tags: {}\n'.format(tags_line))
            else:
                out.write("tags: ['OTHERS']\n")
            out.write("comments: true\n")
            out.write("---\n\n")
            # copy the rest lines
            while 1:
                line = fh.readline()
                if not line:
                    break
                out.write(line)


list(map(convert_article, get_files(src_dir)))

```
## 配置站点favicon

用的主题貌似没有favicon，而且缺了个`apple-touch-icon-144-precomposed.png`的静态资源，想来应该是把`favicon.ico`一起塞到`static`目录下，试了下果然ok。

[Where do I put my favicon with Hugo](https://stackoverflow.com/questions/42043648/where-do-i-put-my-favicon-with-hugo)
