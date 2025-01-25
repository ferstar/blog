---
title: "How to Build Kernel for Realme GT5 Pro(RMX3888)"
date: "2025-01-25T10:45:41+08:00"
tags: ['Android']
comments: true
---

1. 环境&配置

操作系统 Ubuntu、Debian 都可以，内存 16 GB 起步，不够的自行加 swap，硬盘空间 50GB

装依赖：`sudo apt install git gnupg flex bison build-essential zip curl zlib1g-dev unzip rsync python3(如果还有缺的自己补)`

2. 装 repo 工具

```shell
sudo curl https://mirrors.tuna.tsinghua.edu.cn/git/git-repo > /usr/bin/repo
sudo chmod +x /usr/bin/repo
```

3. 拉取机型源码&编译

```shell
mkdir kernel
cd kernel
export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo' 
# 安卓14可以把 gt5pro_v.xml 换成 gt5pro_u.xml
repo init --repo-rev=v2.16 --depth=1 -u https://github.com/ferstar/kernel_manifest.git -b realme/sm8650 -m gt5pro_v.xml
repo sync --no-tags
cd kernel_platform
# 这个必须删，不然内核启动后没法驱动WiFi、蓝牙和4/5G
rm common/android/abi_gki_protected_exports_*
# 编译
python build_with_bazel.py -t pineapple gki  --lto=thin --config=fast --disk_cache=$HOME/.cache/bazel --//msm-kernel:skip_abi=true --//msm-kernel:skip_abl=true -o "$(pwd)/out" || true
```

因为真我只开源了Kernel和Vendor，没有common source，所以这个方案是跟一加12杂交的，上面的编译中间会有报错，但不影响，内核可以正常生成：

`bazel-out/k8-fastbuild/bin/msm-kernel/pineapple_gki_kbuild_mixed_tree/Image`

将其塞进`AnyKernel3`的压缩包内即可刷入手机。



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-25T10:45:41+08:00
Updated at: 2025-01-25T10:45:51+08:00
Origin issue: https://github.com/ferstar/blog/issues/88
```
