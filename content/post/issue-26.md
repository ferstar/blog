---
title: "小米8养老折腾"
date: "2020-10-17T10:23:39+08:00"
tags: ['Android']
comments: false
---

> created_date: 2020-10-17T10:23:39+08:00

> update_date: 2020-11-28T00:44:11+08:00

> comment_url: https://github.com/ferstar/blog/issues/26

养老养老了，MIUI11 9.9.27，只装个面具root，其他模块调度全扔
---

一路官方 OTA 上到 MIUI12, 感觉手上的米 8 已经战不动了, 正好官方最后的开发版定格在 MIUI12 20.9.4, 所以是时候再搞一波机, 养个老

1. 官方 or 官改 or 类原生

> 因为 NFC 公交卡是刚需, 类原生就不能考虑, 官改感觉改的乱七八糟, 所以只能自己整整官方包了

2. ext4 or f2fs

> 这个当然是 f2fs yes(4k随机写性能大概能比 ext4 高 25% 左右) 其实从 MIUI10 起官方内核也是支持 f2fs 的, 只不过 ROM 默认还是用的是 ext4, 附一个补丁
[Patch-wayne-f2fs-any-rom.zip](https://github.com/ferstar/blog/files/5395404/Patch-wayne-f2fs-any-rom.zip) 其实很简单, 就是修改了系统`/data`及`/cache`的挂载参数, 另外最好再加刷一个 f2fs 优化补丁 
[f2fs-optimize.zip](https://github.com/ferstar/blog/files/5395405/f2fs-optimize.zip)

> 改 f2fs 步骤大概说一下: REC 里把/data, /cache 格式化为 f2fs -> 重启至REC -> 刷补丁 -> 重启手机即可

3. 官核 ~~or 第三方内核~~

> UPDATE: 弃坑，还是官核稳。

> 第三方内核的优点是自定义了一坨东西, 代码上较官方内核新一些, 我主要看重快充, 以及支持 MIUI DC 调光, 所以这方面选择就比较窄, 因为没几个三方内核支持 DC 调光的, 目前试用下来有两个内核支持, 一个是巫女内核, 我只用过 7.1 这个是支持 DC 调光的, 另外还有个Tsing Kernel这个也是支持 DC 调光, 安卓 9 以下的三方内核没有一个支持 DC 调光, 所以直接 pass

> 刷三方内核的步骤: 刷回原生 ROM 内核 -> 刷 magisk ->  刷三方内核 -> 刷 magisk -> 双清cache(不需要清数据)

4. 要不要上调度

> 神他么的 yc 调度, 你值得拥有: https://github.com/yc9559/uperf

5. magisk 模块

> 这个自己去酷安捞, 我主要用了杜比&蝰蛇音效的模块以及 Riru core & EdXposed & Busybox & SQLite 加上上面提到的 yc调度

6. exposed 模块

> ChiMi & 微X模块 & 腾爱优芒豆去广告 & 知了 & AD 快消

7. 搞机常用 APP 们

> 酷安 & Scene & MT 管理器 & 钛备份 & AccuBattery & STM工具箱 & 搞机助手 & EX kernel manager

8. To be continue...

