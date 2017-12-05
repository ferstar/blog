+++
date = "2015-12-02T19:22:44+08:00"
title = "利用vsftp搭建ftp服务器(匿名可上传)"
tags = ['OTHERS']

+++
## 配置文件
`cat /etc/vsftpd/vsftpd.conf | grep -v ^#`
```shell
anonymous_enable=YES    # 使能匿名
local_enable=YES
write_enable=YES
local_umask=022    # 本地用户的umask值
anon_upload_enable=YES    # 使匿名用户可上传
anon_mkdir_write_enable=YES    # 匿名用户可以对目录进行写操作
anon_root=/home/ftp    # 匿名用户home目录
anon_other_write_enable=YES    # 赋予匿名用户更多权限, 如删除重命名文件/夹的能力
anon_umask=022    # 匿名用户的umask值
dirmessage_enable=YES
xferlog_enable=YES
connect_from_port_20=YES
xferlog_std_format=YES
idle_session_timeout=600    # 空闲时间
data_connection_timeout=120    # 超时时间
ftpd_banner=Welcome to TARSBOT's FTP server!
listen=YES
listen_ipv6=NO
pam_service_name=vsftpd
userlist_enable=YES
tcp_wrappers=YES
use_localtime=YES    # 使用本地时间代替UTC
```

## 使用
重启服务
`service vsftpd restart`

关闭selinux服务

## 	问题记录

- 主要记录下匿名用户上传文件无法下载的问题
默认配置文件中只有`local_umask=022`的选项, 这也是一般unix系统默认的umask值, 他决定了用户新建文件/夹的权限. 默认文件权限是666, 文件夹是777, 减去umask值即默认权限, 文件644/文件夹755. 实际测试发现匿名用户上传的文件权限变成了600, 也就是说其他群组用户是不具备任何权限的, 怪不得无法下载, 同时也得出默认vsftpd服务对匿名用户的umask值是066, 略狠, 所以为了让匿名用户上传的文件可被下载, 我们需要修改匿名用户的umask值, 在vsftp中控制此项的设置为`anon_umask=022`, 重启服务后即可发现匿名用户可以正常上传下载文件了