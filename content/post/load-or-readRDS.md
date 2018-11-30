---
title: "Load() or ReadRDS()?"
date: 2018-07-20T14:40:19+08:00
tags: ['R']
comments: true
---

最近做的项目，需要从用户手里拿到一个 R 对象文件，姑且叫 out.rdata，后台要从这个 out.rdata 中取出一个叫 fuck 的对象。原来一直是用`load('out.rdata')`这种方式加载，没发现问题，直到昨天发现一个报错的记录：

```shell
Error in load('out.rdata') :
  bad restore file magic number (file may be corrupted) -- no data loaded
In addition: Warning message:
file ‘seurat.rdata’ has magic number 'X'
  Use of save versions prior to 2 is deprecated
Execution halted
```

放狗一搜，发现这篇文章：

https://yihui.name/en/2017/12/save-vs-saverds/

猜测可能用户是用`saveRDS()`方法保存的数据，于是对应的，用`readRDS()`加载就正常了。

但谁知道用户爸爸哪天心情好又换`save()`存咋办？

所以需要做个判断：如果是`save()`保存的数据，用`load()`；如果是`saveRDS()`保存的，则用`readRDS()`。

那么问题来了，怎么判断`*.rdata`的保存方式方法？

继续放狗，未果

换思路，Try...Catch 之：先`load()`扑街了再用`readRDS()`，代码如下：

R 的`tryCatch`写起来好丑陋。。。

```R
library(stringr)

loadFuck <- function(fp) {
  out <- tryCatch({
    # 大佬建议用 attach
    attach(fp)$fuck
  }, warning = function(e) {
    # 这里扑街提示是 warning
    return(readRDS(fp))
  }, error = function(e) {
    # 真扑街那没办法，停车报警
    stop('cannot load R object')
  }, finally = {
    # attach 完了打扫现场
    name = paste("file", fp, sep = ":")
    detach(name, character.only = TRUE)
  })
  return(out)
}

fuck <- loadFuck('out.rdata')
```

搞定！

贴个参考文章的好评论

> Great  post! If you really want to use `save()` and then want load it back, use `attach()` instead of `load()`. The former will warn you about  overwriting. Also you can unload it with `detach("file:foo.RData")`. 
