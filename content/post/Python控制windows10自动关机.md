+++
date = "2016-09-01T08:51:00+08:00"
title = "Python控制windows10自动关机"
tags = ['OTHERS']

+++

看到`segmentfault`的这个问题, 就花了点时间解决了下, 感叹`python`的轮子真多, 真好用
via <https://segmentfault.com/q/1010000006782616>
以下是我的答案:
```
# coding=utf8
import os
import threading
import time

import pyHook  # 在http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyhook这里下载, 用pip安装
import pythoncom  # 在https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/这里下载安装

last_time = time.time()
flag = False

def shut_down():
    while 1:
        time.sleep(1)
        new_time = time.time()
        # print("new time: {}".format(new_time))
        if new_time - last_time > 1800:  # 30分钟无按键响应就关机
            os.system("shutdown /s /t 1")  # 1秒后关机


def OnMouseEvent(event):
    global last_time
    last_time = time.time()
    # print("old time: {}".format(last_time))
    return True


def OnKeyboardEvent(event):
    global last_time, flag
    if not flag and str(event.Key) == 'Space':  # 按下空格键启动子线程计时
        t = threading.Thread(target=shut_down)
        t.setDaemon(True)  # 设定主线程结束时自动杀掉子线程
        t.start()
        flag = True
    last_time = time.time()
    # print("old time: {}".format(last_time))
    if str(event.Key) == 'Escape':  # 按下ESC退出程序
        exit()
    # print(event.Key)
    return True


def main():
    # create the hook mananger
    hm = pyHook.HookManager()
    # register two callbacks
    hm.MouseAllButtonsDown = OnMouseEvent
    hm.KeyDown = OnKeyboardEvent
    # hook into the mouse and keyboard events
    hm.HookMouse()
    hm.HookKeyboard()
    pythoncom.PumpMessages()


if __name__ == "__main__":
    main()
```
64位windows10, python2.7.11测试通过, 料想python3应该也ok
本来打算定时任务做主线程, 子线程监听鼠标键盘事件, 结果发现这个`pyHook`监听时就阻塞了, 主线程根本起不来, 所以换成主线程监听鼠标事件, 子线程做定时关机逻辑