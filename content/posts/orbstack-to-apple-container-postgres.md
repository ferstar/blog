---
title: "从 OrbStack 换到 Apple Container：顺手把 PostgreSQL 搬了家"
slug: "orbstack-to-apple-container-postgres"
date: "2026-06-13T18:40:39+08:00"
tags: ['Mac', 'Container', 'PostgreSQL']
description: "OrbStack 可以退场了，但 PostgreSQL 数据不能丢；这次用 Apple Container 接管本地数据库，顺手关掉本地 WAL 归档，最后释放了约 19GiB 磁盘空间。"
series: ['Homelab']
---

今天把本机的 OrbStack 卸了。

不是因为它不好用。恰恰相反，OrbStack 这几年一直是我在 macOS 上最省心的 Docker 替代品。但 Apple 自己的 `container` CLI 已经能跑 Linux 容器了，本地目前真正长期运行的服务只剩一个 PostgreSQL。既然依赖面已经收窄，就顺手把运行时也收窄一下。

这类迁移最怕一句“直接删了重来”。容器可以重建，数据库不行。

### 先看清楚到底在跑什么

原来 OrbStack 里只有一个长期运行的容器：

```bash
docker ps -a --format '{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'
```

结果很简单：

```text
d377e0104620  registry.cheftin.cn/p/postgres17_pd-arm64  scriber_pg  Up 2 weeks (healthy)
```

看 `docker inspect` 时发现一个坑：`docker-compose.yml` 里挂的是 `./pg17:/var/lib/postgresql/data`，但镜像实际用的 `PGDATA=/data/data`。也就是说，宿主机的 `pg17` 是空目录，真正的数据在旧容器内部的 `/data`。

这个差点让迁移变成事故。

```text
PGDATA=/data/data
/Users/ferstar/myprojects/postgresql/pg17  0B
/data                                 7.2G
```

所以不能停掉 OrbStack 后指望“原目录重挂”就完事，必须先从运行中的旧容器导出。

### 备份先行

我做了两份备份：

```bash
docker exec scriber_pg pg_dumpall -U postgres | gzip -9 > pg_dumpall.sql.gz
docker exec scriber_pg tar -C / -cf - data | zstd -T0 -10 > container-data.tar.zst
```

逻辑备份只有 `38M`，物理归档一开始有 `6.8G`。当时我还以为数据库很大，后来才发现不是。

`/data` 大头不是业务数据，而是镜像自己的本地 WAL 归档：

```text
6865.7M  data/backup/wal
293.5M   data/data/base
126.7M   data/data/log
32.0M    data/data/pg_wal
```

真正的表数据也就几百 MB。

### Apple Container 接手

本机是 macOS 15.7.3，Apple `container` 官方更偏向 macOS 26，但 Homebrew 已经能装：

```bash
brew install container
container system start
```

第一次启动会安装默认 kernel。跑个 Alpine 测试通过后，把 PostgreSQL 镜像从 Docker 本地导出再导入 Apple Container，绕过私有 registry 凭据问题：

```bash
docker save registry.cheftin.cn/p/postgres17_pd-arm64:latest -o postgres17_pd-arm64.docker-save.tar
container image load -i postgres17_pd-arm64.docker-save.tar
```

正式容器最后这样跑：

```bash
container run -d \
  --name scriber_pg \
  --memory 4g \
  --cpus 4 \
  --shm-size 8g \
  -p 0.0.0.0:5432:5432 \
  -v /Users/ferstar/myprojects/postgresql/apple-pg17:/data \
  -e DEBUG=false \
  -e POSTGRES_PASSWORD=... \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  registry.cheftin.cn/p/postgres17_pd-arm64:latest \
  postgres -c archive_mode=off -c archive_command=
```

这里最后两个 `-c` 很关键。

这个镜像启动时会重写 `postgresql.conf`，直接改数据目录里的配置会被覆盖。把 `archive_mode=off` 放到 PostgreSQL 启动参数里，来源会变成 `command line`，重启后也稳定。

验证结果：

```text
archive_command=(disabled) source=command line
archive_mode=off source=command line
wal_level=logical source=configuration file
```

`wal_level=logical` 我没有动。它不是本地备份膨胀的来源，贸然关掉还可能影响逻辑复制或扩展。

### 自动启动补一刀

Apple Container 现在还没有 Docker Compose 那种 `restart: unless-stopped` 体验。`brew services start container` 只能保证 apiserver 登录后起来，不保证具体容器自动启动。

所以我加了一个用户级 LaunchAgent：

```text
~/Library/LaunchAgents/com.ferstar.apple-container.scriber-pg.plist
```

实际执行的是一个很小的脚本：

```bash
container system start >/tmp/scriber_pg_container_system_start.log 2>&1 || true

if container ls --quiet | grep -Fxq 'scriber_pg'; then
  exit 0
fi

container start scriber_pg
```

不华丽，但够用。

### 清理完的账

最后把 OrbStack 卸载并 zap：

```bash
brew uninstall --cask --zap orbstack
```

顺手清掉 `~/.orbstack`、`~/OrbStack`、Group Containers 里的残留。因为本机的 Docker CLI 也是 OrbStack 带来的，卸载后 `docker` 命令也一起没了。这个没关系，现在日常只需要 `container`。

清理效果：

```text
迁移中最紧张时可用空间：  6.8GiB
删除物理回滚包后：       14GiB
卸载 OrbStack 后：       26GiB
总体释放：               约 19GiB
```

当前占用：

```text
Apple Container 运行时数据： 3.8G
PostgreSQL 新数据目录：     274M
迁移逻辑备份和日志：        76M
scriber_pg 实际内存：       约 148MiB / 4GiB
scriber_pg CPU：            0.00%
```

数据库也还在：

```text
postgres|11
```

### 结尾

这次迁移最大的教训不是 Apple Container 怎么用，而是：别相信 compose 文件表面上的 volume，先看运行中容器的真实 `PGDATA` 和 mount。

另一个收获是，备份目录要分清“数据库运行必需的 WAL”和“额外归档出来的 WAL”。前者不能碰，后者如果本地不需要，就应该关掉。不然一个几百 MB 的数据库，迟早被几 GB 的归档文件吓一跳。

OrbStack 退场，PostgreSQL 留下。机器少跑一个常驻运行时，也算给这台 Mac 减了点负。
