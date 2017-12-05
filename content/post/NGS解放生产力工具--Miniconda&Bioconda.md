+++
date = "2016-08-31T09:37:00+08:00"
title = "NGS解放生产力工具--Miniconda&Bioconda"
tags = ['OTHERS']

+++

状态不甚了了的情行下多逛`github`似乎更容易转角遇到"神器"--Miniconda

via <http://conda.pydata.org/miniconda.html>

按照manual安装很轻松

安装完成后, 再看这个神器: bioconda

via <https://bioconda.github.io/index.html>

几条简单的命令, 照做, 于是, 发现曾经被坑爹的各种源码编译包折腾半死的软件都可以像这样一键安装搞定:

```
conda install abyss
```
是的没错, 就这么一句, 依赖, 编译全搞定, 以下为输出

```
Using Anaconda Cloud api site https://api.anaconda.org
Fetching package metadata ...........
Solving package specifications: ..........

Package plan for installation in environment /prodata/miniconda2/envs/qiime:

The following packages will be downloaded:

    package                    |            build
    ---------------------------|-----------------
    abyss-1.9.0                |      boost1.60_1        21.3 MB  bioconda

The following NEW packages will be INSTALLED:

    abyss: 1.9.0-boost1.60_1 bioconda

Proceed ([y]/n)? y

Fetching packages ...
abyss-1.9.0-bo 100% |########################################| Time: 0:01:19 281.70 kB/s
Extracting packages ...
[      COMPLETE      ]|###########################################################| 100%
Linking packages ...
[      COMPLETE      ]|###########################################################| 100
```

如果创建`myenv`环境时指定的是`none-root`路径, 基本上就完全独立于`host`系统, 而且无需`root`权限(这个特性简直天然为cluster而生), 配置好`env`以后完全开箱即用, 缺啥`conda install xxx`, 自动解决依赖, 热泪盈眶......

于是曾经被认为超级难装的`Qiime`, `SURPI`等只需要对着依赖表敲`conda install xxx`即可

呃, 脱坑的感觉真好!

`source activate qiime`

conda大法好!

## 注意

因为墙的存在, 访问 Anaconda 下载 packages 速度很慢, 所幸有清华大学做了镜像

使用方法很简单, 两句话

```
conda config --add channels 'https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/'
conda config --set show_channel_urls yes
```

> 如果是 Windows 系统, 需要把第一行的 url 两边单引号去掉

Anaconda 安装包可以到 <https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/>下载