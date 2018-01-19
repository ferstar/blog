---
title: "缩短xfrp断线重连时间"
date: 2018-01-19T15:25:16+08:00
tags: ['LINUX', 'OPENWRT', 'XFRP', 'Python']
comments: true
---

试用一段时间xfrp以后发现这货不是很稳定，容易任性断开，重连的时间不定，可能是秒级，也可能是分钟级甚至小时级，实在不能忍，于是迫切希望能够想个法子缩短这个断线重连的问题。

于是简单想了一个思路：

1. 客户端先检测自己能否正常上网
2. 确定上网OK后，客户端向xfrps的api发起请求查看返回的端口号
3. 根据返回端口号来判断是否重启xfrpc强制重连xfrps服务

但实际发现xfrps自带的api有个bug，即使是客户端断开连接，依然返回原来的端口号，这就比较扯，于是给原项目提了个Issues：[设备断开后调用api依然可以获取remote port](https://github.com/KunTengRom/xfrps/issues/4)但并未收到回复，于是只能自己简单撸个api来完成检测端口的任务。

Python Flask甩起来：

```python
#!/usr/bin/env python3
# coding=utf-8
import json
import socket

import requests
from flask import Flask, jsonify

app = Flask(__name__)


def get_port(sn):
    # 利用原api获取设备占用端口
    url = "http://127.0.0.1:7500/api/port/tcp/getport/" + str(sn)
    try:
        r = requests.request("GET", url)
        result = r.text
        port = json.loads(result).get("port")
        return port
    except:
        pass


def is_used(ip, port):
    is_used = False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((ip, int(port)))
    except socket.error as e:
        #print(e)
        is_used = True
    finally:
        s.close()
    return is_used


@app.route('/api/port/tcp/getport/<sn>')
def is_online(sn):
    port = get_port(sn)
    # 当xfrps端口在线且该端口确实有占用才能确定该客户端在线,其他均为设备断开
    if port:
        if is_used("127.0.0.1", port):
            return jsonify({"code": 0, "msg": "", "port": port}), 200
    return jsonify({"code": 1, "msg": "can not get port by its runid", "port": 0}), 200


if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0')
```

测试

```shell
# 客户端在线,返回端口号
curl http://api.tianbot.com:5000/api/port/tcp/getport/2076932757AC
{
  "code": 0, 
  "msg": "", 
  "port": 62058
}
# 不在线返回0
curl http://api.tianbot.com:5000/api/port/tcp/getport/2076932757A
{
  "code": 1, 
  "msg": "can not get port by its runid", 
  "port": 0
}
```

客户端搞个shell脚本检测

```shell
PROG_NAME="xfrpc"
PROG_UCI_CONF="$PROG_NAME"
PROG_COMMAND=$(which "$PROG_NAME")
JQ_NAME="jq"
JQ_COMMAND=$(which "$JQ_NAME")
PROG_INITD="/etc/init.d/$PROG_NAME"
# 拿到remote server地址
SERVER_ADDR=$($UCI get $PROG_UCI_CONF.common.server_addr)
REMOTE_PORT_API="${SERVER_ADDR}:5000/api/port/tcp/getport"
GENERATE_204="http://g.cn/generate_204"
RUN_ID=$($PROG_COMMAND -r | cut -d ":" -f2)

if [ -z "$JQ_COMMAND" ]; then
    echo "error: $JQ_NAME not found!"
    exit 1
fi

get_remote_port() {
    PORT=$(curl --connect-timeout 3 -m 3 "$REMOTE_PORT_API/$RUN_ID" 2>/dev/null | $JQ_COMMAND '.port') || exit 1
    echo $PORT
}

CODE=$(curl --connect-timeout 3 -m 3 -sk $GENERATE_204 -w '%{http_code}') || exit 1
if [ "$CODE"x = "204"x ]; then
    echo "Network ok, check xfrps remote port..."
    PORT=$(get_remote_port)
    if [ "$PORT"x == "0"x ] || [ $(echo "${PORT}" | grep -E -q '^[0-9]{4,}$') ]; then
        echo "xfrps remote port not available, reconnect..."
        $PROG_INITD restart
    else
        echo "Got remote port:$PORT, do nothing."
    fi
else
    echo "Network down, no need to run xfrpc, stop it."
    $PROG_INITD stop
fi

```

扔crontab任务计划，每五分钟检测一次

```shell
# crontab -e
*/5 * * * * /root/check_xfrpc.sh
```

重启crontab生效

```shell
/etc/init.d/cron restart
```

查看log有无是否调用成功

```shell
# logread | grep check_xfrpc
Fri Jan 19 16:10:01 2018 cron.info crond[2056]: crond: USER root pid 15405 cmd /root/check_xfrpc.sh
```

