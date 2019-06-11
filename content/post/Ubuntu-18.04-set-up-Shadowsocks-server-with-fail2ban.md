---
title: "Ubuntu 18.04 set up Shadowsocks server with fail2ban"
date: 2018-12-01T13:33:45+08:00
tags: ['LINUX', 'UBUNTU']
comments: true


---

> Here I use Shadowsocks-libev for better performance

# [Shadowsocks-libev](https://github.com/shadowsocks/shadowsocks-libev)

Shadowsocks-libev is written in pure C and depends on libev.

```
# install
sudo apt install shadowsocks-libev
sudo ufw allow 8389

# config
sudo tee /etc/shadowsocks-libev/config.json > /dev/null<<EOF
{
 "server":"0.0.0.0",
 "server_port":8389,
 "local_port":1081,
 "password":"$(openssl rand -base64 12)",
 "timeout":60,
 "method":"chacha20-ietf-poly1305"
}
EOF     

# start
sudo systemctl restart shadowsocks-libev
sudo systemctl start shadowsocks-libev.service
sudo systemctl enable shadowsocks-libev.service

# check
sudo systemctl status shadowsocks-libev.service
```

## Problem

systemctl status shadowsocks-libev.service status shows following error:[2]

> This system doesn’t provide enough entropy to quickly generate high-quality random numbers. The service will not start until enough entropy has been collected.

## Solution

```
sudo apt-get install rng-tools
sudo rngd -r /dev/urandom
```

# [fail2ban](https://github.com/fail2ban/fail2ban)

There are also other options to secure the Shadowsocks Server[3]

But since my server is only uesd by some acquaintances, I just care about brute force password cracking.

## Intro

fail2ban is used to ban IP addresses conducting too many failed login attempts.

How fail2ban works?[4]
fail2ban use date pattern to capture and remove the date from log, and then use failregex to parse the log to get the IP. After that, fail2ban would update the firewall rule to block the IP addresses

## log file

Both Shadowsocks and Shadowsocks-libev output log to /var/log/syslog, Shadowsocks also output some INFO and DEBUG level log to /var/log/shadowsocks.log

Shadowsocks can customize log file location but Shadowsocks-libev cannot[5]

I would use ufw rather than iptables to modify my firewall `sudo vim /etc/fail2ban/jail.local`

```
[DEFAULT]
banaction = ufw
```



## Shadowsocks-libev

### log sample

```
Aug 15 08:59:07 <hostname> ss-server[1382]: 2018-08-15 08:59:07 ERROR: failed to handshake with <HOST>: authentication error
```

### create filter

```
sudo tee /etc/fail2ban/filter.d/shadowsocks-libev.conf > /dev/null <<EOF
[INCLUDES]
before = common.conf

[Definition]
_daemon = ss-server

failregex = ^\w+\s+\d+ \d+:\d+:\d+\s+%(__prefix_line)sERROR:\s+failed to handshake with <HOST>: authentication error$

ignoreregex =

datepattern = %%Y-%%m-%%d %%H:%%M:%%S
EOF
```

**test**
`fail2ban-regex /var/log/syslog /etc/fail2ban/filter.d/shadowsocks-libev.conf --print-all-matched`

### update jail config

```
sudo vim /etc/fail2ban/jail.local
[shadowsocks-libev]
enabled = true
filter = shadowsocks-libev
port = 8839
logpath = /var/log/syslog

maxretry = 3
findtime = 3600
bantime = 3600
```



## start fail2ban

```
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo systemctl status fail2ban
sudo fail2ban-client status shadowsocks
sudo fail2ban-client status shadowsocks-libev
```

# Notes

- use ufw rather than iptables to modify firewall, it would make life easier

  > UFW (Uncomplicated Firewall) is a front-end for iptables and is particularly well-suited for host-based firewalls.<https://help.ubuntu.com/community/Firewall>

- `Can't assign requested address`[11]
  In config file, set the server_ip as 0.0.0.0

# Reference

[1] https://novnan.github.io/Shadowsocks/setup-Shadowsocks-on-ubuntu-1604/

[2] https://www.linuxbabe.com/ubuntu/shadowsocks-libev-proxy-server-ubuntu-16-04-17-10

[3] https://github.com/shadowsocks/shadowsocks/wiki/Securing-Public-Shadowsocks-Server

[4] https://github.com/fail2ban/fail2ban/issues/2201#issuecomment-413155557

[5] https://github.com/shadowsocks/shadowsocks/issues/1242

[6] https://fail2ban.readthedocs.io/en/latest/filters.html

[7] https://www.fail2ban.org/wiki/index.php/MANUAL_0_8#Filters

[8] https://github.com/coleturner/fail2ban-slack-action

[9] https://api.slack.com/methods/chat.postMessage

[10] https://api.slack.com/incoming-webhooks

[11] https://github.com/shadowsocks/shadowsocks/issues/961
