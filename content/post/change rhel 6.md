---
title: "change rhel 6.5 yum to centos"
date: "2016-07-01T11:28:00+08:00"
tags: ['OTHERS']
comments: true
---


```
# 卸载yum
rpm -aq | grep yum|xargs rpm -e --nodeps

# 下载依赖
wget http://mirrors.163.com/centos/6/os/x86_64/Packages/yum-metadata-parser-1.1.2-16.el6.x86_64.rpm
wget http://mirrors.163.com/centos/6/os/x86_64/Packages/yum-3.2.29-73.el6.centos.noarch.rpm
wget http://mirrors.163.com/centos/6/os/x86_64/Packages/yum-plugin-fastestmirror-1.1.30-37.el6.noarch.rpm
wget http://mirrors.163.com/centos/6/os/x86_64/Packages/python-urlgrabber-3.9.1-11.el6.noarch.rpm
wget http://mirrors.163.com/centos/6/os/x86_64/Packages/python-iniparse-0.3.1-2.1.el6.noarch.rpm

# 安装
rpm -ivh python-iniparse-0.3.1-2.1.el6.noarch.rpm
rpm -ivh python-urlgrabber-3.9.1-11.el6.noarch.rpm --force
rpm -ivh yum-metadata-parser-1.1.2-16.el6.x86_64.rpm 
rpm -ivh yum-3.2.29-73.el6.centos.noarch.rpm yum-plugin-fastestmirror-1.1.30-37.el6.noarch.rpm

# 换源
mv /etc/yum.repos.d/rhel-source.repo /etc/yum.repos.d/rhel-source.repo.bak
wget http://mirrors.163.com/.help/CentOS6-Base-163.repo -O /etc/yum.repos.d/CentOS6-Base-163.repo
sed -i "s;\$releasever;6;g" /etc/yum.repos.d/CentOS6-Base-163.repo
yum makecache
```
