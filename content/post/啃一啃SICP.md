---
date = "2017-08-25T13:13:00+08:00"
title = "啃一啃SICP"
tags = ['SICP', 'LISP', 'SCHEME', 'SUBLIME']
comments = true
---

## 中文or原版?

中文翻译质量一般, 甚至有些练习题连题干都没翻译全, 所以建议慢慢啃原版

这个网站提供制作精美的电子书版本

https://sicpebook.wordpress.com/

我在百度云存了一份, 方便你我他

> 链接: https://pan.baidu.com/s/1geUJpRH 密码: ebck

**How to get Scheme**: via <http://www.gnu.org/software/mit-scheme/>

MIT Scheme用着不是很爽, 于是有了下面的折腾

## 配置sublime3

via <http://www.sublimetext.com/3>

### 注册信息

> v3126、v3124、v3124、v3114、 v3103可用

```shell
—– BEGIN LICENSE —–
Ryan Clark
Single User License
EA7E-812479
2158A7DE B690A7A3 8EC04710 006A5EEB
34E77CA3 9C82C81F 0DB6371B 79704E6F
93F36655 B031503A 03257CCC 01B20F60
D304FA8D B1B4F0AF 8A76C7BA 0FA94D55
56D46BCE 5237A341 CD837F30 4D60772D
349B1179 A996F826 90CDB73C 24D41245
FD032C30 AD5E7241 4EAA66ED 167D91FB
55896B16 EA125C81 F550AF6B A6820916
—— END LICENSE ——
```

### 安装插件

按Ctrl+`调出console，输入

`import urllib.request,os; pf = 'Package Control.sublime-package'; ipp = sublime.installed_packages_path(); urllib.request.install_opener( urllib.request.build_opener( urllib.request.ProxyHandler()) ); open(os.path.join(ipp, pf), 'wb').write(urllib.request.urlopen( 'http://sublime.wbond.net/' + pf.replace(' ','%20')).read())`

重启Sublime Text 3，如果在Perferences->package settings中看到package control这一项，则安装成功。按下Ctrl+Shift+P调出命令面板输入install 调出 Install Package 选项并回车，然后在列表中选中要安装的插件。

### 折腾Scheme插件

via [How To Config SublimeREPL for Scheme](https://notechsolution.github.io/2017/01/03/How-To-Config-SublimeREPL-for-Scheme/)

1. Install LISP scheme interpreter - [SCM](http://people.csail.mit.edu/jaffer/SCM.html). there are several interpreter for scheme - DrRacket, MIT-Scheme. but SCM may be the easist one to integrate with Sublime.
2. Add scm bin folder into your system path. e.g.`set PATH = %PATH%; C:\Program Files (x86)\scm\`

then verify it using command line

```
C:\Users\Administrator>scm
SCM version 5f2, Copyright (C) 1990-2006 Free Software Foundation.
SCM comes with ABSOLUTELY NO WARRANTY; for details type (terms).
This is free software, and you are welcome to redistribute it
under certain conditions; type (terms) for details.
;loading C:\Program Files (x86)\slib\require
;done loading C:\Program Files (x86)\slib\require.scm
;loading C:\Program Files (x86)\scm\Transcen
;done loading C:\Program Files (x86)\scm\Transcen.scm
```

### REPL installation in Sublime Text 3

1. Open the package installation of Sublime Text, if not install yet, plz try Tools -> Install Package Control

2. Install Package “Scheme”

3. Install Package “SublimeREPL”

4. Then, open Preferences -> Browse Packages -> SublimeREPL -> config -> Scheme -> Main.sublime-menu, edit the section with the “id”: “repl_scheme” :

   ```
   "windows": ["scm", "-f", "$file_basename"]}
   ```

5. Save and restart Sublime Text, choose the target file, Open Tools -> Build System, you may find “Scheme” is auto selected. if not, plz choose “Scheme”

6. Try build/run the file via Tools -> Build

7. If you meet error like **“File Not Find”, [“gsi”,”-:d-“,”your-file-path”]**, it may be caused that your configuration are override by Scheme package. then you may go to C:\Users\Adminstrator\AppData\Roaming\Sublime Text 3\Installed Packages, find the scheme package “Scheme.sublime-package”, unzip it and modify the startup command line in the file “Scheme.sublime-build”, change it to :

```
{
    "cmd": ["scm", "-f", "$file"],
    "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
    "selector": "source.scheme"
}
```

## 转向DrRacket

[SICP Support for DrRacket](http://www.neilvandyke.org/racket/sicp/)

总结起来就两步:

1. 下载安装DrRacket

2. ### `#lang planet neil/sicp`

