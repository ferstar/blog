---
date = "2015-08-31T23:13:00+08:00"
title = "实用shell脚本整理（不定期更新）"
tags = ['SHELL', 'LINUX']

---

## 转换时间和unix时间戳
```
# 时间转时间戳
date -d "2015-07-24 12:25:00" +%s
# 时间戳转时间
date -d "@1437711900"
```
<!--more-->

## 分析nginx日志

```
#查看访问地址次数排行
awk -F\" '{print $2}' blog_access.log | awk '{print $2}' | sort | uniq -c | sort -rn
```

## 输出当前目录下各个子目录所使用的空间
```
du -h --max-depth=1
```
## 查找文件内容
```
grep "search" filename

# 从文件内容查找与正则表达式匹配的行：
grep –e “/pattern/” filename

# 查找时不区分大小写：
grep –i "search" filename

# 查找匹配的行数：
grep -c "search" filename

# 从文件内容查找不匹配指定字符串的行：
grep –v "search" filename

# 结合find
find . -name "*.php" | xargs grep "function"
```

## 查看dd命令的进度

`dd if=/dev/zero of=/tmp/zero.img bs=10M count=100000`
想要查看上面的dd命令的执行进度，可以使用下面几种方法：

比如：每5秒输出dd的进度
```
方法一：
watch -n 5 pkill -USR1 ^dd$
方法二：
watch -n 5 killall -USR1 dd
方法三：
while killall -USR1 dd; do sleep 5; done
方法四：
while (ps auxww |grep " dd " |grep -v grep |awk '{print $2}' |while read pid; do kill -USR1 $pid; done) ; do sleep 5; done
上述四种方法中使用三个命令：pkill、killall、kill向dd命令发送SIGUSR1信息，dd命令进程接收到信号之后就打印出自己当前的进度。
```
## 判断远程主机端口是否开启
- TCP端口：
  `nc -w 1 127.0.0.1 9527 && echo true || echo false`
- UDP端口：
  `nc -w 1 -u 127.0.0.1 9527 && echo true || echo false`

## ubuntu删除过期内核方法
ubuntu 的一个让处女座人不舒服的地方就是 每次升级后原来的文件还保留在系统中，不会自动清理，所以对于有洁癖的人来说需要自己清理。
先来看看你的系统中已经存在的内核版本：
`dpkg --get-selections | grep linux`
先别乱删，先看看系统正在运行的是什么版本，当然这个不可以删除的。`uname -r` ，可以看到 `3.2.0-60-generic-pae`，这个就是我的系统目前使用的内核版本。其他的就尽情的删除吧

## git 删除远程分支
`git push origin :branch-name`
冒号前面的空格不能少，原理是把一个空分支push到server上，相当于删除该分支。
## 更改git默认nano编辑器为vim
当然这可以是任意喜欢的编辑器
`git config --global core.editor vim`
## ubuntu 14.04系统设置图标丢失解决方法
`sudo apt-get install ubuntu-desktop`
or
`sudo apt-get install unity-control-center-signon gnome-control-center-unity`
Original Page: <http://askubuntu.com/questions/466720/system-settings-icons-missing-in-14-04>