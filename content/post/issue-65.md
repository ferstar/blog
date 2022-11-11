---
title: "黑苹果显示电池建议维修的一个解决方法"
date: "2022-11-11T02:11:54+08:00"
tags: ['macOS']
comments: true
---

装黑苹果用了三年多的小新pro13电池终于不行了，提示“电池建议维修”

![image](https://user-images.githubusercontent.com/2854276/201245551-5ab8aa61-6a5f-4532-999e-d19d070b813c.png)

于是跑Windows下看了一眼电池健康度，已经掉到73%了，于是某宝一百来块购入电池一块，拆机换之，发现原电池已经鼓包，再不换可能就有boom的风险

一顿操作之后，进macOS一看，卧槽居然还提示“电池建议维修”，乱搜一通什么清NVRAM、换SMCBatteryManager驱动等等办法都没效果，忽然想到可能跟电池序列号有关，因为这款机器黑苹果的人很多，也许电池id会在苹果爹地的数据库里有健康度的绑定，所以就尝试修改电池序列号，果然换完就正常了

![image](https://user-images.githubusercontent.com/2854276/201246112-702e1df5-0ea0-4f93-a9a6-83d70eb8f320.png)

下面简单说一下修改电池序列号的方法：

- About This Mac -> System Information -> Power -> Serial Number 记下你现在的电池序列号，小新的话默认应该是`123456789`
- 工具：[MaciASL](https://github.com/acidanthera/MaciASL)
- 挂载EFI分区，打开SSDT-BATS-PRO13.aml文件
- 查找上面记下的序列号`123456789`，替换成任意你喜欢的数字组合，最好保证长度一致
- 改完点保存
- 重启电脑，电池维修的提示就没有了



```
# NOTE: I am not responsible for any expired content.
create@2022-11-11T02:11:54+08:00
update@2022-11-11T02:15:58+08:00
comment@https://github.com/ferstar/blog/issues/65
```
