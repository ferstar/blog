---
title: "利用Nginx Stream模块把 ssh 藏在 443 端口"
date: "2022-03-13T13:36:29+08:00"
tags: ['Linux', 'Snippet']
comments: true
---

Stream 模块真是牛的不行, 直接放配置

```shell
stream {
    map $ssl_preread_server_name $name {
        mydomain                xtls;
        www.mydomain            http;
        default    ssh;
    }
    # upstream pool
    upstream xtls {
        server localhost:8081;
    }
    upstream http {
        server localhost:8080;
    }
    upstream ssh {
        # 默认 ssh 连接会回落到 default , 然后到本机 22 端口
        server localhost:22;
    }
    server {
        listen 443 so_keepalive=on;
        proxy_pass $name;
        proxy_protocol on;
        ssl_preread on;
    }
}
```

这样做的好处显而易见: ssh 可以经过 443 端口接入, 所以防火墙可以直接屏蔽掉`22`端口, VPS 安全性又能上个台阶, 虽然有`fail2ban`护体但每天 auth.log 里一堆垃圾试探看着也是神烦

当然 由于工作在四层, 你可以有更多的玩法, 比如[搭把梯子](https://github.com/XTLS/Xray-core/discussions/697#discussioncomment-1295912)



```
# NOTE: I am not responsible for any expired content.
create@2022-03-13T13:36:29+08:00
update@2022-03-13T13:36:29+08:00
comment@https://github.com/ferstar/blog/issues/54
```
