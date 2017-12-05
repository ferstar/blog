+++
date = "2016-12-28T09:34:00+08:00"
title = "Python 3.x控制台输入密码的方法总结"
tags = ['PYTHON', 'WINDOWS']

+++

昨天撸了个公司OA消息提醒工具, 发现让人在控制台输入密码不给隐藏是一件很羞耻的事情, 于是就诞生了这个需求

> 输入密码时回显*号

Google 大法后, 发现这位仁兄已经提前帮我实现了, 甚是开心

<http://www.programgo.com/article/48653077853/>

原理大概就是`接受一个字符输入后光标立马回退, 显示*号占位, 依次类推`

放码如下:

```python
import msvcrt


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

print("请输入密码：")
pwd = pwd_input()
print("\n密码是：{0}".format(pwd))
input("按回车键退出")
```



Linux下可以用getpass.getpass() 缺点是不回显任何内容, 不知道的还以为没有输入进去呢

所以类似的Linux下可使用termios, 在windows下要用msvcrt代替termios



人生苦短, 必须Python啊!