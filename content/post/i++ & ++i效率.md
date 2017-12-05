+++
date = "2015-09-27T21:48:00+08:00"
title = "i++ & ++i效率"
tags = ['PYTHON']

+++

偶然又看到关于`i++ & ++i`哪个运行效率高低的讨论, 发现蛮有趣的, 记录下:
## 举个栗子
```C
for( int i=0; i < MAX_SIZE ; i++)
    {    ...}
```
这种写法常见于各类语法速成书籍中, 循环范围不大的情况下, 效率问题似乎并不需要考虑; 但如果`MAX_SIZE`太大, 效率问题就会比较明显了.
就字面意思而言
- ++i 先将i+1, 然后再使用i的值, 放在循环里会比i++少一个循环 MAX_SIZE
- i++ **先使用i的值, 然后再对i+1**, 放在循环里会比++i多一个循环 MAX_SIZE + 1

因此在迭代的时候, ++i比i++好, 省去了中间生成无名临时对象的构建过程

## 网上流行的经典分析

### 1. 从高级层面上解释

++i 是i=i+1,表达式的值就是i本身
i++ 也是i=i+1,但表达式的值是加1前的副本，由于要先保存副本，因此效率低一些。
对于C/C++内置类型而言，大部分编译器会做优化，因此效率没什么区别。但在自定义类型上，就未必有优化，++i 效率会高一些。

### 2. 从底层汇编来看内置类型
int a,i=0; a=++i;汇编代码如下：
```
int a,i=0;
01221A4E mov dword ptr [i],0
a=++i;
01221A55 mov eax,dword ptr [i]
01221A58 add eax,1
01221A5B mov dword ptr [i],eax
01221A5E mov ecx,dword ptr [i]
01221A61 mov dword ptr [a],ecx
```
int a,i=0; a=i++;汇编代码如下：
``` 
int a,i=0;
009E1A4E mov dword ptr [i],0
a=i++;
009E1A55 mov eax,dword ptr [i]
009E1A58 mov dword ptr [a],eax
009E1A5B mov ecx,dword ptr [i]
009E1A5E add ecx,1
009E1A61 mov dword ptr [i],ecx
```
从上述汇编代码可以看到，对于内置类型，它们的执行数目是一样的，效率没有差别。而自定义类型中由于并不清楚编译器是否针对这一操作做优化, 所以最好是使用++i而不是i++。
### 3. 从重载运算符来看自定义类型
```
Operator Operator::operator++()
{
++value; //内部成员变量
return *this;
}
 
Operator Operator::operator++(int)
{
Operator temp;
temp.value=value; //多了一个保存临时对象的操作
value++;
return temp;
}
```
从上面代码可以看出，后置++多了一个保存临时对象的操作，因此效率自然低一些。
## 总结
对于C/C++内置类型，两者的效率差别不大(编译器会自动优化)；
对于自定义的类而言，++i 的效率更高一些。

## Python怎么处理自增运算的
Python doesn't support ++, but you can do:
`number += 1`
壮哉我大python...