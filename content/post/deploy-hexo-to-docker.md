---
date = "2015-09-04T19:08:47+08:00"
title = "使用docker构建hexo环境"
tags = ['DOCKER', 'HEXO', 'LINUX']
---
# 前言  
最近花了点时间重整博客，由于受不了wordpress的日益臃肿，决定迁移到时下很火的[hexo](https://hexo.io/)，hexo基于node.js，所以首先需要搭建node环境，折腾起来略麻烦，实在不想在公司机器和自己的笔电上来回装，于是打算寻个一劳永逸的方法，偶然想到[docker](https://www.docker.com/) ，所以就有了下面的尝试……


# 开始尝试

## 安装docker

### 懒人安装法
`apt-get install update && apt-get install -y docker.io`    
装完之后会自动启动docker服务，此方法安装的docker版本略低，所以并不推荐。

### 略高大的安装法
大部分Linux发行版均可以通过下面的命令安装：
`curl -sSL https://get.daocloud.io/docker | sh`  
为了下载docker镜像的速度能快些，建议配置好[daocloud](https://www.daocloud.io/) 加速。

## 获取镜像
本来的命令是`docker pull ubuntu:14.04`，如果配置了daocloud加速的话，会是这样`dao pull ubuntu:14.04`

## 运行容器
`docker run -t -i ubuntu:14.04 /bin/bash`
记住容器的id，比如`0b2616b0e5a8`

## 更换容器sources.list
修改repo指向阿里云ubuntu镜像
`sed -i ‘s/us.archive.ubuntu.com/mirrors.aliyun.com/g’ /etc/apt/sources.list`

## 容器中添加hexo相关应用

- `apt-get update`  
  `apt-get install -y git-core nodejs npm`  
- 软链接nodejs到node
  `ln -s /usr/bin/nodejs /usr/bin/node`  
- 安装hexo，也许你需要阿里cnpm的拯救，传送门：[淘宝NPM镜像](http://ferstar.org/2015/09/04/%E6%B7%98%E5%AE%9DNPM%E9%95%9C%E5%83%8F/) 
  `cnpm install -g hexo`
- 添加一个非root用户  
  `adduser hexo`剩下的按照提示做即可
- 完成后`exit`退出，此时容器已经改变，用docker commit命令提交更新后的副本
  `sudo docker commit -m "Added hexo" -a "Docker hexo" 0b2616b0e5a8 hexo:v1`

## 用Dockerfile来创建镜像

dockerfile内容大概是这样子：  

```  
#
# Hexo Dockerfile
#

# Pull base image.
FROM hexo:v1
MAINTAINER ferstar <zhangjianfei3@gmail.com>

ENV HOME /home/hexo

# Mount a Host Directory as a Data Volume for hexo
VOLUME /blog

# Expose ports.
EXPOSE 4000

WORKDIR /blog

USER hexo  
```

根据dockerfile创建镜像
`docker build -t hexo:v2 .`

## 测试容器hexo是否安装成功

`docker run --rm -v "$PWD:/blog" -p 4000:4000 hexo:v2 hexo -v`
结果显示如下，说明安装成功

```
hexo: 3.1.1
os: Linux 3.19.0-28-generic linux x64
http_parser: 1.0
node: 0.10.25
v8: 3.14.5.9
ares: 1.10.0
uv: 0.10.23
zlib: 1.2.8
modules: 11
openssl: 1.0.1f
```

## 导出镜像到本地

`docker save -o hexo_v2.tar hexo:v2`

## 部署镜像到新系统

此时新系统只需要安装docker，然后将上一步生成的镜像导入docker中
`docker load < hexo_v2.tar`

## 在新系统中部署hexo博客

新建博客目录，如`~/blog`

```
mkdir ~/blog
cd blog
```

原本的初始化命令`hexo init`变成了如下的命令
`docker run --rm -v "$PWD:/blog" -p 4000:4000 hexo:v2 hexo init`
`npm install`变成如下的命令
`docker run --rm -v "$PWD:/blog" -p 4000:4000 hexo:v2 cnpm install`
至此，新的hexo blog即成功建立，当然为了简化命令，你可以把上述命令加入到bash或者zsh alias里面，如

```
docker-hexo="docker run --rm -v "$PWD:/blog" -p 4000:4000 hexo:v2"
hexo="docker-hexo hexo"
```

重新打开终端后hexo命令就和原来一样用了，`npm`命令则变成了`docker-hexo cnpm`
安装插件的命令变成这样
`docker-hexo cnpm install plugin_name --save`
至于平时写作发布指令跟原来别无二致

# 后记
生成的docker镜像还是太大，417MB，过程也略繁琐，需要进一步选择轻量级的迁移方案。

# 参考文章
1. [ubuntu 修改repo直接成阿里云](http://www.philo.top/1899/11/30/ubuntuChangeRepo/) 
2. [在OSX下使用docker构建hexo环境](http://open.daocloud.io/build-hexo-env-by-docker-under-osx/) 
3. [Docker —— 从入门到实践](http://yeasy.gitbooks.io/docker_practice/content/index.html) 
4. [Docker Container for Hexo](https://github.com/billryan/docker-hexo) 