然后就可以愉快的练习`SICP`了

## 习题解答记录

### 1.1

```lisp
10
(+ 5 3 4)
(- 9 1)
(/ 6 2)
(+ (* 2 4) (- 4 6))
(define a 3)
(define b (+ a 1))
(+ a b (* a b))
(= a b)
(if (and (> b a) (< b (* a b)))
b
a)
(cond ((= a 4) 6)
((= b 4) (+ 6 7 a))
(else 25))
(+ 2 (if (> b a) b a))
(* (cond ((> a b) a)
((< a b) b)
(else -1))
(+ a 1))
;; 解释器依次输入即可
```

### 1.2

```lisp
(/ (+ 5 4
         (- 2
            (- 3
               (+ 6
                  (/ 4 5)))))
      (* 3 (- 6 2) (- 2 7)
;; -246.66666666666667e-3 or -37/150
```

### 1.3

```lisp
(define (ex1.3 x y z)
  (sum (sqr (first x y z))
       (sqr (second x y z))))

;; max No.
(define (first x y z)
  (cond ((and (>= x y) (>= x z)) x)
        ((and (>= y x) (>= y z)) y)
        (else z)))

;; second No.
(define (second x y z)
  (cond ((or (and (<= x y) (>= x z))
             (and (>= x y) (<= x z))) x)
        ((or (and (<= y x) (>= y z))
             (and (>= y x) (<= y z))) y)
        (else z)))

;; squares
(define (sqr x)
  (* x x))

;; sum
(define (sum x y)
  (+ x y))

;; test
(ex1.3 3 4 5) 41
```

### 1.4

高阶函数的例子:

在`if`判断部分, 根据`b`的值确定返回`+`还是`-`, 当`b > 0`时返回`+`, 其余返回`-`. 

```lisp
(define (a-plus-abs-a-b a b)
  ((if (> b 0) + -) a b))
;; test
> (a-plus-abs-a-b 4 1)
5
> (a-plus-abs-a-b 4 -1)
5
> (a-plus-abs-a-b 4 -4)
8
```

### 1.5

1. 应用序: 先求值参数而后应用
2. 正则序: 完全展开而后规约

`(define (p) (p))`中不论解释器使用何种求值方式, 调用`(p)`肯定进入无限循环, 函数`p`会不断调用自身

在应用序中所有被传入的实际参数都会被立即求值, 因此执行`(define (test x y) (if (= x 0) 0 y))`时, 实际参数`0`和`p`都会被立即求值, 而对`p`求值则会使采用应用序求值模式的解释器进入无限循环

不过在正则序中, 传入的实际参数只有在用到的时候才会被求值, 类似`Python`中的惰性求值, 所以运行`(test 0 (p)`时, `if`返回值为`#t`, 而这个值又作为`test`函数的值被返回, 即在正则序求值中, 调用`(p)`从始至终都没有被执行, 所以不会产生无限循环, 并且会正常返回`0`, 也就说明该解释器使用的是正则序求值模式

> 形参和实参:
>
> 对于一个函数来说, 他接受的参数的局部名称被称为形式参数. 而电泳函数时传入的表达式, 被称为实际参数.
>
> 通常人们说的参数一般是指形参

### 1.1.7 采用牛顿法求平方根

