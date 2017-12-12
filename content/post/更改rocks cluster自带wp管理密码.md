---
date = "2016-09-28T08:51:00+08:00"
title = "更改rocks cluster自带wordpress管理密码"
tags = ['OTHERS']
---

安装这个集群系统后默认是自带了这么个东西, 当然要利用起来, 然而发现貌似超管密码不知道, 查官方文档似乎有人问但鲜有人回答的. 所以只能自己撸了, 思路就是找个数据库管理软件连上集群自带MySQL数据库wordpress, 修改管理员admin的密码即可

### 1. 找wordpress配置文件得到数据库配置参数
```
# 集群上这个文件的位置在/var/www/html/wordpress/wp-config.php
// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define('DB_NAME', 'wordpress');

/** MySQL database username */
define('DB_USER', 'wordpress');

/** MySQL database password */
define('DB_PASSWORD','QqgsNY9lJ4IvqN7n');

/** MySQL hostname */
define('DB_HOST', 'localhost:/var/opt/rocks/mysql/mysql.sock');

/** Database Charset to use in creating database tables. */
define('DB_CHARSET', 'utf8');

/** The Database Collate type. Don't change this if in doubt. */
define('DB_COLLATE', '');

```

### 2. 拿到数据库密码后, 找个数据库管理软件
> 当然你要是用命令行撸那也是可以, 跪拜大神! 我等懒人还是用现成的工具比较合适
我用的软件叫`Navicat Premium`, 用14天免费试用版即可
安装完成后新建一个MySQL连接, 因为集群MySQL默认禁止非本机访问, 所以用ssh隧道方式连接
```
[常规]
    连接名:    cluster
    主机名:    localhost
    端口:     40000
    用户名:    wordpress
    密码:     QqgsNY9lJ4IvqN7n
[SSH]
...
都是ssh的套路
...
```
连接成功后数据库长这样

![](~/09-56-37.jpg)
在<http://pajhome.org.uk/crypt/md5/>这个网站转换一下你需要更改的密码, 将加密后的字符串填写到user_pass这一栏即可
