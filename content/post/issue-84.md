---
title: "How to Fix High CPU load of kwin_x11 when locking or turning off the screen"
date: "2025-01-13T02:01:49+08:00"
tags: ['Linux', 'TODO']
comments: true
---

> TL;DR, use [xsecurelock](https://github.com/google/xsecurelock) instead of the KDE default screenlocker

好像也没什么好说的，这是一个持续了一年的 bug 至今没有修复：https://bugs.kde.org/show_bug.cgi?id=484323

所以只能曲线救国，换一种锁屏方式，即 xsecurelock。只要把 KDE 自带的 锁屏关闭，然后把锁屏快捷键 Meta + L 绑定给 xsecurelock 程序即可。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-13T02:01:49+08:00
Updated at: 2025-01-25T10:03:12+08:00
Origin issue: https://github.com/ferstar/blog/issues/84
```
