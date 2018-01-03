---
title: "Deploy Xfrp on Openwrt"
date: 2018-01-03T15:53:30+08:00
tags: ['LINUX', 'OPENWRT', 'XFRP']
comments: true
---

原生的frp对路由器来说还是略显笨重，于是有好人用C实现了一遍，叫[xfrps](https://github.com/KunTengRom/xfrps)，对比之下go实现的frp显然臃肿太多，负担不起。

![负载](http://p2.cdn.img9.top/ipfs/QmTkn9DSCbf6Tk5nenGaBon2FTNne8aeL6gcyDcCuMYHYu?2.png)

部署过程中有个坑，xfrpc依赖的libevent2版本太高，路由器固件自带的版本显然没法满足，所以只好自己编译，makefile早有好心人写好，抄抄改改轻松把libevent2版本艹到2.1.6，需要ipk的可以去我的[GitHub-openwrt-libevent21](https://github.com/ferstar/openwrt-libevent21)自取。

附交叉编译ipk简单步骤：

1. 下载对应芯片平台的SDK,我的是联想newifi mini [mt7620a](http://downloads.openwrt.org/barrier_breaker/14.07/ramips/mt7620a/OpenWrt-SDK-ramips-for-linux-x86_64-gcc-4.8-linaro_uClibc-0.9.33.2.tar.bz2)
2. 下载[PandoraBox Toolchain](http://downloads.openwrt.org.cn/PandoraBox/PandoraBox-Toolchain-ralink-for-mipsel_24kec%2Bdsp-gcc-4.8-linaro_uClibc-0.9.33.2.tar.bz2)
3. 配置交叉编译环境变量(假设我将以上SDK及Toolchain都解压到~/pbox目录)

```
PATH=$PATH:~/pbox/toolchain-mipsel_24kec+dsp_gcc-4.8-linaro_uClibc-0.9.33.2/bin
export PATH
STAGING_DIR=~/pbox
export STAGING_DIR
```

4. 将本Repository中的Makefile放到SDK根目录package目录下,如`package/libevent21`
5. 在SDK根目录运行`make package/libevent21/install V=s`
6. 不出意外的话`ipk`会在`bin/ramips/packages/base`目录下
7. 将所需的`ipk`上传到路由器安装即可

PS:安装ipk需要加点东西
```shell
# vi /etc/opkg.conf
arch all 100
arch ralink 200
arch ramips 300
arch ramips_24kec 400
```
