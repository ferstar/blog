---
title: "再说点梯子的事情"
date: "2022-11-14T00:39:53+08:00"
tags: ['Linux', 'TODO', 'Docker', 'Android']
comments: true
---

被我放弃的甲骨文坡县小机居然坚挺了大半年之久，于是又废物利用，试用了一下最近风头正盛的几个小众的梯子。

从跑带宽测速来排位：Hysteria > tuic > naiveproxy
从抗封锁来排位：naiveproxy > Hysteria/tuic
从性能表现来说：tuic > naiveproxy > Hysteria

总体看未来爬墙梯应该会是 quic 的天下，一众 tcp 方案可休矣

- Hysteria 这玩意其实他一出来我就在用了，目前绝对主力
- tuic
- naiveproxy

配置这玩意其实没什么好讲的，自然 Docker 一把梭哈

这是 naiveproxy + filebrowser 的一个组合

```yml
version: "3"
services:
  caddy:
    restart: unless-stopped
    container_name: caddy
    image: kwaabot/caddy
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - "./naiveproxy:/etc/caddy"        # State data will be stored in this directory
      - "/home/ubuntu/.local/share/caddy:/root/.local/share/caddy"           # Required for tailscale to work
    sysctls:
      - net.ipv4.tcp_congestion_control=bbr
  filebrowser:
    restart: unless-stopped
    container_name: filebrowser
    image: filebrowser/filebrowser
    volumes:
      - "./filebrowser/srv:/srv"        # State data will be stored in this directory
      - "./filebrowser/database.db:/database.db"        # State data will be stored in this directory
      - "./filebrowser/.filebrowser.json:/.filebrowser.json"        # State data will be stored in this directory
      - "/etc/timezone:/etc/timezone:ro"
      - "/etc/localtime:/etc/localtime:ro"
```

```shell
$ cat filebrowser/.filebrowser.json
{
  "port": 80,
  "locale": "zh-cn",
  "baseURL": "",
  "address": "",
  "log": "stdout",
  "database": "/database.db",
  "root": "/srv"
}
$ cat naiveproxy/Caddyfile
{
        order forward_proxy before reverse_proxy
}

:443, play.ferstar.org
tls fer_star@qq.com
route {
        forward_proxy {
                basic_auth username password
                hide_ip
                hide_via
                probe_resistance
        }
        reverse_proxy filebrowser:80
}

```

再来个 hysteria 的

```shell
sudo docker run -td --name hysteria -p 8443:443/udp -v /home/ubuntu/myprojects/hysteria/config.json:/etc/config.json -v /home/ubuntu/.local/share/caddy/certificates/acme-v02.api.letsencrypt.org-directory/:/etc/hysteria/ --sysctl net.ipv4.tcp_congestion_control=bbr --restart unless-stopped tobyxdd/hysteria -config /etc/config.json server --log-level=panic
```

tuic: 

```shell
[Unit]
After=network.target

[Service]
User=tuic
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_NET_RAW
AmbientCapabilities=CAP_NET_BIND_SERVICE CAP_NET_RAW
NoNewPrivileges=true
WorkingDirectory=/etc/tuic
#Environment=HYSTERIA_LOG_LEVEL=info
ExecStart=/usr/local/bin/tuic -c /etc/tuic/config.json
Restart=on-failure
RestartPreventExitStatus=1
RestartSec=5

[Install]
WantedBy=multi-user.target
```



```
# NOTE: I am not responsible for any expired content.
create@2022-11-14T00:39:53+08:00
update@2023-01-04T13:02:53+08:00
comment@https://github.com/ferstar/blog/issues/66
```
