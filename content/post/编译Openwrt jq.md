---
title: "编译Openwrt jq"
date: "2017-06-20T12:42:00+08:00"
tags: ['OTHERS']
comments: true
---


上文中提到我要在`kk-sp3`上解析json发现自己拿shell正则来人肉挫实在不雅，于是搜了一番轮子，嗯，找到这个神器[jq](https://stedolan.github.io/jq/) 简直相见恨晚

然而在路由器上没有现成的`ipk`供使用, 所以只能自己撸一发了

## 1. 下载 openwrt SDK

`kk-sp3`芯片是`ar71xx`

[OpenWrt-SDK-ar71xx-for-linux-x86_64-gcc-4.8-linaro_uClibc-0.9.33.2.tar.bz2](https://downloads.openwrt.org/barrier_breaker/14.07/ar71xx/generic/OpenWrt-SDK-ar71xx-for-linux-x86_64-gcc-4.8-linaro_uClibc-0.9.33.2.tar.bz2)

解压之

```shell
tar jxf OpenWrt-SDK-ar71xx-for-linux-x86_64-gcc-4.8-linaro_uClibc-0.9.33.2.tar.bz2
mv OpenWrt-SDK-ar71xx-for-linux-x86_64-gcc-4.8-linaro_uClibc-0.9.33.2 sdk
```

## 2. 一些依赖

我用的是`centOS`, 年代久远, 所以需要的依赖基本都满足, 个别不满足的看`error log`也很容易搞定, 这里贴个`ubuntu`的

```shell
apt-get update && apt-get install gcc g++ binutils patch bzip2 flex bison make autoconf gettext texinfo unzip sharutils libncurses5-dev ncurses-term zlib1g-dev gawk git ccache asciidoc
```

## 3. 配置menuconfig

好心人在`github`上共享了一份`openwrt`的`feeds`配置, 其实就是个`makefile`文件, 不客气的收下之

```shell
git clone https://github.com/ferstar/openwrt-myfeeds.git hello
```

把里面的`jq`文件夹复制到`sdk/package`目录下

```shell
cp -r hello/jq sdk/package
```

再把里面的`jq-1.4.tar.gz`复制到`sdk/dl`目录下

```shell
cp hello/jq-1.4.tar.gz sdk/dl
```

进入配置界面

```shell
make menuconfig
```

界面如下

```shell
.config - Linux Kernel Configuration
 qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq
  lqqqqqqqqqqqqqqqqqqqqqq Linux Kernel Configuration qqqqqqqqqqqqqqqqqqqqqqqk
  x  Arrow keys navigate the menu.  <Enter> selects submenus --->.          x  
  x  Highlighted letters are hotkeys.  Pressing <Y> includes, <N> excludes, x  
  x  <M> modularizes features.  Press <Esc><Esc> to exit, <?> for Help, </> x  
  x  for Search.  Legend: [*] built-in  [ ] excluded  <M> module  < >       x  
  x lqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqk x  
  x x    [*] Image configuration  --->                                    x x  
  x x        Libraries  --->                                              x x  
  x x        Utilities  --->                                              x x  
  x mqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqx x  
  tqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqu  
  x        <Select>    < Exit >    < Help >    < Save >    < Load >         x  
  mqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqj  
                                                                               
```

空格选中`jq`,然后`tab`键切到`Save`保存退出

## 4. 编译之

```shell
make package/jq/compile V=99 -j4
```

## 5. ipk在哪?

> ipk在此: sdk/bin/ar71xx/packages
>
> 可能会有一点点编译错误, 不过最终ipk是成功编译完成的, 所以可以无视掉

## 6. 我是好人

嗯, 刚才给的那个`github`repo中已经有我打包好的一个`ipk`安装包

随便怎么样上传到路由器/kk-sp3上就可以安装了

```shell
opkg install jq_1.4-1_ar71xx.ipk
```

## 7. 测试一下

```shell
root@OpenWrt:~# jq . /www/switches.json
{
  "switches": [
    {
      "DisplayName": "Switch 1",
      "ip": "192.168.137.115"
    }
  ]
}
root@OpenWrt:~# jq '.switches[0].ip' /www/switches.json
"192.168.137.115"
root@OpenWrt:~# jq -r '.switches[0].ip' /www/switches.json
192.168.137.115
```

## 8. 一个改IP的脚本

```shell
#!/bin/sh
# 把我扔在cron中就可以了
# crontab -e
# */5 * * * * /root/change_ip.sh
# 五分钟检查一次, 别忘了加执行权限
# by ferstar
PATH=/usr/bin:/sbin:/bin
SW_FILE=/www/switches.json
NOW_IP=$(ifconfig wlan0 | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
OLD_IP=$(jq -r '.switches[0].ip' ${SW_FILE})

if [ ${NOW_IP} != ${OLD_IP} ]; then
    echo "ip changes detected, I'll update the ${SW_FILE}"
    jq --arg v ${NOW_IP} '.switches[0].ip=$v' ${SW_FILE} > /tmp/tmp.json
    mv /tmp/tmp.json ${SW_FILE}
    echo "change ip from ${OLD_IP} to ${NOW_IP}"
else
    echo "nothing to be done"
fi
```

其中`jq --arg v ${NOW_IP} '.switches[0].ip=$v' ${SW_FILE} > /tmp/tmp.json`这一步被坑的有点美, 特别记录下

本来想简单把`${NOW_IP}`变量值传进去, 结果每次都传的是`${NOW_IP}`变量名, 求助`Google`发现人家官网写的很清楚, 传参需要加`--arg`参数, 吐血...

> `--arg name value`:
>
> This option passes a value to the jq program as a predefined variable. If you run jq with `--arg foo bar`, then `$foo` is available in the program and has the value `"bar"`. Note that `value` will be treated as a string, so `--arg foo 123` will bind `$foo` to `"123"`.
>
> Named arguments are also available to the jq program as `$ARGS.named`.

via <https://stedolan.github.io/jq/manual>