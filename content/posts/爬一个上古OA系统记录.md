---
title: "爬一个上古OA系统记录"
slug: "legacy-oa-system-web-scraping-record"
date: "2016-12-23T09:51:00+08:00"
tags: ['OTHERS']
comments: true
---


对, 是的, 就是我司的OA系统, 界面浓浓的上世纪90年代风格, 响应也很慢, 所以一般除了看通知和月底交报表以外几乎不会打开这货, 但是公司通知确实是在这上面分发的, 所以就萌生了写个脚本定时检查通知, 有新通知给我发邮件提醒

也就是一个爬虫的情形, 所以兴高采烈开始用Python撸

## 1. 找登录接口及新消息接口

> 这一步没什么好说的, 用 Chrome 或者 Firefox 的开发者工具 Network 选项找

- 登录接口

  URL: `http://<我司官网url>/logincheck.php` 

  POST 表单内容: `UNAME=用户名&PASSWORD=密码` 

  编码: `charset=gb2312`

  Content-Type: `application/x-www-form-urlencoded` 

  得到cookie格式: response headers 里面 `Set-Cookie`字段值拼起来

- 新消息接口

  URL: `http://<我司官网url>/attachment/new_sms/<userid>.sms?now=<timestamp>` 

  方法: 当然是带着`cookie`的`GET`

  cookie: `PHPSESSID=<模拟登录后拿到>; USER_NAME_COOKIE=<用户名全拼>; OA_USER_ID=<用户名全拼>; SID_<员工编号, 目前三位数, 也是模拟登录后才能拿到>=<这个不知道什么鬼, 反正模拟登录后也能拿到>; UI_COOKIE=0`

  返回值: 新消息为1 / 无新消息为0 <string>

## 2. 拿 cookie

自然是模拟登录才能拿到了,  比较奇葩的是这货只有`curl`才能解析到正确的响应, 其他用`requests`或者`http.client`构造`POST`都无法拿到正确的`cookie`信息, 所以用`pycurl`解决, 放码: 

```python
class Cookies:
    def __init__(self):
        self.url = '我司URL'
        self.username = '用户名'
        self.password = '密码'
        self.status = None  # 存status code, 正确回应是302
        self.cookies = []  # 存各种cookie项
        self.user_id = None

    def _body(self, buf):
        # drop body info
        with open('nul', 'w') as fh:  # 执行perform函数后总是返回烦人的body内容, 我只要header信息, 所以这部分body直接扔掉, linux 系统 nul 要换成 /dev/null
            print(buf, file=fh)

    def _store(self, buf):
        if isinstance(buf, bytes):
            buf = buf.decode('gb2312')
        if buf.startswith('HTTP/1.1'):
            # 获取HTTP Status Code
            self.status = buf.split(' ')[1]
        elif buf.startswith('Set-Cookie:'):
            # 获取 Cookie
            item = buf.strip().split(': ')[-1].split(';')[0]
            self.cookies.append(item)
            if item.startswith('SID_'):
                # 从 Cookie 中截取 user_id
                self.user_id = item.split("=")[0].split('_')[-1]

    def get(self):
        post_data = {
            'UNAME': self.username,
            'PASSWORD': self.password
        }
        # Form data must be provided already urlencoded.
        post_fields = urlencode(post_data)

        c = pycurl.Curl()
        c.setopt(c.URL, 'http://{}/logincheck.php'.format(self.url))
        c.setopt(c.WRITEFUNCTION, self._body)
        # save header info
        c.setopt(c.HEADERFUNCTION, self._store)
        # Sets request method to POST,
        # Content-Type header to application/x-www-form-urlencoded
        # and data to send in request body.
        c.setopt(c.POSTFIELDS, post_fields)
        c.perform()
        c.close()
```

然后就是调用上面这货拿 cookie 了

```python
ck = Cookies()
ck.username = "xxx"
ck.password = "xxx"
ck.get()
cookie = '; '.join(ck.cookies)
# cookie = PHPSESSID=67244df787460089c92def22b99e8cb1; USER_NAME_COOKIE=xxx; OA_USER_ID=xxx; SID_110=32e00603; UI_COOKIE=0
```

## 3. 检测新消息

拿到 cookie 后就可以从消息接口 GET 信息了, `pycurl`还是难用, 这次用自带的`http.client`来做

```python
def check_sms(user_id, cookie):
    conn = http.client.HTTPConnection(host)
    headers = {
        'user-agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
        'accept': "*/*",
        'accept-encoding': "gzip, deflate, sdch",
        'accept-language': "zh-CN,zh;q=0.8",
        'cookie': cookie,
    }

    conn.request("GET", "/attachment/new_sms/{}.sms?now={}".format(user_id, time.time()), headers=headers)

    res = conn.getresponse()
    data = res.read()

    return data.decode("gb2312")
```

返回值为1即有新消息, 0表示没有新消息

> PS: 比较奇葩的是走到这一步忽然才发现这个新消息接口不用cookie也可以查询, 也就是根本匿名都可以访问, 顿时有种吃了苍蝇的感觉, 好比是好不容易撬掉门锁以后忽然发现这门即使上锁也能打开的...

