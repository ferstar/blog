---
title: "python中使用eval和ast.literal_eval的区别"
date: "2017-07-24T17:41:00+08:00"
tags: ['PYTHON']
comments: true
---


> 转自: [python中使用eval() 和 ast.literal_eval()的区别](http://blog.csdn.net/yisuowushinian/article/details/45644299)

eval函数在python中做数据类型的转换还是很有用的。它的作用就是把数据还原成它本身或者是能够转化成的数据类型。

那么eval和ast.literal_val的区别是什么呢？

eval在做计算前并不知道需要转化的内容是不是合法的（安全的）python数据类型。只是在调用函数的时候去计算。如果被计算的内容不是合法的python类型就会抛出异常。

ast.literal则会判断需要计算的内容计算后是不是合法的python类型，如果是则进行运算，否则就不进行运算。

------------------------------引用自stackoverflow--------------------------------

`datamap = eval(raw_input('Provide some data here: ')` means that you actually evaluate the code before you deem it to be unsafe or not. It evaluates the code as soon as the function is called. See also [the dangers of `eval`](http://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html).

`ast.literal_eval` raises an exception if the input isn't a valid Python datatype, so the code won't be executed if it's not.

Use `ast.literal_eval` whenever you need `eval`. If you have Python expressions as an input that you want to evaluate, you shouldn't (have them).

嗯, 就是建议无脑用`ast.literal_eval`代替`eval`就欧了