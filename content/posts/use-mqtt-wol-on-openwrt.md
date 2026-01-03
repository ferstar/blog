---
title: "利用MQTT远程唤醒内网电脑"
slug: "remote-wake-on-lan-via-mqtt-openwrt"
date: 2018-08-09T17:53:16+08:00
tags: ['OTHERS']
comments: true
---

偶尔需要远程登录公司电脑处理一些事情，但老是开着机太费电，刚好手上有个VPS，还有个MTK7628方案的一个小路由，又刚好维护着个人订阅号一枚，然后又刚刚好看到度娘提供的天工物接入服务，所以一个点子诞生：给公众号发某个暗号(特殊数字啥的)完成远程开机任务。

所以消息链路是这样的：

0. 确认电脑主板支持wake on lan功能，并且同时在操作系统及BIOS中开启此功能，这是基本前提
1. 如果是Windows8及以上，需要关闭快速启动功能
2. 给公众号发暗号
3. 公众号捕获暗号，给天工物接入服务特定topic发布开机消息
4. 路由器MQTT客户端收到天工物接入服务转发的开机消息
5. 调用etherwake软件唤醒目标计算机

过程中用到的软件/组件：

0. [MQTT Dash](https://play.google.com/store/apps/details?id=net.routix.mqttdash) - 手机端发送消息给MQTT server
1. [WeRoBot](http://werobot.readthedocs.io/zh_CN/latest/) - 一个微信公众号开发框架
2. [天工-物联网平台-物联网云-百度云](https://iot.baidu.com) - 这里被用作MQTT Server
3. [etherwake](https://wiki.openwrt.org/doc/uci/etherwake) - 网络唤醒软件
4. mosquitto-client-nossl - MQTT客户端

天工物接入照着官方文档很好配，配好后写个脚本扔路由里(运行openwrt系统)跑起来

```shell
#!/bin/sh

HOSTNAME=office_pc
HOST=xxx.mqtt.iot.gz.baidubce.com
USER=用户名
PASSWD=天工物接入密钥
TOPIC=wake_on
TARGET='唤醒目标电脑网卡MAC地址'

while :
do
  # 收到一次消息即退出接收，收不到消息就阻塞等待，所以这个死循环并不怎么耗CPU，并不需要设sleep时间
  s=$(/usr/bin/mosquitto_sub -i $HOSTNAME -h $HOST -u $USER -P $PASSWD -t $TOPIC -C 1)
  d=$(date +%Y-%m-%dT%H:%M:%S)
  if [ ${s}x == 'onx' ]; then
    echo "${d} GET ${s} command, will wake on xps"
    /usr/bin/etherwake -i "br-lan" ${TARGET}
  else
    echo "${d} GET ${s} command, do nothing"
  fi
done
```

写个死循环监听消息，用`nohup`方式启动，扔进`/etc/rc.local`里搞定自启动

```shell
/usr/bin/nohup /root/wake_on.sh > /root/wake_on.log &
# 写在exit 0之前
exit 0
```

公众号服务端消息发布脚本

```shell
#!/bin/sh

HOSTNAME=do-vps
HOST=xxx.mqtt.iot.gz.baidubce.com
USER=用户名
PASSWD=天工物接入密钥
TOPIC=wake_on
MSG="on"  # 这个消息内容可以随便定制，与客户端判断逻辑一致即可

/usr/bin/mosquitto_pub -i $HOSTNAME -h $HOST -u $USER -P $PASSWD -t $TOPIC -m $MSG &
```

改可执行权限，直接在WeRoBot中用`subprocess`调用即可

```python
import subprocess

def bash_command(*args):
    lst = ['"{}"'.format(i) for i in args]
    cli = ' '.join(lst)
    proc = subprocess.run(cli, shell=True)
```

最终目标达成，远程开机功能完美实现。

```shell
root@GL-MT300N-V2:~# tail wake_on.log 
2018-08-09T17:48:51 GET on command, will wake on xps
```

数秒后电脑开机，自动启动teamviewer，可以开始愉快的远程工作了~

PS：其实肯定还有别的解决方法，比如利用IFTTT、DDNS啥的，只要稍稍有点码力加折腾精神，很好搞定。