## 4. 有新消息发邮件

这一步写个循环定时检测消息即可

```python
class Mail:
    def __init__(self):
        self.is_send = False
        self.mail_addr = ""
        self.password = ""

    def send(self):
        if not self.is_send:  # 已经发过邮件就不再发送
            # 第三方 SMTP 服务
            mail_host = "smtp.163.com"  # SMTP服务器
            mail_user = " "  # 用户名
            mail_pass = " "  # 密码

            sender = ' '  # 发件人邮箱(最好写全, 不然会失败)
            receivers = [' ']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

            content = 'OA有新消息, 请注意查收'
            title = 'OA有新消息, 请注意查收'  # 邮件主题
            message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
            message['From'] = "{}".format(sender)
            message['To'] = ",".join(receivers)
            message['Subject'] = title

            try:
                smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
                smtpObj.login(mail_user, mail_pass)  # 登录验证
                smtpObj.sendmail(sender, receivers, message.as_string())  # 发送
                print("mail has been send successfully.")
            except smtplib.SMTPException as e:
                print(e)

mail = Mail()
try:
    while 1:
        if check_sms(ck.user_id, cookie) != "0":
            mail.send()  # 有新消息, 发邮件
            mail.is_send = True  # 证明邮件已发
        else:
            mail.is_send = False  # 无新消息, 恢复未发邮件状态
        time.sleep(5 * 60)  # sleep 5min
except KeyboardInterrupt as e:
    print("Ctrl + C pressed, will exit.")
    sys.exit()
```

## 5. pyinstaller 打包