```lisp
;; 绝对值计算
(define (abs x)
  (if (> x 0) x (- 0 x)))

;; 平均值计算
(define (average x y)
  (/ (+ x y) 2))

;; 取猜测值 (y x / y) / 2
(define (improve guess x)
  (average guess (/ x guess)))

;; 结果是否足够好?
;; 猜测值平方后误差小于 0.001 即可认为足够好, 返回真
(define (good-enough? guess x)
  (< (abs (- (square guess) x)) 0.001))

;; 求平方
(define (square x) (* x x))

;; 求平方根(迭代)
(define (sqrt-iter guess x)
  (if (good-enough? guess x)
      guess
      (sqrt-iter (improve guess x) x)))

;; partial func(给定初始值为1.0)
;; MIT Scheme区分精确的整数和十进制数值, 两个整数的商是一个有理式而不是十进制数
(define (sqrt x)
  (sqrt-iter 1.0 x))

;; test
> (sqrt 16)
4.000000636692939
> (sqrt 128)
11.313708502161349
> (sqrt 256)
16.00000352670594
```

### 1.6

```lisp
;; Alyssa的new-if定义
(define (new-if predicate then-clause else-clause)
    (cond (predicate then-clause)
          (else else-clause)))

;; 重写求平方根过程
(define (sqrt-iter guess x)
    (new-if (good-enough? guess x)
            guess
            (sqrt-iter (improve guess x) x)))

;; 这里可能碰到如下错误
;; define-values: assignment disallowed; cannot re-define a constant constant: sqrt-iter
;; 解决方法 Choose Language --> uncheck Enforce constant definitions.
```

