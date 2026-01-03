---
title: "python虚拟环境设置virtualenvwrapper"
slug: "python-virtualenvwrapper-setup-guide"
date: "2016-06-07T11:42:00+08:00"
tags: ['OTHERS']
comments: true
---


神器级应用
文档在这里
<https://virtualenvwrapper.readthedocs.io/en/latest/>
## 简单使用
- 创建虚拟环境管理目录

    ```
    mkdir -p $HOME/.local/virtualenvs
    ```
- 在.bashrc中添加

    ```
    export VIRTUALENV_USE_DISTRIBUTE=1  # 总是使用 pip/distribute
    export WORKON_HOME=$HOME/.local/virtualenvs  # 所有虚拟环境存储的目录
    source $HOME/software/bin/virtualenvwrapper.sh
    export PIP_VIRTUALENV_BASE=$WORKON_HOME
    export PIP_RESPECT_VIRTUALENV=true
    ```

- 所有命令可以查看`virtualenvwrapper --help`输出
