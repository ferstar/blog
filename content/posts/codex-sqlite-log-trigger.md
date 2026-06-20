---
title: "用 SQLite Trigger 给 Codex 日志库止血"
slug: "codex-sqlite-log-trigger"
date: "2026-06-20T16:55:00+08:00"
tags: ['Codex', 'SQLite', 'Logging']
description: "Codex 本地 SQLite 日志库增长太快；用一个 BEFORE INSERT trigger 暂时拦住新日志写入，并保留恢复命令，快速降低磁盘 IO 和 WAL 增长。"
series: ['AI Coding']
---

Codex 最近把本地日志写进 `~/.codex/logs_2.sqlite`，我的库已经涨到 1GB 以上。真正占空间的不是 WAL 文件，而是日志表本身：`TRACE`、`DEBUG`、`INFO` 一直进 SQLite，时间一长就没必要地消耗磁盘和 IO。

官方配置里能调的东西有限：`RUST_LOG` 可以降日志级别，`log_dir` 只管明文 TUI log，`history.max_bytes` 只影响 `history.jsonl`。我没找到公开的 `logs_2.sqlite` retention、max size 或 journal mode 配置。

所以先用 SQLite 自己的机制止血。

### 一条 trigger 拦住新增日志

```bash
sqlite3 ~/.codex/logs_2.sqlite "CREATE TRIGGER IF NOT EXISTS block_log_inserts BEFORE INSERT ON logs BEGIN SELECT RAISE(IGNORE); END;"
```

这条 trigger 的意思很直接：每次有人往 `logs` 表插入数据时，SQLite 直接忽略这次插入。

验证也很简单：

```bash
sqlite3 ~/.codex/logs_2.sqlite "
SELECT count(*) FROM logs;
INSERT INTO logs(ts, ts_nanos, level, target, feedback_log_body, estimated_bytes)
VALUES(strftime('%s','now'), 0, 'INFO', 'trigger_test', 'should_not_exist', 1);
SELECT count(*) FROM logs;
SELECT count(*) FROM logs WHERE target='trigger_test';
"
```

如果前后行数一样，并且 `trigger_test` 是 `0`，说明生效。

### Windows PowerShell 版本

Windows 上路径通常是：

```powershell
$db = Join-Path $env:USERPROFILE ".codex\logs_2.sqlite"
sqlite3 $db "CREATE TRIGGER IF NOT EXISTS block_log_inserts BEFORE INSERT ON logs BEGIN SELECT RAISE(IGNORE); END;"
```

我在远端 Windows 机器上验证过，测试 insert 前后行数不变：

```text
trigger: block_log_inserts
before: 76387
after: 76387
trigger_test_rows: 0
```

### 恢复日志写入

```bash
sqlite3 ~/.codex/logs_2.sqlite "DROP TRIGGER IF EXISTS block_log_inserts;"
```

PowerShell：

```powershell
$db = Join-Path $env:USERPROFILE ".codex\logs_2.sqlite"
sqlite3 $db "DROP TRIGGER IF EXISTS block_log_inserts;"
```

### 顺手压缩旧日志

trigger 只拦新增，不会自动缩小已经膨胀的库。退出 Codex 后再做一次 checkpoint 和 `VACUUM`：

```bash
sqlite3 ~/.codex/logs_2.sqlite "
PRAGMA wal_checkpoint(TRUNCATE);
DELETE FROM logs WHERE level IN ('TRACE','DEBUG');
DELETE FROM logs WHERE level = 'INFO' AND ts < strftime('%s','now','-3 days');
VACUUM;
"
```

如果 Codex 还开着，SQLite 可能会报 `database is locked`。这不是坏事，关掉 Codex 再跑。

### 这个办法的边界

它不是“修复 Codex 日志系统”，只是本机止血。

好处是不用改 Codex，不用等版本发布，也不用写守护脚本。坏处是之后 `logs_2.sqlite` 里不会再有新日志，本地排障能力会下降。需要排障时删掉 trigger，复现问题，再重新加回来。

长期看，正确做法还是 Codex 自己提供日志库 retention 或 max-size 配置。但在那之前，一个 SQLite trigger 已经够用了。
