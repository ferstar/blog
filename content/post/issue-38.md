---
title: "dyld: Library not loaded: /usr/local/opt/icu4c/lib/libicui18n.67.dylib"
date: "2021-03-05T02:33:26+08:00"
tags: ['PostgreSQL', 'macOS']
comments: true
---

起pg的时候报了这么个错

```shell
pg_ctl: another server might be running; trying to start server anyway
dyld: Library not loaded: /usr/local/opt/icu4c/lib/libicui18n.67.dylib
  Referenced from: /usr/local/Cellar/postgresql/13.1/bin/postgres
  Reason: image not found
no data was returned by command ""/usr/local/Cellar/postgresql/13.1/bin/postgres" -V"
The program "postgres" is needed by pg_ctl but was not found in the
same directory as "/usr/local/Cellar/postgresql/13.1/bin/pg_ctl".
Check your installation.
```

看样子是`brew`更新把`icu4c`这个包搞挂了, 所以解决也很简单, 卸了重装即可
```shell
brew uninstall --ignore-dependencies icu4c postgresql
brew install postgresql
```



```
# NOTE: I am not responsible for any expired content.
create@2021-03-05T02:33:26+08:00
update@2021-03-05T02:33:36+08:00
comment@https://github.com/ferstar/blog/issues/38
```
