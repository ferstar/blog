---
title: "Upgrading PostgreSQL from v14 to v15"
date: "2023-02-03T11:51:35+08:00"
tags: ['Linux', 'PostgreSQL']
comments: true
---

奶奶的又升16了，都开始刷版本，我不跟了，Docker 钉死先

```yml
version: "3.8"

services:
  postgres:
    restart: on-failure
    container_name: pg_pin
    image: postgres:15
    volumes:
      - "./pg_data:/var/lib/postgresql/data"
    environment:
      - DEBUG=false
      - POSTGRES_PASSWORD=xzsDwlk3LqaY
    # ports:
      # - 5432:5432
    network_mode: host
```

---

> https://wiki.archlinux.org/title/PostgreSQL#Upgrading_PostgreSQL

我的 PG 一般是随项目走的，假设路径：data/pg_data

- mv data/pg_data data/pg_data.old
- pacman -S postgresql-old-upgrade
- initdb -D data/pg_data --locale=zh_CN.UTF-8 --encoding=UTF8
- pg_upgrade -b /opt/pgsql-14/bin -B /usr/bin -d data/pg_data.old -D data/pg_data
- 一切正常后删掉 data/pg_data.old 备份
- 卸载掉 postgresql-old-upgrade

一些输出：

```shell

The files belonging to this database system will be owned by user "ferstar".
This user must also own the server process.

The database cluster will be initialized with locale "zh_CN.UTF-8".
initdb: could not find suitable text search configuration for locale "zh_CN.UTF-8"
The default text search configuration will be set to "simple".

Data page checksums are disabled.

creating directory data/pg_data ... ok
creating subdirectories ... ok
selecting dynamic shared memory implementation ... posix
selecting default max_connections ... 100
selecting default shared_buffers ... 128MB
selecting default time zone ... Asia/Shanghai
creating configuration files ... ok
running bootstrap script ... ok
performing post-bootstrap initialization ... ok
syncing data to disk ... ok

initdb: warning: enabling "trust" authentication for local connections
initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.

Success. You can now start the database server using:

    pg_ctl -D data/pg_data -l logfile start

Performing Consistency Checks
-----------------------------
Checking cluster versions                                   ok
Checking database user is the install user                  ok
Checking database connection settings                       ok
Checking for prepared transactions                          ok
Checking for system-defined composite types in user tables  ok
Checking for reg* data types in user tables                 ok
Checking for contrib/isn with bigint-passing mismatch       ok
Creating dump of global objects                             ok
Creating dump of database schemas
                                                            ok
Checking for presence of required libraries                 ok
Checking database user is the install user                  ok
Checking for prepared transactions                          ok
Checking for new cluster tablespace directories             ok

If pg_upgrade fails after this point, you must re-initdb the
new cluster before continuing.

Performing Upgrade
------------------
Analyzing all rows in the new cluster                       ok
Freezing all rows in the new cluster                        ok
Deleting files from new pg_xact                             ok
Copying old pg_xact to new server                           ok
Setting oldest XID for new cluster                          ok
Setting next transaction ID and epoch for new cluster       ok
Deleting files from new pg_multixact/offsets                ok
Copying old pg_multixact/offsets to new server              ok
Deleting files from new pg_multixact/members                ok
Copying old pg_multixact/members to new server              ok
Setting next multixact ID and offset for new cluster        ok
Resetting WAL archives                                      ok
Setting frozenxid and minmxid counters in new cluster       ok
Restoring global objects in the new cluster                 ok
Restoring database schemas in the new cluster
                                                            ok
Copying user relation files
                                                            ok
Setting next OID for new cluster                            ok
Sync data directory to disk                                 ok
Creating script to delete old cluster                       ok
Checking for extension updates                              ok

Upgrade Complete
----------------
Optimizer statistics are not transferred by pg_upgrade.
Once you start the new server, consider running:
    /usr/bin/vacuumdb --all --analyze-in-stages

Running this script will delete the old cluster's data files:
    ./delete_old_cluster.sh
```

可能会碰到的报错：

Q: lc_collate values for database "template1" do not match:  old "zh_CN.UTF-8", new "en_US.UTF-8"

A: initdb -D data/pg_data --locale=zh_CN.UTF-8 --encoding=UTF8 指定一样的locale即可



```
# NOTE: I am not responsible for any expired content.
create@2023-02-03T11:51:35+08:00
update@2023-12-26T02:27:10+08:00
comment@https://github.com/ferstar/blog/issues/74
```
