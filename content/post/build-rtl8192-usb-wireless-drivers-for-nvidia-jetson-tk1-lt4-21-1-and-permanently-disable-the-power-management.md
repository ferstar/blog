---
date = "2015-08-31T23:20:43+08:00"
title = "build rtl8192 usb wireless drivers for nvidia jetson tk1 lt4-21-1 and permanently disable the power management"
tags = ['LINUX']

---
- download the kernel sources from [developer.download.nvidia.com][1]
- decompressed the files into /usr/src, the directory should like this /usr/src/kernel.
- `#zcat /proc/config.gz > /usr/src/kernel/.config`
- `$cd /usr/src/kernel `
- `#make prepare`
- `#make modules_prepare`
- `$cd /the/path/to/the/usb/driver/`
- `$make ARCH=arm`
- `#make install`
- block the default rtl8192cu driver  
  `vi /etc/modprobe.d/blacklist-native-rtl8192.conf`
  This file ships with the rtl8192-fixes DKMS module.
  Blacklist the native (and currently broken) kernel driver so
  ours gets loaded instead:
  blacklist rtl8192cu
  blacklist rtl8192c_common
  blacklist rtlwifi
  `vi /etc/modprobe.d/8192cu.conf`
  prevent power down of wireless when idle
  options 8192cu rtw_power_mgnt=0
- reboot the device
  you can check the status if it is off:
  `cat /sys/module/8192cu/parameters/rtw_power_mgnt`
  it should be 0 now.

  [1]: http://developer.download.nvidia.com/mobile/tegra/l4t/r21.1.0/sources/kernel_src.tbz2
