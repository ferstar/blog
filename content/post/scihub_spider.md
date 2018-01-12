---
title: "Sci-Hub Spider"
date: 2017-12-18T15:22:02+08:00
tags: ['PYTHON', 'SCI']
comments: true
---

众所周知，因为版权问题，科研神器`SciHub`近来并不稳定，频繁更换域名。为了方便单位科研同学，上周用Python写了SCI文献下载器，并在朋友圈发布，反响颇佳。周末又重新理了一遍逻辑，现在论文下载能力应该是得到了进一步增强。

工具原理很简单，主要利用了爬虫技术（老司机可以直接自己撸一个也没啥问题，纯体力活）。

程序首先会检测更新，发现新版本则自动下载到桌面，需要手动安装。

接着爬取目前可用的`Sci-Hub`站点。

然后会以验证`http.headers`的方式（一般网站的headers大小仅仅几百个字节，所以并不会对服务器造成什么压力）去探测`Sci-Hub`可用站点在本地网络的连通性，保留本地确定可连的站点。

然后就开始检测用户剪贴板内容，如发现纯数字的PMID或者合法的DOI（通常以10.开头）就会自动去检索。

PMID/PMCID/Manuscript ID/DOI ID转换是通过爬取`NCBI`主站获得。也就是说如果在`NCBI`上找不到对应DOI的文章是不会下载的，这种情况就需要你自己想办法找到文章的DOI号，再尝试让程序检索下载。

拿到DOI号后即开始检索文献真实下载地址，优先从[libgen.io](http://libgen.io)爬取，爬取失败再去`sci-hub`目前可用的镜像站点爬取。所以其实这里是从两个源头去下载，libgen服务比较稳定，`Sci-Hub`相对不太稳。

爬取成功则将文章保存在用户桌面。

免安装版使用[PyInstaller](http://www.pyinstaller.org/)制作，只支持Windows7以上系统。

安装版使用[cx_Freeze](https://anthony-tuininga.github.io/cx_Freeze/)（打包）[Inno Setup - JRSoftware](http://www.jrsoftware.org/isinfo.php)（安装）制作，支持Windows XP系统，因为少了解压过程，不会产生系统垃圾，同时打开速度比安装版要快很多，推荐使用。

## 使用方法

只需打开软件，复制要下载文章的PMID/PMCID/Manuscript ID/DOI等任一ID，程序可以自动从复制内容中解析出ID信息进行检索，找到文章即下载到桌面。

PS：打开软件和复制ID无先后顺序，你可以先打开软件再复制ID或者先复制ID再打开软件。

> **请注意，并不是所有的文章都可以下载的到！！！**
>
> **Please note that not all papers can be downloaded successfully!!!**
>
> **考虑到可能引起的资源滥用，暂不开源**

## 下载地址(百度网盘已作废)

[SciHub-Spider-update-1.6.4](http://p2f3k7a9w.bkt.clouddn.com/exe/SciHub-Spider-update-1.6.4.exe?v=1234)

~~链接:https://pan.baidu.com/s/1boAEC4f~~

~~密码:dz4y~~

## 求捐赠

PayPal: https://www.paypal.me/ferstar

觉得好用可以请我喝点饮料，谢谢

![未命名_meitu_0](http://7xivdp.com1.z0.glb.clouddn.com/png/2017/12/3d1e449bc01bae28f85b1675bd769b7a.png/xyz)

## 更新信息
请注意由于SciHub网站更新,所以旧版本(1.6.2以前)都无法正常解析到文献下载地址,请更新新版

```shell
2018/01/12 1.6.4:
1. 原网盘分享莫名被禁,故增加程序自动更新功能,弃用百度(使用七牛云存储服务)
2. 如果觉得微信赞赏码烦人,可以去程序根目录把wechat.jpg图片删除即可

2018/01/11 1.6.3:
1. 适配SciHub网站更新
2. 增加了一个SciHub可用性检测站点
3. 增加微信赞赏码(更新不易,请多多支持)

2017/12/20 1.6.2:
1. 隐去scihub可用网站信息
2. 修复macOS模块引用的一个小bug

2017/12/20 1.6.1:
1. 增加macOS支持

2017/12/19 1.6.1:
1. 修复文章标题包含特殊字符时程序闪退的问题
2. 修复检测scihub站点可用性时可能引起的闪退问题
3. 未检测到合法ID不再清空用户剪贴板内容
4. 增加从真实下载地址解析文章标题功能,如解析到则用作保存文件名,否则使用DOI代替
5. 延长检测可用scihub站点扫描超时时间(应对龟速网络)
6. 考虑系统兼容性增加64位专版，使用优先级“*支持xp”>“*免安装版不支持xp”>“*64位专版免安装”，如果都有问题，请反馈留言

2017/12/18 1.6:
1. 新增SciHub镜像站点可用性检测
2. 重写爬虫逻辑,提升文献下载能力
3. 改名改图标
4. 精简不必要的组件包,缩小安装包体积
5. 移除微信二维码捐赠图片
6. 提供安装板和免安装版两种选择

2017/12/14 1.5:
1. 兼容xp系统，完成Windows全平台支持
2. 首版安装版
3. 缩减程序体积

2017/12/14 1.4:
1. 兼容32位系统，xp依然不支持
2. 禁止ssl验证
3. 取消ssl禁用警告信息

2017/12/14 1.3:
1. 修复bug
2. 支持Windows 7 64位
3. 增加PMID/PMCID/Manuscript ID转换DOI支持

2017/12/14 1.0-1.2:
1. 初版，单文件，仅支持Windows10 x64位系统
2. 修复bug

```

## 程序运行信息：

```shell
 ________________
| Sci-Hub Spider |
 ----------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\-
                ||----w |
                ||     ||
		written by ferstar with love

USAGE: copy a DOI or any content that contains a valid DOI and wait
BTW:   PMID/PMCID/Manuscript ID also supported but not recommended
       Please note that not all papers can be downloaded successfully
BLOG:  https://blog.ferstar.org/post/scihub_spider

I need to check if scihub is available locally
it may take a few seconds, please wait

fetching available sci-hub mirrors
sci-hub mirror list updated

check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://sci-hub***"...ok
check site status "https://www.sci***"...ok

ID detected: 29245169, need convert to DOI...
DOI converted: 10.1055/s-0043-122232, fetching...
try to fetch on "libgen.***"
paper found, will download
paper title: [Fehler und Schwchen ...] found
[Fehler und Schwchen ...] download completed 220.59 KB / 220.59 KB
[Fehler und Schwchen ...] has been saved on you Desktop

press enter key to continue or click the close button to exit
```

## 反馈

如果出现运行闪退的情况，请在本博客留言，注明引起闪退的DOI号及操作系统信息。

或者直接加我微信沟通。
