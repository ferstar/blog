---
title: "Stopping Codex SQLite Log Growth with a Trigger"
slug: "codex-sqlite-log-trigger"
date: "2026-06-20T16:55:00+08:00"
tags: ['Codex', 'SQLite', 'Logging']
description: "Codex's local SQLite log database can grow too fast; a small BEFORE INSERT trigger blocks new log rows, keeps a restore path, and quickly reduces disk IO and WAL growth."
series: ['AI Coding']
---

> I am not a native English speaker; this article was translated by AI.

Codex recently started storing local logs in `~/.codex/logs_2.sqlite`. On my machine that database had already grown past 1GB. The real problem was not the WAL file itself, but the log table: `TRACE`, `DEBUG`, and `INFO` rows kept going into SQLite, creating unnecessary disk usage and IO.

The public configuration surface is limited here. `RUST_LOG` can reduce verbosity, `log_dir` only controls the plaintext TUI log, and `history.max_bytes` only applies to `history.jsonl`. I could not find a public retention, max-size, or journal-mode option for `logs_2.sqlite`.

So I used SQLite itself as the stopgap.

### Block new log rows with one trigger

```bash
sqlite3 ~/.codex/logs_2.sqlite "CREATE TRIGGER IF NOT EXISTS block_log_inserts BEFORE INSERT ON logs BEGIN SELECT RAISE(IGNORE); END;"
```

The trigger is intentionally blunt: whenever something tries to insert into the `logs` table, SQLite ignores that insert.

Verification is also simple:

```bash
sqlite3 ~/.codex/logs_2.sqlite "
SELECT count(*) FROM logs;
INSERT INTO logs(ts, ts_nanos, level, target, feedback_log_body, estimated_bytes)
VALUES(strftime('%s','now'), 0, 'INFO', 'trigger_test', 'should_not_exist', 1);
SELECT count(*) FROM logs;
SELECT count(*) FROM logs WHERE target='trigger_test';
"
```

If the row count stays the same and `trigger_test` is `0`, the trigger is working.

### Windows PowerShell version

On Windows, the path is usually:

```powershell
$db = Join-Path $env:USERPROFILE ".codex\logs_2.sqlite"
sqlite3 $db "CREATE TRIGGER IF NOT EXISTS block_log_inserts BEFORE INSERT ON logs BEGIN SELECT RAISE(IGNORE); END;"
```

I verified this on a remote Windows machine. The test insert did not change the row count:

```text
trigger: block_log_inserts
before: 76387
after: 76387
trigger_test_rows: 0
```

### Restore log writes

```bash
sqlite3 ~/.codex/logs_2.sqlite "DROP TRIGGER IF EXISTS block_log_inserts;"
```

PowerShell:

```powershell
$db = Join-Path $env:USERPROFILE ".codex\logs_2.sqlite"
sqlite3 $db "DROP TRIGGER IF EXISTS block_log_inserts;"
```

### Compact the old logs too

The trigger only blocks new rows. It does not shrink a database that has already grown. After quitting Codex, run a checkpoint and `VACUUM`:

```bash
sqlite3 ~/.codex/logs_2.sqlite "
PRAGMA wal_checkpoint(TRUNCATE);
DELETE FROM logs WHERE level IN ('TRACE','DEBUG');
DELETE FROM logs WHERE level = 'INFO' AND ts < strftime('%s','now','-3 days');
VACUUM;
"
```

If Codex is still running, SQLite may report `database is locked`. That is expected. Quit Codex and run it again.

### The limit of this trick

This does not fix Codex's logging system. It is just local damage control.

The upside is that it needs no Codex patch, no release wait, and no background cleanup daemon. The downside is that `logs_2.sqlite` will no longer contain new local logs, which makes local debugging weaker. When you need logs, drop the trigger, reproduce the issue, then add the trigger again.

Long term, Codex should expose log database retention or max-size settings. Until then, one SQLite trigger is enough.
