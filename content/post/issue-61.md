---
title: "Fcitx不停往xxxtmp.log写入日志的治标方法"
date: "2022-05-25T08:09:52+08:00"
tags: ['Linux']
comments: true
---

> 偶然发现`/tmp/xxxtmp.log`会不停的写入一些日志，于是就想搞清楚是谁干的

用*auditctl*监听一下文件状态： https://serverfault.com/a/320718 发现是`Fcitx`干的

日志大概是这样子

```shell
time->Tue May 24 14:33:12 2022
type=PROCTITLE msg=audit(1653373992.503:379): proctitle="fcitx"
type=PATH msg=audit(1653373992.503:379): item=1 name="/tmp/xxxtmp.log" inode=4469 dev=00:23 mode=0100644 ouid=1000 ogid=1001 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 cap_fe=0 cap_fver=0 cap_frootid=0
type=PATH msg=audit(1653373992.503:379): item=0 name="/tmp/" inode=1 dev=00:23 mode=041777 ouid=0 ogid=0 rdev=00:00 nametype=PARENT cap_fp=0 cap_fi=0 cap_fe=0 cap_fver=0 cap_frootid=0
type=CWD msg=audit(1653373992.503:379): cwd="/dev/mqueue"
type=SYSCALL msg=audit(1653373992.503:379): arch=c000003e syscall=257 success=yes exit=15 a0=ffffff9c a1=7f0bd1206b4b a2=442 a3=1b6 items=2 ppid=1 pid=1720 auid=1000 uid=1000 gid=1001 euid=1000 suid=1000 fsuid=1000 egid=1001 sgid=1001 fsgid=1001 tty=(none) ses=1 comm="fcitx" exe="/usr/bin/fcitx" subj==unconfined key=(null)
```

翻了下GitHub发现是陈年老bug，治本是不太可能了，只能治标：把这玩意输出重定向到宇宙黑洞：`/dev/null`

说干就干，先删源文件：`rm /tmp/xxxtmp.log`

然后软链接到黑洞：`ln -s /dev/null /tmp/xxxtmp.log`

大功告成！等等，这玩意下次重启还会恢复原样，当然可以搞个启动脚本简单处理，但是本着逼格无限的折腾精神，我找到了`logrotate`：定时根据定义配置来rotate指定的文件，还可以定义post hooks命令，就是你了杰尼龟：

```shell cat /etc/logrotate.d/xxxtmp
/tmp/xxxtmp.log {
        su ferstar ferstar
        daily
        nocreate
        rotate 0
        missingok
        size 1k
        postrotate
                ln -s /dev/null /tmp/xxxtmp.log
        endscript
}
```

嗯，就这么几行搞定，你fcitx dbus爱写入啥垃圾无所谓了，眼不见心不烦



```
# NOTE: I am not responsible for any expired content.
create@2022-05-25T08:09:52+08:00
update@2022-05-25T08:09:52+08:00
comment@https://github.com/ferstar/blog/issues/61
```
