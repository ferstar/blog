---
date = "2015-08-20T15:52:00+08:00"
title = "Static IP Setup On Arch Linux ARM"
tags = ['OTHERS']

---

[http://archlinuxarm.org/forum/viewtopic.php?f=58&amp;t=8045](http://archlinuxarm.org/forum/viewtopic.php?f=58&amp;t=8045)

Try this, in a chroot (assumes you are root. you can always add sudo to the beginning of each command if you prefer sudo). Note in the below it is eth0.network not eth0-network as stated in your post. Systemd-networkd uses *.network files.

<!--more-->

    nano /etc/systemd/network/eth0.network
    `</pre>

    Then paste this in:

    <pre>`[Match]
    Name=eth0

    [Network]
    Address=192.168.1.8/24
    Gateway=192.168.1.1
    DNS=8.8.8.8
    DNS=8.8.4.4
    `</pre>

    You will then need to disable netcl. To find out what is enabled that is netctl related, run this:

    <pre>`systemctl list-unit-files
    `</pre>

    Once you identify all netctl related stuff. Go through and disable all netctl related stuff. You may have more to disable than just the below:

    <pre>`systemctl disable netctl@eth0.service
    `</pre>

    You will then need systemd-networkd enabled:

    <pre>`systemctl enable systemd-networkd
    