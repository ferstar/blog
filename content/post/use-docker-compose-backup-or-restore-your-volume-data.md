---
title: "利用docker-compose备份、还原volume数据"
date: "2018-06-14T15:17:00+08:00"
tags: ['DOCKER']
comments: true
---

先说说实际情况，最近做的项目跑在 AWS 的 EC2 上面，林林总总依赖好几个服务；实际开发却是用的 Windows10，还好有 Docker 这神器。

有个 PostgreSQL 的容器资料开始是挂在名叫 pgdata 的一个 volume 上面，为方便本机调试我修改了 docker-compose.yml 的部分内容，实际的 volume 变成了 scsweb_pgdata

这就面临一个问题，原来 pgdata 的数据怎么迁移到新的 scsweb_pgdata 上来？

可以参考我这里的例子去迁移 pg 数据库，但感觉太麻烦，觉得应该有更简单的方式。

自然求助万能的 Google 希望能够有 volume clone 的神奇命令搞定，然而目前 docker volume 支持的指令只有 

```shell
$ docker volume

Usage:  docker volume COMMAND

Manage volumes

Options:


Commands:
  create      Create a volume
  inspect     Display detailed information on one or more volumes
  ls          List volumes
  prune       Remove all unused local volumes
  rm          Remove one or more volumes

Run 'docker volume COMMAND --help' for more information on a command.
```

这么几个，完全不够用。还好发现有好心人弄了个脚本

via -> https://loomchild.net/2017/03/26/backup-restore-docker-named-volumes/

满心欢喜去照抄进终端，然后来了个大大的错误：

```shell
$ docker run -it -v scsweb_pgdata:/volume -v ./db:/backup alpine \
> sh -c "rm -rf /volume/* /volume/..?* /volume/.[!.]* ; tar -C /volume/ -xjf /backup/pgdata.tar.bz2"
C:\Program Files\Docker Toolbox\docker.exe: Error response from daemon: create .\db;C: ".\\db;C" includes invalid characters for a local volume name, only "[a-zA-Z0-9][a-zA-Z0-9_.-]" are allowed. If you intended to pass a host directory, use absolute path.
See 'C:\Program Files\Docker Toolbox\docker.exe run --help'.
```

同样的命令在 Linux 系统是没有任何问题的，为了短平快解决问题，我并没有过于深究这个原因，而是曲线救国的方案，利用 docker-compose 来搞

```yml
# filename: docker-compose.yml
backup:
  image: alpine
  volumes:
    - ./db:/backup
    - pgdata:/volume
  command: tar -cjf /backup/pgdata.tar.bz2 -C /volume ./

restore:
  image: alpine
  volumes:
    - ./db:/backup
    - scsweb_pgdata:/volume
  command: sh -c "rm -rf /volume/* /volume/..?* /volume/.[!.]* ; tar -C /volume/ -xjf /backup/pgdata.tar.bz2"
  ```
  
  原理很简单，就是把要备份的 volume 和存放备份的目录，比如我这里是用的当前目录下 db 目录挂载到一起，然后用 tar 命令打包。
  
  使用方法：
  
  1. 备份 - `docker-compose run --rm backup`
  2. 还原 - `docker-compose run --rm restore`
  
  PS：自行替换对应文件名
  
