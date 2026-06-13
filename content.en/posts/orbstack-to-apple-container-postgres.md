---
title: "Moving from OrbStack to Apple Container, with PostgreSQL in Tow"
slug: "orbstack-to-apple-container-postgres"
date: "2026-06-13T18:40:39+08:00"
tags: ['Mac', 'Container', 'PostgreSQL']
description: "OrbStack was ready to go, but the local PostgreSQL data had to survive; I moved it to Apple Container, disabled local WAL archiving, and freed about 19GiB of disk space."
series: ['Homelab']
---

> I am not a native English speaker; this article was translated by AI.

Today I removed OrbStack from my Mac.

Not because it was bad. Quite the opposite: for the past few years, OrbStack has been the least annoying Docker replacement I have used on macOS. But Apple's own `container` CLI can now run Linux containers, and the only long-running local service I still had was PostgreSQL. With the dependency surface already this small, it made sense to shrink the runtime too.

The dangerous version of this migration would be: "just delete it and recreate it." Containers can be recreated. Databases cannot.

### First, check what is actually running

There was only one long-running container in OrbStack:

```bash
docker ps -a --format '{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'
```

The result was simple:

```text
d377e0104620  registry.cheftin.cn/p/postgres17_pd-arm64  scriber_pg  Up 2 weeks (healthy)
```

Then `docker inspect` exposed the trap: `docker-compose.yml` mounted `./pg17:/var/lib/postgresql/data`, but the image actually used `PGDATA=/data/data`. In other words, the host-side `pg17` directory was empty, while the real database lived inside the old container under `/data`.

That almost turned the migration into an incident.

```text
PGDATA=/data/data
/Users/ferstar/myprojects/postgresql/pg17  0B
/data                                 7.2G
```

So I could not simply stop OrbStack and remount the same host directory. I had to export the data from the running old container first.

### Backups first

I made two backups:

```bash
docker exec scriber_pg pg_dumpall -U postgres | gzip -9 > pg_dumpall.sql.gz
docker exec scriber_pg tar -C / -cf - data | zstd -T0 -10 > container-data.tar.zst
```

The logical backup was only `38M`; the physical archive was `6.8G`. At first I thought the database was huge. It was not.

The largest part of `/data` was not business data, but the image's own local WAL archive:

```text
6865.7M  data/backup/wal
293.5M   data/data/base
126.7M   data/data/log
32.0M    data/data/pg_wal
```

The actual table data was only a few hundred MB.

### Apple Container takes over

This machine is on macOS 15.7.3. Apple's `container` project is more officially aimed at macOS 26, but Homebrew can already install it:

```bash
brew install container
container system start
```

The first startup installs the default kernel. After a small Alpine test passed, I exported the PostgreSQL image from local Docker and loaded it into Apple Container, avoiding private registry credential issues:

```bash
docker save registry.cheftin.cn/p/postgres17_pd-arm64:latest -o postgres17_pd-arm64.docker-save.tar
container image load -i postgres17_pd-arm64.docker-save.tar
```

The final container is launched like this:

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

The last two `-c` options matter.

This image rewrites `postgresql.conf` during startup, so editing the file directly inside the data directory gets overwritten. Putting `archive_mode=off` in PostgreSQL command-line arguments makes the setting source `command line`, and it stays stable after restart.

Verification:

```text
archive_command=(disabled) source=command line
archive_mode=off source=command line
wal_level=logical source=configuration file
```

I left `wal_level=logical` alone. It was not the source of the local backup growth, and disabling it casually could break logical replication or extensions.

### One more piece for autostart

Apple Container does not yet feel like Docker Compose with `restart: unless-stopped`. `brew services start container` brings up the apiserver at login, but it does not guarantee a specific container starts.

So I added a user LaunchAgent:

```text
~/Library/LaunchAgents/com.ferstar.apple-container.scriber-pg.plist
```

It runs a tiny script:

```bash
container system start >/tmp/scriber_pg_container_system_start.log 2>&1 || true

if container ls --quiet | grep -Fxq 'scriber_pg'; then
  exit 0
fi

container start scriber_pg
```

Not elegant, but enough.

### The final bill

Then OrbStack was uninstalled and zapped:

```bash
brew uninstall --cask --zap orbstack
```

I also removed leftovers under `~/.orbstack`, `~/OrbStack`, and related Group Containers directories. Since the local Docker CLI came from OrbStack, the `docker` command disappeared too. That is fine; daily usage now only needs `container`.

Cleanup result:

```text
Free space at the tightest point:  6.8GiB
After deleting physical rollback archive: 14GiB
After uninstalling OrbStack:       26GiB
Total freed:                       about 19GiB
```

Current footprint:

```text
Apple Container runtime data: 3.8G
New PostgreSQL data directory: 274M
Migration logical backups/logs: 76M
scriber_pg actual memory: about 148MiB / 4GiB
scriber_pg CPU: 0.00%
```

The databases are still there:

```text
postgres|11
```

### Closing

The biggest lesson here was not how to use Apple Container. It was: do not trust the volume path in a compose file at face value. Check the running container's real `PGDATA` and mounts first.

The other lesson was to distinguish between WAL that PostgreSQL needs to run and WAL that an image archives elsewhere as backup. The former must stay. The latter should be disabled if local backups are not needed. Otherwise, a few-hundred-MB database can eventually scare you with several GB of archived WAL.

OrbStack is gone. PostgreSQL stays. One fewer always-on runtime for this Mac.
