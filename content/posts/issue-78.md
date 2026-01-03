---
title: "信创之从PostgreSQL到GaussDB"
slug: "migrate-postgresql-gaussdb"
date: "2023-06-15T06:19:44+08:00"
tags: ['Linux', 'Python', 'PostgreSQL']
comments: true
---

> 信创是个啥玩意具体我懒得说了，简单记录下作为中年 CRUD 仔给 Web 后端换 DB 这件事。

情况大概是这样：

我们 ORM 是 [Gino](https://snyk.io/advisor/python/gino)

然后 Gino 依赖 [asyncpg](https://github.com/MagicStack/asyncpg) 来链接 PostgreSQL，换 GaussDB 的话，由于这玩意是华为从 PostgreSQL 一个古早版本 9.2.4 一通魔改糊起来的，一些特性并不支持，所以这一步就掉坑了：

```shell
    return await self._protocol.query(query, timeout)
  File "asyncpg/protocol/protocol.pyx", line 338, in query
asyncpg.exceptions.FeatureNotSupportedError: UNLISTEN statement is not yet supported.
```

查了下华为云的说明：

https://support.huaweicloud.com/intl/en-us/sqlreference-dws/dws_06_0006.html

嗯，发现不支持 notification 相关特性，那么看来要小改下 asyncpg，见：

https://github.com/ferstar/asyncpg/commit/0be6023443346213a26795a27ef3add7abc79aea

让 asyncpg 识别到 GaussDB 以后关几个 feature 即可，这里的 server_settings 可以通过初始化 DB Pool 的时候传过去。

我们通过 [alembic](https://alembic.sqlalchemy.org/) 来做 DB migration，这个环节也出现了类似的问题，就是人家不认这个 GaussDB，解决也简单：改到让他认。

见：https://github.com/sqlalchemy/sqlalchemy/commit/3a0794ce455201a219a5e8491a9c346d69558ad9

然后正常连接是没有问题了，但跑到一些 GaussDB 不支持的迁移脚本时就又扑街：项目用到了 gin 的 extension，看一时半会估计是不太会兼容了，所以么办法只能改写用普通索引。

接下来，项目初始化、DB migration都顺利完成，于是就跑了一发单元测试，再次被打脸：

```shell
ProgrammingError: syntax error at or near "ON  CONFLICT ("
```

也就是说`UPDATE ... ON CONFLICT ... DO ...`这种也是不支持，要改也简单：先查冲突，然后再更新。

一通操作后，项目总算正常运行。后续有几个需要注意的问题：

1. 代码要考虑兼容性：从base version来看，横跨了好几个大版本，基本上告别 PostgreSQL 新特性
2. DB 相关组件也要考虑兼容性，自己订制魔改的部分，几乎不太可能被主线合并
3. 组员代码审核：需要维护一个lint机制来自动检测组员提交的 DB 相关代码的兼容性



```
# NOTE: I am not responsible for any expired content.
create@2023-06-15T06:19:44+08:00
update@2023-06-15T06:19:44+08:00
comment@https://github.com/ferstar/blog/issues/78
```
