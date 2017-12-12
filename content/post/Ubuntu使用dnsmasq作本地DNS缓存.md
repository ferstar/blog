---
date = "2015-09-17T23:48:00+08:00"
title = "Ubuntu使用dnsmasq作本地DNS缓存"
tags = ['OTHERS']

---

http://mydf.github.io/blog/ubuntu-dnsmasq/
```
sudo apt-get install dnsmasq
sudo vi /etc/NetworkManager/NetworkManager.conf
注释#dns=dnsmasq
sudo vi /etc/dhcp/dhclient.conf
去掉注释prepend domain-name-servers 127.0.0.1;
sudo vi /etc/default/dnsmasq
去掉注释IGNORE_RESOLVCONF=yes
sudo vi /etc/dnsmasq.conf
resolv-file=/etc/resolv.dnsmasq
sudo service dnsmasq restart
sudo service network-manager restart
```