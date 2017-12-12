---
title: "Ubuntu查看crontab运行日志"
date: "2015-09-18T09:12:00+08:00"
tags: ['OTHERS']
comments: 
---


修改rsyslog
`sudo vim /etc/rsyslog.d/50-default.conf`
cron.* /var/log/cron.log #将cron前面的注释符去掉 
重启rsyslog
`sudo service rsyslog restart`
查看crontab日志
`less /var/log/cron.log `
crontab问题定位
查看日志
`/var/log/cron.lo`g 和 `/var/mail/$user`
因为crontab运行日志记录在cron.log，开启sendmail服务会给当前crontab运行属主发送邮件