+++
date = "2017-06-27T09:54:00+08:00"
title = "解决混合硬盘执行update-grub命令后Windows引导丢失的问题"
tags = ['OTHERS']

+++

> 公司配的台式机是Dell xps8900，32G的SSD+2T的HDD，默认启用了intel的快速存储技术。前几日在HDD末端抠了个分区安装了Linux Mint 18，早上升级新内核执行`update-grub`命令后发现Windows10引导丢失。查看磁盘信息发现有两个莫名其妙的RAID array条目，估计就是磁盘中还残留有Intel RSTe RAID信息导致Windows分区被隐藏起来了。OK，发现原因就开始解决问题。

1. 进BIOS同步一下RAID磁盘内容，或者在Windows10中暂时将RAID加速功能关闭，以免意外资料丢失

2. 在Mint中执行如下命令就可以搞定了

   ```shell
      sudo dmraid -rE
      sudo os-prober
      sudo update-grub
   ```

3. 附命令输出，可以看到已经识别到Windows boot manager

   ```shell
   ferstar@XPS-8900 ~ $ sudo dmraid -rE
   [sudo] password for ferstar:
   Do you really want to erase "isw" ondisk metadata on /dev/sdb ? [y/n] :y
   Do you really want to erase "isw" ondisk metadata on /dev/sda ? [y/n] :y
   ferstar@XPS-8900 ~ $ sudo os-prober
   /dev/sda2@/EFI/Microsoft/Boot/bootmgfw.efi:Windows Boot Manager:Windows:efi
   ferstar@XPS-8900 ~ $ sudo update-grub
   Generating grub configuration file ...
   Found Windows Boot Manager on /dev/sda2@/EFI/Microsoft/Boot/bootmgfw.efi
   Found linux image: /boot/vmlinuz-4.4.0-81-generic
   Found initrd image: /boot/initrd.img-4.4.0-81-generic
   Found linux image: /boot/vmlinuz-4.4.0-53-generic
   Found initrd image: /boot/initrd.img-4.4.0-53-generic
   Adding boot menu entry for EFI firmware configuration
   done
   ```

   ​

> 参考链接
>
> https://www.linuxwolfpack.com/linux-wont-install-due-to-prvious-raid.php