---
title: "使用hexo来写博客"
date: "2015-09-09T10:25:22+08:00"
tags: ['OTHERS']
comments: 
---

[官方说明](https://hexo.io/zh-cn/docs/)

# 我的安装过程
## 装nodejs
访问官网下载
[https://nodejs.org/en/](https://nodejs.org/en/)
解压到`～/.bin/`目录
添加环境变量
`vim ～/.zshrc`如下（我用的zsh）
```
# export MANPATH="/usr/local/man:$MANPATH"
export PATH="$HOME/.bin/node-v4.0.0-linux-x64/bin:$PATH"
source $ZSH/oh-my-zsh.sh
```
然后source一下`source ～/.zshrc`
检查是否正确指定`node -v`正常应该显示版本号`v4.0.0`
## 装git
`sudo apt-get install git`就这样
## 装淘宝cnpm替换npm
[淘宝npm镜像](http://ferstar.org/2015/09/04/%E6%B7%98%E5%AE%9DNPM%E9%95%9C%E5%83%8F/)
```
npm install -g cnpm --registry=https://registry.npm.taobao.org
```
一切为了速度！
## 安装hexo
`cnpm install -g hexo-cli`
是的你没看错，是cnpm而不是npm
检查下版本`hexo -v`正确输出如下
```
hexo-cli: 0.1.8
os: Linux 3.19.0-26-generic linux x64
http_parser: 2.5.0
node: 4.0.0
v8: 4.5.103.30
uv: 1.7.3
zlib: 1.2.8
ares: 1.10.1-DEV
modules: 46
openssl: 1.0.2d
```
## 建站
安装 Hexo 完成后，请执行下列命令，Hexo 将会在指定文件夹中新建所需要的文件
`hexo init blog`输出如下
```
INFO  Copying data to ~/blog
INFO  You are almost done! Don't forget to run 'npm install' before you start blogging with Hexo!
```

`cd blog`and`cnpm install`输出如下（截取一部分）

```
parser2@3.8.3)
├── nunjucks@1.3.4 (optimist@0.6.1, chokidar@0.12.6)
├── hexo-util@0.1.7 (ent@2.2.0, highlight.js@8.8.0)
├── bunyan@1.5.1 (safe-json-stringify@1.0.3, dtrace-provider@0.6.0, mv@2.1.1)
├── moment-timezone@0.3.1
├── lodash@3.10.1
├── moment@2.10.6
└── swig@1.4.2 (optimist@0.6.1, uglify-js@2.4.24)
```
完成后，指定文件夹的目录如下：

```
├── _config.yml
├── node_modules
│   ├── hexo
│   ├── hexo-generator-archive
│   ├── hexo-generator-category
│   ├── hexo-generator-index
│   ├── hexo-generator-tag
│   ├── hexo-renderer-ejs
│   ├── hexo-renderer-marked
│   ├── hexo-renderer-stylus
│   └── hexo-server
├── package.json
├── scaffolds
│   ├── draft.md
│   ├── page.md
│   └── post.md
├── source
│   └── _posts
└── themes
    └── landscape
```
生成这个目录树的程序叫`tree`可以`man tree`查看他的具体用法
其他说明官网说明写的很清楚[hexo.io](https://hexo.io/zh-cn/docs/setup.html)

