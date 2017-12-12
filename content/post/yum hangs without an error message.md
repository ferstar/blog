---
date = "2017-07-06T11:33:00+08:00"
title = "yum命令卡住无响应的解决办法"
tags = ['LINUX', 'YUM', 'CENTOS']

---

一台CentOS服务器的yum无端卡住，Ctrl + C也干不掉，Google了一番找到这个解决方法很管用，记录一下

via: [yum hangs and won't respond](https://superuser.com/questions/384963/yum-hangs-and-wont-respond)

```shell
rm -f /var/lib/rpm/__*
rpm --rebuilddb -v -v   
yum clean all
```

我用这几条命令就OK了，不管用的话继续往下看

---

If that did not work, you can set a debug level, error level and timeout for yum in `/etc/yum.conf`:

```
debuglevel=1
errorlevel=1
timeout=1

```

The timeout is standard 30 seconds. So if a repository does not respond, the error takes 30 seconds to appear. Also try using yum without the plugins (like fastest mirror and priorities) with the option `--noplugins`. Now starting yum again should give you more info faster. Test with:

```
yum --verbose --noplugins info

```

You might get something like this:

```
 Config time: 0.105
 Yum Version: 3.2.22
 Setting up Package Sacks
 Loading mirror speeds from cached hostfile
 * base: mirror.nl.leaseweb.net
 * extras: mirror.nl.leaseweb.net
 * ius: mirrors.ircam.fr
 * rpmforge: mirror.nl.leaseweb.net
 * updates: mirror.nl.leaseweb.net link-to-server-repository/repomd.xml: [Errno 4] IOError: urlopen error (97, 'Address family not supported by protocol') 
 Trying other mirror.

```

This indicates no information can be received from the server. Try the URL that is displayed by yum (indicated above with link-to-server-repository) in your web browser. Copy&paste it from your yum response, not from this post! If you get a list, you know the repository is online.

If you get an error in your browser, try removing that repository from `/etc/yum.repos.d`. Try to fetch the list on your server with wget and paste the URL:

```
wget link-to-server-repository/repomd.xml

```

If this generates a timeout, then there's a problem with your firewall or proxy settings. Try to disable your firewall.

If you are running `csf` (ConfigServer Security and Firewall) and `lfd` you can disable csf with:

```
csf -x

```

Try yum again and if it works, you'll have to reconfigure your `csf`. Enable `csf` again with:

```
csf -e

```

And also check your proxy settings. You can also try to change the https in to http in the .repo files at `/etc/yum.repos.d/`.