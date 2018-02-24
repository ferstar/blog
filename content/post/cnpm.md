---
title: "国内优秀npm镜像推荐及使用"
date: 2018-02-24T15:52:27+08:00
tags: ['LINUX', 'NODEJS']
comments: true
---

> 转载自: http://riny.net/2014/cnpm/

`npm`全称`Node Package Manager`，是node.js的模块依赖管理工具。由于`npm`的源在国外，所以国内用户使用起来各种不方便。下面整理出了一部分国内优秀的`npm`镜像资源，国内用户可以选择使用。

## 国内优秀npm镜像

### 淘宝npm镜像

- 搜索地址：<http://npm.taobao.org/>
- registry地址：<http://registry.npm.taobao.org/>

### cnpmjs镜像

- 搜索地址：<http://cnpmjs.org/>
- registry地址：<http://r.cnpmjs.org/>

## 如何使用

有很多方法来配置`npm`的registry地址，下面根据不同情境列出几种比较常用的方法。以淘宝`npm`镜像举例：

### 1.临时使用

```
npm --registry https://registry.npm.taobao.org install express

```

### 2.持久使用

```
npm config set registry https://registry.npm.taobao.org

// 配置后可通过下面方式来验证是否成功
npm config get registry
// 或
npm info express

```

### 3.通过`cnpm`使用

```
npm install -g cnpm --registry=https://registry.npm.taobao.org

// 使用
cnpm install express

```
