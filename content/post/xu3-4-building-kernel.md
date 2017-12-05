+++
date = "2015-12-17T11:55:14+08:00"
title = "Odroidxu3/4_building_kernel"
tags = ['OTHERS']

+++
## Introduction
This page introduce how you can download and compile the Linux system kernel for ODROID-XU3/XU4. Generic Linux system needs gcc version 4.6 to build the Kernel.

## Step-by-Step guide to building an ODROID-XU3/4 Kernel

### Download the cross tool chain package

<http://dn.odroid.com/ODROID-XU/compiler/arm-eabi-4.6.tar.gz>

> Note:

>> This toolchain only used to build the kernel.
This toolchain is included in the Android source package. ($ANDROID_ROOT/prebuilts/gcc/linux-x86/arm/arm-eabi-4.6)
Copy the cross tool package to /opt/toolchains

> If the '/opt/toolchains' directory does not exist in host pc, then create the directory.

```
$ sudo mkdir /opt/toolchains
$ sudo cp arm-eabi-4.6.tar.gz /opt/toolchains
$ cd /opt/toolchains
$ sudo tar zxvf arm-eabi-4.6.tar.gz
```

###  Uncompress the cross tool with tar command

```
$ cd /opt/toolchains
$ sudo tar xvfz arm-eabi-4.6.tar.gz
```

###  Add Path in your environment file

Modify your ~/.bashrc(or ~/.zshrc if you use zsh as your default shell) file to add a new path with editor (gedit or vi)

```
export ARCH=arm
export PATH=${PATH}:/opt/toolchains/arm-eabi-4.6/bin
export CROSS_COMPILE=arm-eabi-
```

###  To apply this change, login again or restart the .bashrc
`$ source ~/.bashrc`

###  Check the tool-chain path to see if it is set up correctly or not.
```
$ arm-eabi-gcc -v
Using built-in specs.
COLLECT_GCC=arm-eabi-gcc
COLLECT_LTO_WRAPPER=/opt/toolchain/arm-eabi-4.6/bin/../libexec/gcc/arm-eabi/4.6.x-google/lto-wrapper
Target: arm-eabi
Configured with: /tmp/android-15472/src/build/../gcc/gcc-4.6/configure --prefix=/usr/local --target=arm-eabi --host=x86_64-linux-gnu 
--build=x86_64-linux-gnu --with-gnu-as --with-gnu-ld --enable-languages=c,c++ --with-gmp=/tmp/android-15472/obj/temp-install --with-
mpfr=/tmp/android-15472/obj/temp-install --with-mpc=/tmp/android-15472/obj/temp-install --without-ppl --without-cloog --disable-libs
sp --enable-threads --disable-nls --disable-libmudflap --disable-libgomp --disable-libstdc__-v3 --disable-sjlj-exceptions --disable-
shared --disable-tls --disable-libitm --with-float=soft --with-fpu=vfp --with-arch=armv5te --enable-target-optspace --with-abi=aapcs
 --with-gcc-version=4.6 --with-binutils-version=2.21 --with-gmp-version=4.2.4 --with-mpfr-version=2.4.1 --with-gdb-version=7.3.x --w
ith-arch=armv5te --with-sysroot=/tmp/android-15472/install/sysroot --with-prefix=/tmp/android-15472/install --with-gold-version=2.21
 --enable-gold --disable-gold --disable-multilib --program-transform-name='s&^&arm-eabi-&'
Thread model: single
gcc version 4.6.x-google 20120106 (prerelease) (GCC)
```

## Linux ODROID-XU3/4 works as follow

### It must have at least two partitions

- First Partition must be a FAT32/EXT4 partition.

- Second Partition can be whatever the Filesystem that your kernel supports (must be built in).
> Note: It is possible to use the first partition as ext4, however its strongly not recommended due to Windows Users lost the capability of changing boot.ini

- Partition Contents
```
Partition 1:
    Kernel Image (zImage)
    boot.scr
    exynos5422-odroidxu3.dtb
    uInitrd (if applicable)
    
Partition 2:
    rootfs (a.k.a. File System)
    Currently Supported Linux Distributions
```
- Ubuntu 14.04 [Ubuntu 14.04 Forum Thread][1]
> Note: More distribution support will come with time.

