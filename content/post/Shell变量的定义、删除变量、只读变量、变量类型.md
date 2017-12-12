---
title: "Shell变量的定义、删除变量、只读变量、变量类型"
date: "2016-08-12T09:08:00+08:00"
tags: ['OTHERS']
comments: 
---


via <http://c.biancheng.net/cpp/view/6999.html>

其中使用一个定义过的变量有两种方法:
```
your_name="mozhiyan"
echo $your_name
echo ${your_name}
```
变量名外的花括号可选, 花括号的作用是帮助解释器识别变量的边界, 比如下面这种情况
```
for skill in Ada Coffe Action Java 
do
    echo "I am good at ${skill}Script"
done
```
如果不给skill变量加花括号，写成`echo "I am good at $skillScript"`，解释器就会把`$skillScript`当成一个变量（其值为空），代码执行结果就不是我们期望的样子了。
嗯, 这个坑我也是踩中才觉得蛋疼, 所以有必要记录下
**一定要给所有变量加上花括号，这是个好的编程习惯**
