---
title: "Django Development With Docker Compose and Machine"
date: 2018-06-15T14:53:16+08:00
tags: ['DOCKER']
comments: true
---

这篇文章算是对近期将 Django Project 封装到 Docker Container 中的经验总结。

灵感思路取自这篇文章：

https://realpython.com/django-development-with-docker-compose-and-machine/

但是又略有不同：主要是根据项目需要，把文章中的 nginx container 替换为了 Caddy container，方便做全站 HTTPS 加密；另外，也对用 PyCharm 开发调试封装在 Docker Container 中的 Django 应用做了一些探索实践。

整个示例代码：https://github.com/ferstar/dockerizing-django

## 安装 Docker 相关

我开发机是 Windows 平台，平时比较常用 VirtualBox，所以安装的是 [Docker Toolbox](https://www.docker.com/products/docker-toolbox) ，没有使用 Windows 自带的 Hyper-V 虚拟化方式。具体安装步骤很简单，根据官方说明一路 Next 即可。

装好后看下输出：

```shell
$ docker-machine version
docker-machine.exe version 0.14.0, build 89b8332
$ docker-compose version
docker-compose version 1.20.1, build 5d8c71b2
docker-py version: 3.1.4
CPython version: 3.6.4
OpenSSL version: OpenSSL 1.0.2k  26 Jan 2017
```

你可能会遇到如下错误提示：

```shell
exec: "docker-credential-wincred": executable file not found in %PATH%, out: ``
```

解决方法是去 <https://github.com/docker/docker-credential-helpers/releases> 下载这货 **docker-credential-wincred-v0.6.0-amd64.zip**，解压`docker-credential-wincred.exe`到 Docker Toolbox 的目录下，一般是`C:\Program Files\Docker Toolbox\` ，就 OK 了。

接下来克隆我的示例代码

`git clone https://github.com/ferstar/dockerizing-django.git`

整个目录结构应该是这样：

```shell
│  .env
│  .gitignore
│  docker-compose.yml
│  production.yml
│  README.md
│
├─caddy
│      access.log
│      Caddyfile
│      Caddyfile_tls
│
└─web
    │  Dockerfile
    │  manage.py
    │  requirements.txt
    │
    ├─docker_django
    │  │  settings.py
    │  │  urls.py
    │  │  wsgi.py
    │  │  __init__.py
    │  │
    │  └─apps
    │      │  __init__.py
    │      │
    │      └─todo
    │          │  admin.py
    │          │  models.py
    │          │  tests.py
    │          │  urls.py
    │          │  views.py
    │          │  __init__.py
    │          │
    │          └─templates
    │                  home.html
    │                  _base.html
    │
    ├─static
    │      main.css
    │
    └─tests
            test_env_settings.py
            __init__.py
```

## 在 PyCharm 中开发调试

1. 打开代码目录 - `File -> Open -> dockerizing-django`
2. 配置 Docker - `File -> Settings -> Build, Execution, Deployment -> Docker -> Tool[docker-machine, docker-compose]`
3. 配置 Project Interpreter - `File -> Settings -> Project dockerizing-django -> Project Interpreter -> Add -> Docker Compose -> Service: web -> OK`
4. 配置 Build Docker Image - `Run -> Edit Configurations -> + -> Docker -> Docker Compose -> Service(s): web -> OK`
5. 配置 RUN Configurations - `Run -> Edit Configurations -> + -> Host: 0.0.0.0 -> OK`
6. 初始化数据库 - `docker-compose run --no-deps --rm web python manage.py migrate` 
7. 静态文件整理 - `docker-compose run --no-deps --rm web python manage.py collectstatic` 
8. Build && Run~ have fun!

没图貌似不行，找时间配图吧。*生产环境配置只需要指明使用 production.yml 即 `docker-compose -f production.yml xxx`*

PS：项目中还用到了 RabbitMQ 管理队列服务，大概贴下 docker-compose.yml 内容（示例代码中没有涉及到）

```yaml
...  
  rabbitmq:
    restart: always
    image: rabbitmq:3-management
    container_name: scs_rabbitmq
    hostname: rabbitmq
    environment:
      RABBITMQ_ERLANG_COOKIE: "WOWOWOWOWWOWOWOW"
      RABBITMQ_DEFAULT_USER: "rabbitmq"
      RABBITMQ_DEFAULT_PASS: "helloworld"
      RABBITMQ_DEFAULT_VHOST: "/"
    ports:
      - 15672:15672
      - 5672:5672
    volumes:
      - rabbitmq:/var/lib/rabbitmq
...
```