- HDMI Support On Linux
HDMI support should work out-of-box for everyone including framebuffer console if you experience any issue please contact us on the ODROID Forums
On the provided Ubuntu image there are several examples on how to configure the HDMI to your specific resolution or even lock to a certain resolution. You can check the configuration file on /media/boot/boot.ini of the Ubuntu Image

- DisplayPort Support on Linux
For displayport configuration please follow this guide Displayport Guide on [ODROID Forums][2]

- Kernel Sources
Kernel sources for ODROID-XU3/4 is on our [Github][3]. Branch is **odroidxu3-3.10.y** defconfig is **odroidxu3_defconfig**

## Kernel Rebuild Guide
>Note:
You can compile **kernel & dtb** images in host PC using the cross compiler. But, you cannot create **uInitrd ramdisk image** in host PC. Because the binary files in ramdisk image refer to current root file system during the executing `update-initramfs` command.

Please follow the instructions below to rebuild the Linux Kernel for ODROID. Those instructions cover native build of the Kernel.

### Install dependencies
```
pc@host:~$ sudo apt-get install build-essential libqt4-dev libncurses5-dev git 
Clone Repo:
pc@host:~$ git clone --depth 1 https://github.com/hardkernel/linux.git -b odroidxu3-3.10.y odroidxu3-3.10.y 
pc@host:~$ cd odroidxu3-3.10.y 
```

### Configure Kernel
```
pc@host:~$ make odroidxu3_defconfig 
```

### Do changes if you need/want
```
pc@host:~$ make menuconfig 
```
for my case, the official kernel can not recognise my **Logitech, Inc. F710 Wireless Gamepad**, so I have to change it by myself:
![内核定义](http://7xivdp.com1.z0.glb.clouddn.com/png/2015/12/310876d095ef89355a35de54838acad9.png)

I alse changed the kernel default resolution to fit my 7' touchscreen:
![分辨率修改](http://7xivdp.com1.z0.glb.clouddn.com/png/2015/12/3ad91156dcea84a78dab3f5643ea2832.png)

### Build Kernel and Modules
```
pc@host:~$ make -j8
```

 > This explanation assume that your USB memory CARD reader is assigned at /dev/sdb. Be careful!

### Install zImage & DTB file
```
pc@host:~$ mkdir -p mount
pc@host:~$ sudo mount /dev/sdb1 ./mount
pc@host:~$ sudo cp arch/arm/boot/zImage arch/arm/boot/dts/exynos5422-odroidxu3.dtb /media/boot && sync && sudo umount ./mount
```

### Install Modules
```
pc@host:~$ sudo mount /dev/sdb2 ./mount
pc@host:~$ sudo make modules_install ARCH=arm INSTALL_MOD_PATH=./mount
```
### Copy .config to /boot for initramfs creation
```
pc@host:~$ sudo cp .config ./mount/boot/config-`make kernelrelease`
```

> You must do the remaining steps in **ODROID-XU3/4 board**. So plugin your tf card to odroid and boot it, then continue the following steps.

###  Create initramfs
```
odroid@odroid:~$ sudo update-initramfs -c -k `uname -r`
```

### Create uInitrd
```
odroid@odroid:~$ sudo mkimage -A arm -O linux -T ramdisk -C none -a 0 -e 0 -n uInitrd -d /boot/initrd.img-`uname -r` /boot/uInitrd-`uname -r`
```

### Install new uInitrd
```
odroid@odroid:~$ sudo cp /boot/uInitrd-`uname -r` /media/boot/uInitrd
```

### reboot and check if the kernel works well on your board
`odroid@odroid:~$ sudo sync && reboot`

Your new kernel should be installed. 

## ODROID Utility
Note for your own convenience we provide daily builds of Linux kernel that can be easily installed on Supported distros by using a ODROID Utility.
```
odroid@odroid:~$ sudo -s
root@odroid:~$ wget -O /usr/local/bin/odroid-utility.sh https://raw.githubusercontent.com/mdrjr/odroid-utility/master/odroid-utility.sh
root@odroid:~$ chmod +x /usr/local/bin/odroid-utility.sh
root@odroid:~$ odroid-utility.sh
```

  [1]: http://forum.odroid.com/viewtopic.php?f=95&t=5985
  [2]: http://forum.odroid.com/
  [3]: http://github.com/hardkernel/linux