---
title: "Ubuntu安装第三方内核后如何使用linux-common-tools"
date: "2023-01-24T01:11:05+08:00"
tags: ['Linux']
comments: true
---

Ubuntu 有点讨厌，内核相关的包给拆好几个，如果一直官方内核倒也没啥，关键官方内核太老，我一般第一时间就会替换成第三方的内核，比如：https://github.com/xanmod/linux

但是一旦换成第三方内核，你要使用类似 perf cpupower 这种内核相关命令的时候就会提示下面的错误：

```shell
perf
WARNING: perf not found for kernel 6.1.7-x64v3

  You may need to install the following packages for this specific kernel:
    linux-tools-6.1.7-x64v3-xanmod1
    linux-cloud-tools-6.1.7-x64v3-xanmod1

  You may also want to install one of the following packages to keep up to date:
    linux-tools-xanmod1
    linux-cloud-tools-xanmod1
```

缺包，但还贴心的给出了提示，估计是做了一层包装，我们拆开看看：

```shell
~ head -n 18 $(which perf)
#!/bin/bash
full_version=`uname -r`

# First check for a fully qualified version.
this="/usr/lib/linux-tools/$full_version/`basename $0`"
if [ -f "$this" ]; then
        exec "$this" "$@"
fi

# Removing flavour from version i.e. generic or server.
flavour_abi=${full_version#*-}
flavour=${flavour_abi#*-}
version=${full_version%-$flavour}
this="$0_$version"
if [ -f "$this" ]; then
        exec "$this" "$@"
fi
...
```

显然是从`/usr/lib/linux-tools/$(uname -r)`这个目录里去找`perl`了，解决也很简单：

1. 拉内核源码编译perf二进制塞到上面的目录
2. 因为这种工具代码更新频率很低，所以可以直接从低版本官方内核包中拖出来，丢到上面的目录

迫于太懒，我肯定选方法二：

```shell
mkdir -p /usr/lib/linux-tools/$(uname -r)
apt download linux-tools-5.19.0-21
# 把deb解压，/./usr/lib/linux-tools-5.19.0-21/ 目录里的文件全拷贝到 /usr/lib/linux-tools/$(uname -r)
```

大概的目录结构是这样：

```shell
➜  ~ uname -a
Linux u2004-p13 6.1.7-x64v3-xanmod1 #0~20230118.a4fbffc SMP PREEMPT_DYNAMIC Wed Jan 18 23:47:06 UTC  x86_64 x86_64 x86_64 GNU/Linux
➜  ~ tree /usr/lib/linux-tools/6.1.7-x64v3-xanmod1
/usr/lib/linux-tools/6.1.7-x64v3-xanmod1
├── acpidbg
├── bpftool
├── cpupower
├── libperf-jvmti.so
├── perf
├── turbostat
├── usbip
├── usbipd
└── x86_energy_perf_policy

0 directories, 9 files
```

敲个命令试试看：

```shell
➜  ~ cpupower frequency-info
analyzing CPU 0:
  driver: acpi-cpufreq
  CPUs which run at the same hardware frequency: 0
  CPUs which need to have their frequency coordinated by software: 0
  maximum transition latency:  Cannot determine or is not supported.
  hardware limits: 1.40 GHz - 1.80 GHz
  available frequency steps:  1.80 GHz, 1.70 GHz, 1.40 GHz
  available cpufreq governors: conservative ondemand userspace powersave performance schedutil
  current policy: frequency should be within 1.40 GHz and 1.80 GHz.
                  The governor "performance" may decide which speed to use
                  within this range.
  current CPU frequency: Unable to call hardware
  current CPU frequency: 1.90 GHz (asserted by call to kernel)
  boost state support:
    Supported: yes
    Active: no
```

完美，后续内核有更新的话，只需要重命名一下 /usr/lib/linux-tools/$(uname -r) 即可

有关的几个issue: 

1. https://github.com/xanmod/linux/issues/94
2. https://github.com/xanmod/linux/issues/121



```
# NOTE: I am not responsible for any expired content.
create@2023-01-24T01:11:05+08:00
update@2023-01-24T16:50:57+08:00
comment@https://github.com/ferstar/blog/issues/69
```