这部分在之前的文章[Python打包工具Pyinstaller使用记录](http://0ne.farbox.com/post/python/pythonda-bao-gong-ju-pyinstallershi-yong-ji-lu)有提到, 照着撸即可

`pyinstaller -F -c check_sms.py`

## 6. 其他包装
把参数写死不是个好事情, 所以又弄了下配置文件, 把用户名/密码/OA地址都写到配置文件里
```python
import configparser


cf = configparser.ConfigParser()
cf.read(conf_file)
if cf.get("main", "send_to"):
        mail.send_to = cf.get("main", "send_to")
else:
    mail.send_to = input("请输入你的邮箱地址: ").strip()
    cf.set("main", "send_to", mail.send_to)
cf.write(open(conf_file, "w"))  # 写入配置文件
...

```

然后发现如果明文保存密码似乎也是不好的, 于是再上个君子协定`base64`

```python
import base64


if cf.get("main", "password"):
        ck.password = base64.b64decode(bytes(cf.get("main", "password"), 'utf8')).decode('utf8')
else:
    print("请输入OA密码: ")
    ck.password = pwd_input()
    cf.set("main", "password", base64.b64encode(bytes(ck.password, 'utf8')).decode('utf8'))
    cf.write(open(conf_file, "w"))

```

## 7. 成果

嗯, 终于可以不用担心那个垃圾的OA漏消息了,我很满意
![](~/微信截图_20161228093640.png)

## 8. 放码

```python
import base64
import configparser
import http.client
import msvcrt
import os
import pycurl
import smtplib
import time
from email.mime.text import MIMEText
from urllib.parse import urlencode


class Cookies:
    def __init__(self):
        self.url = ''
        self.username = ''
        self.password = ''
        self.status = None
        self.cookies = []
        self.user_id = None

    def _body(self, buf):
        # drop body info
        with open('nul', 'w') as fh:
            print(buf, file=fh)

    def _store(self, buf):
        if isinstance(buf, bytes):
            buf = buf.decode('gb2312')
        if buf.startswith('HTTP/1.1'):
            # 获取HTTP Status Code
            self.status = buf.split(' ')[1]
        elif buf.startswith('Set-Cookie:'):
            # 获取 Cookie
            item = buf.strip().split(': ')[-1].split(';')[0]
            self.cookies.append(item)
            if item.startswith('SID_'):
                # 从 Cookie 中截取 user_id
                self.user_id = item.split("=")[0].split('_')[-1]

    def get(self):
        post_data = {
            'UNAME': self.username,
            'PASSWORD': self.password
        }
        # Form data must be provided already urlencoded.
        post_fields = urlencode(post_data)

        c = pycurl.Curl()
        c.setopt(c.URL, 'http://{}/logincheck.php'.format(self.url))
        c.setopt(c.WRITEFUNCTION, self._body)
        # save header info
        c.setopt(c.HEADERFUNCTION, self._store)
        # Sets request method to POST,
        # Content-Type header to application/x-www-form-urlencoded
        # and data to send in request body.
        c.setopt(c.POSTFIELDS, post_fields)
        c.perform()
        c.close()


class Mail:
    def __init__(self):
        self.is_send = False
        self.send_to = ""
        self.host = ""

    def send(self):
        if not self.is_send:
            # 第三方 SMTP 服务
            mail_host = "smtp.126.com"  # SMTP服务器
            mail_user = "xxx"  # 用户名
            mail_pass = "xxx"  # 密码

            sender = 'xxx@126.com'  # 发件人邮箱(最好写全, 不然会失败)
            title = 'OA有新消息, 请注意查收'  # 邮件主题
            content = '点我直达: http://{} \n\n有问题可以在云之家@贾大空'.format(self.host)

            message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
            message['From'] = "{}".format(sender)
            message['To'] = self.send_to
            message['Subject'] = title

            try:
                smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
                smtpObj.login(mail_user, mail_pass)  # 登录验证
                smtpObj.sendmail(sender, self.send_to, message.as_string())  # 发送
                self.is_send = True
                print("检测到新消息, 邮件通知已发送")
            except smtplib.SMTPException:
                print("通知邮件发送失败, 五分钟后再试")


def pwd_input():
    """输入密码替换为星号
    :return: 字符串形式密码
    """
    chars = []
    while True:
        try:
            new_char = msvcrt.getch().decode(encoding="utf-8")
        except:
            return input("你很可能不是在cmd命令行下运行，密码输入将不能隐藏:")
        if new_char in '\r\n':  # 如果是换行，则输入结束
            break
        elif new_char == '\b':  # 如果是退格，则删除密码末尾一位并且删除一个星号
            if chars:
                del chars[-1]
                msvcrt.putch('\b'.encode(encoding='utf-8'))  # 光标回退一格
                msvcrt.putch(' '.encode(encoding='utf-8'))  # 输出一个空格覆盖原来的星号
                msvcrt.putch('\b'.encode(encoding='utf-8'))  # 光标回退一格准备接受新的输入
        else:
            chars.append(new_char)
            msvcrt.putch('*'.encode(encoding='utf-8'))  # 显示为星号
    print('')
    return ''.join(chars)


def check_sms(host, user_id, cookie):
    conn = http.client.HTTPConnection(host)
    headers = {
        'user-agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
        'accept': "*/*",
        'accept-encoding': "gzip, deflate, sdch",
        'accept-language': "zh-CN,zh;q=0.8",
        'cookie': cookie,
    }
    try:
        conn.request("GET", "/attachment/new_sms/{}.sms?now={}".format(user_id, time.time()), headers=headers)
    except ConnectionRefusedError:
        print("查询动作被服务器拒绝")
        return "0"
    except TimeoutError:
        print("服务器超时")
        return "0"
    res = conn.getresponse()
    data = res.read()
    return data.decode("gb2312")


def read_settings(mail, ck, cf):
    if cf.get("main", "send_to"):
        mail.send_to = cf.get("main", "send_to")
    else:
        mail.send_to = input("请输入你的邮箱地址: ").strip()
        cf.set("main", "send_to", mail.send_to)

    if cf.get("main", "host"):
        ck.url = cf.get("main", "host")
    else:
        ck.url = input('请输入OA地址(不要带"http://:"): ').strip()
        cf.set("main", "host", ck.url)

    if cf.get("main", "username"):
        ck.username = cf.get("main", "username")
    else:
        ck.username = input('请输入OA用户名: ').strip()
        cf.set("main", "username", ck.username)

    if cf.get("main", "password"):
        ck.password = base64.b64decode(bytes(cf.get("main", "password"), 'utf8')).decode('utf8')
    else:
        print("请输入OA密码: ")
        ck.password = pwd_input()
        cf.set("main", "password", base64.b64encode(bytes(ck.password, 'utf8')).decode('utf8'))
    cf.write(open(conf_file, "w"))


def main():
    cf = configparser.ConfigParser()
    cf.read(conf_file)
    mail = Mail()
    ck = Cookies()
    read_settings(mail, ck, cf)
    mail.host = ck.url
    while 1:
        ck.get()  # 获取登录信息
        if ck.status == "302":  # 登录成功获得的正确响应
            break
        else:
            print("用户名或密码有误, 请重新输入")
            # 登录失败, 清空用户名/密码, 并要求充填
            cf.set("main", "username", "")
            cf.set("main", "password", "")
            read_settings(mail, ck, cf)

    cookie = '; '.join(ck.cookies)  # 拼接cookie
    print("开始检测, 将此窗口最小化即可")
    try:
        while 1:
            if check_sms(ck.url, ck.user_id, cookie) != "0":
                mail.send()
            else:
                mail.is_send = False
            time.sleep(5 * 60)  # sleep 5min
    except KeyboardInterrupt:
        print("检测到按键中断, 程序将退出")


if __name__ == "__main__":
    conf_file = "oa_check.ini"
    conf_info = """[main]
; OA网址, 注意不需要开头的http://哦
host = xxx.com
username =
password =
; 你要接收提醒的邮箱, 如qq邮箱 hello@qq.com
send_to =
"""
    if not os.path.exists(conf_file):
        with open(conf_file, "w") as fh:
            fh.write(conf_info)
    print("""
 _______________
< OA消息提醒工具 >
 ---------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\\-
                ||----w |
                ||     ||""")
    print("{}  by ferstar".format("\t" * 3))
    print("")
    print("设置好邮箱/用户名/密码后, 如果OA系统有新通知时")
    print("")
    print("你设置的邮箱会收到一封来自xxx@126.com的邮件提醒")
    print("")
    main()
```
