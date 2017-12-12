---
title: "Python打包工具Pyinstaller使用记录"
date: "2016-12-21T16:23:00+08:00"
tags: ['OTHERS']
comments: true
---


有时候要把写的一些脚本分发给实验组的同学使用, 所以就需要将其打包成exe可执行文件，这个时候 Pyinstaller 就可以派上用场了(py2exe已死, 勿念)

## 1. 安装Anaconda3 

感慨一下这玩意实在太好用了, 谁用谁知道, 各种依赖分分钟`conda install xxx`搞定

官网: <https://www.continuum.io/downloads>

我用 Python 3 x64 位

## 2. 创建虚拟环境

一路傻瓜next到底安装好Anaconda3后, 随便起一个cmd窗口, 比如我要建一个名为`hello`的虚拟Python运行环境

```powershell
E:\Users>conda create -n hello python=3
Fetching package metadata .........
Solving package specifications: ..........

Package plan for installation in environment E:\Users\ferstar\Anaconda3\envs\hel
lo:

The following NEW packages will be INSTALLED:

    pip:            9.0.1-py35_1
    python:         3.5.2-0
    setuptools:     27.2.0-py35_1
    vs2015_runtime: 14.0.25123-0
    wheel:          0.29.0-py35_0

Proceed ([y]/n)? y

Linking packages ...
[      COMPLETE      ]|##################################################| 100%
#
# To activate this environment, use:
# > activate hello
#
# To deactivate this environment, use:
# > deactivate hello
#
# * for power-users using bash, you must source
#
```

对就这么简单, `activate hello`即可切换到刚建立的`hello`虚拟运行环境 

## 3. 下载upx

这货是给生成的`exe`文件加壳的, 可以有效减小生成二进制文件的大小

基友之家链接: <https://github.com/upx/upx>

下完解压后把`upx.exe`和`upx.1`扔到你要打包的脚本比如`hello.py`同目录下(pyinstaller默认会调用此程序进行加壳)

## 4. 安装及使用

切换到建好的`hello`虚拟运行环境后, 安装`pyinstaller`

```powershell
(hello) E:\Users\hello>pip install pyinstaller
Collecting pyinstaller
Requirement already satisfied: setuptools in e:\users\ferstar\anaconda3\envs\hel
lo\lib\site-packages\setuptools-27.2.0-py3.5.egg (from pyinstaller)
Collecting pefile (from pyinstaller)
Collecting future (from pefile->pyinstaller)
Installing collected packages: future, pefile, pyinstaller
Successfully installed future-0.16.0 pefile-2016.3.28 pyinstaller-3.2
```

举个栗子, 我们要封装的脚本叫`hello.py`, 内容如下

```python
print("hello world!")
input("press enter to quit")
```

装完先用一发`pyinstaller -F -c hello.py`发现报错

```powershell
Traceback (most recent call last):
  File "e:\users\ferstar\anaconda3\envs\hello\lib\runpy.py", line 184, in _run_m
odule_as_main
    "__main__", mod_spec)
  File "e:\users\ferstar\anaconda3\envs\hello\lib\runpy.py", line 85, in _run_co
de
    exec(code, run_globals)
  File "E:\Users\ferstar\Anaconda3\envs\hello\Scripts\pyinstaller.exe\__main__.p
y", line 5, in <module>
  File "e:\users\ferstar\anaconda3\envs\hello\lib\site-packages\PyInstaller\__ma
in__.py", line 21, in <module>
    import PyInstaller.building.build_main
  File "e:\users\ferstar\anaconda3\envs\hello\lib\site-packages\PyInstaller\buil
ding\build_main.py", line 32, in <module>
    from ..depend import bindepend
  File "e:\users\ferstar\anaconda3\envs\hello\lib\site-packages\PyInstaller\depe
nd\bindepend.py", line 38, in <module>
    from ..utils.win32.winmanifest import RT_MANIFEST
  File "e:\users\ferstar\anaconda3\envs\hello\lib\site-packages\PyInstaller\util
s\win32\winmanifest.py", line 97, in <module>
    from PyInstaller.utils.win32 import winresource
  File "e:\users\ferstar\anaconda3\envs\hello\lib\site-packages\PyInstaller\util
s\win32\winresource.py", line 20, in <module>
    import pywintypes
ImportError: No module named 'pywintypes'
```

嗯, 大概是缺`pywin32`这么个东西, Google 后找到替代品 `pypiwin32`装之

```powershell
(hello) E:\Users\hello>pip install pypiwin32
Collecting pypiwin32
  Using cached pypiwin32-219-cp35-none-win_amd64.whl
Installing collected packages: pypiwin32
Successfully installed pypiwin32-219
```

再跑一发`pyinstaller -F -c hello.py`成功, 打包好的`exe`在当前目录下的`dist`目录, 运行看一下效果

```powershell
(hello) E:\Users\hello>dist\hello.exe
hello world!
press enter to quit
```

然后发现生成的`exe`默认图标很丑, 所以换一换, 只需要补上`-i icon.ico`参数即可`icon.ico`就是自定义的图标

再然后听说你担心三脚猫代码被人看穿怎么办? 不用怕, 再补上`--key xxx`参数即可`xxx`可以换为任意字符

其他更过参数欢迎使用`pyinstaller -h`查询

## 5. 部署

> 呃, 其实就是拉到小伙伴的电脑上跑一跑喽

发现报错:
*无法定位程序输入点ucrtbase.terminate于动态链接库api-ms-win-crt-runtime-|1-1-0.dll*

于是又Google之, 发现是微软常用运行库没有安装, 随便搜个合集安装包安装之, 基本都是 VC++ 那些组件

装完后正常运行!