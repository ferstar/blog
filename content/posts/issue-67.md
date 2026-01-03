---
title: "Ubuntu升级openssl到3.x以后旧应用的处理"
slug: "ubuntu-openssl-3-legacy-apps"
date: "2022-12-09T06:22:11+08:00"
tags: ['Linux']
comments: true
---

> 注意：Manjaro/Arch 里这个包叫 `openssl-1.1` 不小心卸载了的话，得装回来。

最近把Ubuntu更新到22.10，发现openssl已经到3.x了，之前万年1.1.1包居然默认被删掉，这就导致一个问题：之前基于这玩意的很多包如果没有及时做兼容的话，大概率是不能用的，如utools：

```shell
 JavaScript error occurred in the main process
Uncaught Exception:
Error: libcrypto.so.1.1: cannot open shared object file: No such file or directory
    at process.func [as dlopen] (node:electron/js2c/asar_bundle:5:1812)
    at Module._extensions..node (node:internal/modules/cjs/loader:1205:18)
    at Object.func [as .node] (node:electron/js2c/asar_bundle:5:2039)
    at Module.load (node:internal/modules/cjs/loader:988:32)
    at Module._load (node:internal/modules/cjs/loader:829:12)
    at c._load (node:electron/js2c/asar_bundle:5:13343)
    at Module.require (node:internal/modules/cjs/loader:1012:19)
    at require (node:internal/modules/cjs/helpers:102:18)
    at Object.<anonymous> (/opt/uTools/resources/app.asar/node_modules/addon/index.js:18:62)
    at Module._compile (node:internal/modules/cjs/loader:1120:14)
Gtk-Message: 14:00:48.050: Failed to load module "xapp-gtk3-module"
```

本来我是想省事把3.x的so软链接过去，好家伙还不兼容，没办法只好从低版本Ubuntu里拖个1.1.x的openssl应应急了。

```shell
wget http://nz2.archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.16_amd64.deb -O /tmp/ssl.deb
sudo dpkg -i /tmp/ssl.deb
```

搞定



```
# NOTE: I am not responsible for any expired content.
create@2022-12-09T06:22:11+08:00
update@2023-01-24T17:24:02+08:00
comment@https://github.com/ferstar/blog/issues/67
```
