+++
date = "2017-07-26T18:03:00+08:00"
title = "fix an anki plugin bugs which was called Syntax Highlighting for Code"
tags = ['ANKI', 'PYTHON']

+++

最近折腾`anki`神器, 发现用来记忆零散知识点非常管用, 于是自己制作了一些`Python`学习过程中的问题卡片, 然而默认模板渲染代码效果很差, 非常不方便, `Google`一番后发现了这个插件[Syntax Highlighting for Code](https://ankiweb.net/shared/info/1463041493), 代码年久失修, 使用过程中有点小毛病, 就顺手修复了下.

主要毛病有两个:

1. 模块导入错误 ImportError: No module named pygments
2. 行号显示/代码居中样式自定义option不起作用

代码及修复细节请移步`gist`: [code_highlight_addon.py](https://gist.github.com/ferstar/61dbec4e74bcc725172ec46e546c65e1)