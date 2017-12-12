---
date = "2013-10-26T13:38:18+08:00"
title = "openwrt中把wan转为lan的设置"
tags = ['OPENWRT', 'LINUX']

---

买路由中奖，无线信号渣到爆胎，无奈只好拿来当交换机使了，为了不浪费wan口，需要把他搞成lan口。下面三个链接：

[http://wiki.openwrt.org/doc/recipes/bridgedap](http://wiki.openwrt.org/doc/recipes/bridgedap)

**[https://forum.openwrt.org/viewtopic.php?pid=118095#p118095](https://forum.openwrt.org/viewtopic.php?pid=118095#p118095)**

[http://qing.blog.sina.com.cn/tj/6e2c147f330021ef.html](http://qing.blog.sina.com.cn/tj/6e2c147f330021ef.html)

说的是两种方案，一是把LAN的interface eth0.1和WAN的interface eth0.2进行桥接，但在HG255D上失败，WAN口无法获取上级路由ip地址；二是通过划分vlan来实现，<span style="color: #ff9900;">前提是你需要刷带有VLAN功能的OP固件</span>，据说比桥接方式性能更好，事实上HG255D只有这种方式有效，路由缺省network配置信息如下：

config 'interface' 'loopback'
option 'ifname' 'lo'
option 'proto' 'static'
option 'ipaddr' '127.0.0.1'
option 'netmask' '255.0.0.0'

config 'interface' 'lan'
option 'ifname' 'eth0.1'
option 'type' 'bridge'
option 'proto' 'static'
option 'ipaddr' '192.168.1.1'
option 'netmask' '255.255.255.0'
option 'macaddr' '00:0c:43:30:52:77'

<span style="color: #ff0000;">config 'interface' 'wan'</span>
<span style="color: #ff0000;"> option 'ifname' 'eth0.2'</span>
<span style="color: #ff0000;"> option 'proto' 'dhcp'</span>
<span style="color: #ff0000;"> option 'macaddr' '11:1c:43:31:52:74'</span>

config 'switch'
option 'name' 'rt305x'
option 'reset' '1'
option 'enable_vlan' '1'

config 'switch_vlan'
option 'device' 'rt305x'
option 'vlan' '1'
<span style="color: #00ff00;">option 'ports' '1 2 3 4 5 6t'</span>

<span style="color: #ff0000;">config 'switch_vlan'</span>
<span style="color: #ff0000;"> option 'device' 'rt305x'</span>
<span style="color: #ff0000;"> option 'vlan' '2'</span>
<span style="color: #ff0000;"> option 'ports' '0 6t'</span>

需要修改的地方有三处，红色部分删掉，绿色部分改为option 'ports' '0 1 2 3 4 5 6‘即可。

PS：此方法其实不需要关dnsmasq，dhcp，虽然建议关闭，但实际上关不关都无所谓，我没发现有什么影响。另外有网友提到照这样设置后无法进入路由web设置界面，其实是可以进去的，网卡手动设置ip地址即可，192.168.1.xxx的形式。

over
