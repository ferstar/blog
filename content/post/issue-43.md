---
title: "关于最近项目持续重构的一点复盘"
date: "2021-07-11T14:46:05+08:00"
tags: ['Python']
comments: true
---

# 关于最近项目持续重构的粗略复盘

> 先抛成果：
>
> |                  | 重构前      | 重构后                                   |
> | ---------------- | ----------- | ---------------------------------------- |
> | Python版本       | 3.6.x       | 3.8.x                                    |
> | Tornado版本      | 4.5.3       | 6.1(latest)                              |
> | DB driver        | momoko      | gino(latest)                             |
> | Code style check | pylint only | multi pre-commit hooks                   |
> | 单元测试         | 无          | 有(基本覆盖基础业务API&主要数据处理流程) |
> | 热重载           | 不支持      | 支持(gunicorn)                           |
> | 项目冷启动速度   | 8~10秒      | <2秒                                      |
> | 类型注释         | 无          | 有(持续完善中)                           |



## 缘起

一般来说，作为业务CRUD仔，其实没有太大的动力对项目进行重构，能跑就对了，要啥自行车，对吧？但是实际上我就是看不惯再加上若干次组员很傻逼的低级错误引发的线上扑街问题以后，重构就变成了一件很必要的事。

## 过程

下定决心重构以后，接下来的事情就是琢磨下怎么做。时间上，肯定是优先响应bug以及新需求，其次抠出点时间来做重构；顺序方面，因为涉及到多人合作，实在不想老在codereview时就一些基本语法、样式之类的臭裹脚布问题扯皮，所以首先从引入`pre-commit hooks`强制规范代码风格做起。

### pre-commit hooks

> 这个还是直接贴配置说的清楚些

```yml
default_stages: [commit]
fail_fast: true

repos:
  - repo: https://github.com/ambv/black  # 自动格式化
    rev: 21.5b2
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.1
    hooks:
      - id: check-added-large-files  # 大的二进制文件提交检查，主要是模型有时候会被别组的同事误提交，导致.git很膨胀
      - id: trailing-whitespace
        stages: [commit]
      - id: end-of-file-fixer
        stages: [commit]
      - id: debug-statements

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v2.17.9
    hooks:
      - id: commitizen  # commit msg规范检查

  - repo: local
    hooks:
      - id: pylint  # 代码静态检查
        name: pylint
        entry: pylint
        language: system
        types: [python]

```

### 单元测试

> 这个没说的，欠的坑要填上，不然不管是新需求还是重构旧代码心里都没谱

1. 核心基础逻辑测试

这部分其实挺糟心的, 莽荒时期的项目, 既然无单元测试, 那必然写的是非常放飞自我, 业务代码/基础逻辑基本一锅粥, 要想舒服顺利地搞单元测试, 服务分层势在必行, 基本上开始大概就分了四层: 核心逻辑/业务逻辑/接口/数据库

2. 通用业务接口测试 `这个优先级比较低`

### DB driver

> 这个巨坑爹，光是把成吨的`yield from`换成`async/await`都够喝一壶

1. 新需求全换`gino`

一个悲伤的事情, 好不容易完成替换半年多以后, SQLAlchemy 这个渣男官宣支持异步了...

2. 旧代码`momoko`替换
3. 删掉`momoko`

### 类型注释

> 切换 DB driver 的过程中就发现很多方法，特别是一些又臭又长的拼裸 SQL 方法，不头铁挨个找线上环境真实环境测试，你根本不知道自己要改的是啥玩意。

1. 新代码复杂逻辑都要求声明类型, 如果费解又做不好抽象, 那必须有 UT
2. 旧代码改造：单元测试铺路，然后补上类型注释

### Python版本升级

> 祖师爷都亲自放话未来Python的重心之一是大幅提升性能，我们又有什么理由不跟一下呢？实际上同等条件，仅升级 Python 到`3.8.x`的性能提升贡献就超过了百分之五十多。

### 优化冷启动速度

> 通过健全代码风格检查规则以及单元测试的保驾护航，我们对项目的架构做了相对更科学的分层处理，优化了超长代码的模块，使得启动时间由`8~10`秒缩短至现在的不到`2`秒

### 热重载

> 这是运维同事提的需求，对于一个活跃开发的分支环境，`CI` 的频繁启停，导致服务不可用的情况时有发生，对业务组的同事非常不友好。关于这部分的折腾，可以看我这里的说明：[https://github.com/ferstar/blog/issues/39](/post/issue-39) 其实就是借助`gunicorn`实现了`HUP signal`的支持。

## 结论

项目运行得更快更稳定，节省大把时间，用来思考人生或者摸鱼？

## 教训

最大的坑点就是换 ORM 么有做好技术选型, 匆匆选择了 gino, 当时哪怕换个 peewee-async 也比 gino 香啊, 何况 SQLAlchemy 这个渣男人家 blog 上早就把异步支持写进了 roadmap, 当然了, 也没有说 gino 就垃圾, 只是我们用的不爽而已, 比如: xxx.gino.xxx() 这种强烈的个人主义设定, 以及屎一样的 join 支持......

> 下一次重构: 干掉 gino 换 SQLAlchemy!



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2021-07-11T14:46:05+08:00
Updated at: 2025-01-12T20:07:46+08:00
Origin issue: https://github.com/ferstar/blog/issues/43
```
