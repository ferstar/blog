+++
date = "2017-05-22T14:08:00+08:00"
title = "farbox搬家记"
tags = ['WINDOWS', 'LINUX', 'FARBOX', 'BITCRON']

+++

前几天收到farbox的邮件，说由于dropbox api的停摆，farbox造了个bitcron的东东来替代，去官博看了下跟farbox感觉并无太大差别，依旧延续了我喜欢的小清新风格，所以照着博客说明迁移了下。
## 迁移到 Bitcron 吧

考虑到 Dropbox API 停摆之后的问题 (主要是新的文章、图片将无法再通过 Dropbox 更新)，我们建议迁移到 Bitcron。
Bitcron 除了长得更好看、更快之外，还有很多非常强大的功能，而且后续 (网站) 更新内容跟 FarBox 一样，通过 Dropbox 同步，几近可以忽略 Bitcron 的存在。
至于更强大的功能，除了 自动 HTTPS、DailyNote、一个网站多个微信绑定 等琐碎的功能外，还有曾经 FarBox 存在的几个试验性质的 App (比如一页小站)，已经完全产品化为 SmartPage，效果非常惊艳。
我们简单地总结了下 Bitcron 一些特别的功能 (未来仍然会不断更新)，可以访问https://features.bitcron.com 具体了解。

## 如何迁移？

Bitcron 不会对外开放注册的，需要邀请才可以，没什么变故的话，未来也是如此。
所以，在迁移到 Bitcron 的过程中，注册账户时，务必使用自己 FarBox 的账户邮箱、并且通过这个 URL https://bitcron.com/login?by_farbox=true 进行注册，不然系统会提醒需要邀请才能继续。
另外， Bitcron 注册成功后，会自动从 FarBox 上合并账户余额到 Bitcron 上 (不会影响 FarBox 上的数据和使用)。
具体数据如何迁移，请参考这个页面 https://faq.bitcron.com/read/move-from-farbox#toc_1

## 小改farbox editor
迁移后发现farbox editor用不了，在dropbox应用文件夹下单独建立的是Farbox文件夹，所以就想到用软链接解决问题，linux下so easy，Windows下也好整
```bash
C:\Users\fer_s\Dropbox\应用>mklink
创建符号链接。

MKLINK [[/D] | [/H] | [/J]] Link Target

        /D      创建目录符号链接。默认为文件
                符号链接。
        /H      创建硬链接而非符号链接。
        /J      创建目录联接。
        Link    指定新的符号链接名称。
        Target  指定新链接引用的路径
                (相对或绝对)。
C:\Users\fer_s\Dropbox\应用>mklink /J Farbox Bitcron
为 Farbox <<===>> Bitcron 创建的联接
```
嗯，farbox editor又可以愉快的玩耍了