---
title: "Resolve Google Scholar With IPv6 Only"
date: 2018-03-08T09:49:42+08:00
tags: ['LINUX']
comments: true
---

Google Scholar blocked most of DigitalOcean VPS IP(IPv4), so you should 
use IPv6 to access Google Scholar instead.

via: https://github.com/shadowsocks/shadowsocks-libev/issues/113

Here is my solution

> make sure your vps has right ipv6 access
>
> OS: Ubuntu 16.04.3 LTS (GNU/Linux 4.12.2-041202-generic x86_64)
>
> ss version: shadowsocks-libev 3.1.3

- vi /etc/default/shadowsocks-libev

```
...
# add '-6' to resovle hostname to IPv6 address first
DAEMON_ARGS="-u -6" 
...

```

- vi /etc/shadowsocks-libev/config.json

```
...
"dns_ipv6": true
...

```

- vi /etc/hosts

```
...
## Scholar
## type 'host google.com' to get the correct ipv6 address
## for me it's '2607:f8b0:4005:804::200e'
2607:f8b0:4005:804::200e scholar.google.cn
2607:f8b0:4005:804::200e scholar.google.com.hk
2607:f8b0:4005:804::200e scholar.google.com
2607:f8b0:4005:804::200e scholar.l.google.com

```

- `systemctl restart shadowsocks-libev`