![微信截图_20170825141550](http://7xivdp.com1.z0.glb.clouddn.com/png/2017/8/0dcfe8c59dfe42ca08ae8b2d945c9447.png/xyz)

重写`sqrt`后运行会报错:

```shell
The evaluation thread is no longer running, so no evaluation can take place until the next execution.

The program ran out of memory.
```

出错原因就在新定义的`new-if`函数只是一个普通函数, 根据解释器使用的应用序求值规则, 每个函数的实际参数在传入的时候都会被求值, 所以调用`new-if`函数时, 不论条件是真是假, 两个分支都会执行求值, 所以很快会突破解释器最大递归深度, 报OOM错误

### 1.7

```lisp
;; 对于特别小的数, sqrt函数并不能计算出正确的答案, 对于特别大的数, sqrt会陷入死循环

;; 绝对值计算
(define (abs x)
  (if (> x 0) x (- x)))

;; 平均值计算
(define (average x y)
  (/ (+ x y) 2))

;; 取猜测值 (y x / y) / 2
(define (improve guess x)
  (average guess (/ x guess)))

;; 结果是否足够好?
;; 下次猜测值变化低于百分之一时认为足够好, 返回真
(define (good-enough? old new)
    (> 0.01
       (/ (abs (- new old)) old)))

;; 求平方
(define (square x) (* x x))

;; 求平方根(迭代)
(define (sqrt-iter guess x)
  (if (good-enough? guess (improve guess x))
      (improve guess x)
      (sqrt-iter (improve guess x) x)))

;; partial func(给定初始值为1.0)
;; MIT Scheme区分精确的整数和十进制数值, 两个整数的商是一个有理式而不是十进制数
(define (sqrt x)
  (sqrt-iter 1.0 x))
```

### 1.8

只需要重写`improve`函数即可

```lisp
;; 其中guess相当于近似值公式中的y
(define (improve guess x)
    (/ (+ (/ x (square guess)) (* 2 guess)) 3))

;; 其他判断都不需要改, sqrt已经成了求立方根的函数
> (sqrt 8)
2.000004911675504
> (sqrt 27)
3.0000005410641766
> (sqrt (* 8 8 8))
8.0005181503155
```

### 1.1.8 内部定义和块结构

```lisp
;; 过程抽象为黑盒操作
;; 外部调用只关心sqrt即可
;; 块结构思想

(define (sqrt x)
    (define (good-enough? old new)
      (> 0.01
         (/ (abs (- new old)) old)))
    (define (improve guess x)
      (average guess (/ x guess)))
    (define (sqrt-iter guess x)
      (if (good-enough? guess (improve guess x))
          (improve guess x)
          (sqrt-iter (improve guess x) x)))
    (sqrt-iter 1.0 x))

;; test
> (sqrt 9)
3.00009155413138
```

### 1.2.1 线性的递归和迭代

> 若这个函数在**尾**位置调用本身（或是一个**尾**调用本身的其他函数等等），则称这种情况为**尾递归**，是**递归**的一种特殊情形。 **尾**调用不一定是**递归**调用，但是**尾递归**特别有用，也比较容易实现。 **尾**调用的重要性在于它可以不在调用栈上面添加一个新的堆栈帧——而是更新它，如同迭代一般。
>
> via [尾调用- 维基百科，自由的百科全书](https://www.google.com.hk/url?sa=t&rct=j&q=&esrc=s&source=web&cd=2&cad=rja&uact=8&ved=0ahUKEwiW6Ivo8fHVAhUE2WMKHUXWDPUQFggoMAE&url=https%3A%2F%2Fzh.wikipedia.org%2Fzh-hans%2F%25E5%25B0%25BE%25E8%25B0%2583%25E7%2594%25A8&usg=AFQjCNF0r7nIoHwoQOH1yqSWtk-TDDSX1w)

```lisp
;; 阶乘
;; fact(n) = n * fact(n - 1)
;; 线性递归过程
(define (factorial x)
    (if (= x 1)
        1
        (* x (factorial (- x 1)))))

;; 重构 1
;; fact(n) = 1 * 2 * 3 ... * (n - 1) * n
;; product <-- counter * product
;; counter <-- counter + 1
;; 线性迭代过程
(define (factorial x)
    (define (fact-iter product counter max-count)
      (if (> counter max-count)
          product
          (fact-iter (* counter product)
                     (+ counter 1)
                     max-count)))
    (fact-iter 1 1 x))

;; 重构 2
;; fact(n) = n * (n - 1) * ... * 3 * 2 * 1
;; p初始值为1, 首次迭代保存n, 第二次迭代保存n * (n - 1), 直到n = 1, 此时p即n!
(define (factorial n)
    (define (fact-iter p n)
      (if (= n 1)
          p
          (fact-iter (* p n) (- n 1))))
    (fact-iter 1 n))
```

### 1.9

```lisp
;; 线性递归过程
(define (plus a b)
    (if (= a 0)
        b
        (inc (plus (dec a) b))))
;; test
> (plus 4 5)
(inc (plus 3 5))
(inc (inc (plus 2 5)))
(inc (inc (inc (plus 1 5))))
(inc (inc (inc (inc (plus 0 5)))))
(inc (inc (inc (inc 5))))
(inc (inc (inc 6)))
(inc (inc 7))
(inc 8)
9
;; 从计算过程明显可以看到伸展和收缩两个阶段, 且伸展阶段所需要的额外存储量和计算所需的步数都与参数a正相关
;; 是一个线性递归计算过程(recursive)

;; 线性迭代过程
(define (plus a b)
    (if (= a 0)
        b
        (plus (dec a) (inc b))))

;; test
> (plus 4 5)
(plus 3 6)
(plus 2 7)
(plus 1 8)
(plus 0 9)
9
;; 计算过程仅适用敞亮存储空间, 且计算步骤与参数a正相关, 说明是一个线性迭代计算过程(iterative)
```

### 1.10

```lisp
(define (A x y)
    (cond ((= y 0) 0)
          ((= x 0) (* 2 y))
          ((= y 1) 2)
          (else (A (- x 1) (A x (- y 1))))))
```

见 [http://sicp.readthedocs.io/en/latest/chp1/10.html](http://sicp.readthedocs.io/en/latest/chp1/10.html)

### 1.2.2 树形递归

```lisp
;; 斐波那契数列
;; 树形递归
(define (fib n)
    (cond ((= n 0) 0)
          ((= n 1) 1)
          (else (+ (fib (- n 1))
                   (fib (- n 2))))))

;; 线性迭代
(define (fib n)
    (define (fib-iter a b count)
      (if (= count 0)
          a
          (fib-iter (+ a b) a (- count 1))))
    (fib-iter 0 1 n))
```

### 换零钱方式的统计

```lisp
;; 兑换零钱方法
(define (count-change amount) (cc amount 5))

;; 可用的硬币种数作为输入, 返回第一种硬币币值(从大到小排列)
(define (first-denomination kinds-of-coins)
  (cond ((= kinds-of-coins 1) 1)
        ((= kinds-of-coins 2) 5)
        ((= kinds-of-coins 3) 10)
        ((= kinds-of-coins 4) 25)
        ((= kinds-of-coins 5) 50)))

;; 计算
(define (cc amount kinds-of-coins)
  (cond ((= amount 0) 1)
        ((or (< amount 0) (= kinds-of-coins 0)) 0)
        (else (+ (cc amount
                     (- kinds-of-coins 1))
                 (cc (- amount
                        (first-denomination kinds-of-coins))
                     kinds-of-coins)))))

;; test
> (count-change 100)
292
```

### 1.11

```lisp
;; 线性递归
(define (f n)
  (if (< n 3)
      n
      (+ (f (- n 1))
         (f (- n 2))
         (f (- n 3)))))

;; 线性迭代
;; 初始条件: f(0) = 0, f(1) = 1, f(2) = 2
;; i = (n - 1): f(n - 3) = a, f(n - 2) = b, f(n - 1) = c
;; i = n:       f(n - 2) = b, f(n - 1) = c, f(n) = 3a + 2b + c
(define (f n) (f-iter 0 1 2 n))
(define (f-iter a b c n)
    (cond ((< n 0) n)  ; 负数
          ((= n 0) a)
          ((= n 1) b)
          ((= n 2) c)
          (else (f-iter b
                        c
                        (+ (* a 3) (* b 2) c)
                        (- n 1)))))

;; test
> (f -1)
-1
> (f 0)
0
> (f 1)
1
> (f 2)
2
> (f 3)
4
> (f 100)  ; 线性递归会卡死
11937765839880230562825561449279733086
```

### 1.12 帕斯卡三角形

中文版翻译有误, 应该是给出帕斯卡三角形任意元素的计算方法

```shell
row:
0        1
1       1 1
2      1 2 1
3     1 3 3 1
4    1 4 6 4 1
5   . . . . . .
col: 0 1 2 3 4
```

如果使用p(r, c)来代表r行c列上元素的值, 可以得出三个性质:

1. p(r, c) = p(r - 1, c - 1) + p(r -1, c) 即每个元素的值都由左上和右上元素的和组成
2. p(r, 0) or p(x, x) = 1 即最左边元素(c = 0)或最右边元素(r = c)值为1
3. 列数不能多于行数

```lisp
(define (pascal row col)
    (cond ((< row col) (display "invalid row col values"))
          ((or (= col 0) (= row col)) 1)
          (else (+ (pascal (- row 1) (- col 1))
                   (pascal (- row 1) col)))))
```

### 1.13 原题翻译有误, 需要看英文原版

![微信截图_20170827172527](http://7xivdp.com1.z0.glb.clouddn.com/png/2017/8/3ef5b133b00aef6adfb60e74d7f5a73a.png/xyz)

这个原题翻译有问题, 需要看英文原版

### 1.14 增长的阶

> 绘制(count-change 11)在展开时的过程, 只手撸了部分...

![微信图片_20170905114253](http://7xivdp.com1.z0.glb.clouddn.com/jpg/2017/9/43c93eba6fcc96cc9bc9212f1b1f333a.jpg/xyz)

