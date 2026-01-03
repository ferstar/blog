---
title: "Bumblebee双显卡切换安装完成后的惊喜"
slug: "bumblebee-installation"
date: "2013-10-19T20:03:25+08:00"
tags: ['LINUX']
comments: true
---


我大华硕Fn亮度控制终于正常了，至此ubuntu13.04下所有HotKey功能均能正常使用，以下是官方wiki安装说明：[https://wiki.ubuntu.com/Bumblebee#Installation](https://wiki.ubuntu.com/Bumblebee#Installation "官方wiki页面")

## Bumblebee Project

Bumblebee aims to provide support for [NVIDIA Optimus](http://www.nvidia.com/object/optimus_technology.html) laptops for GNU/Linux distributions. Using Bumblebee, you can use your NVIDIA card for rendering graphics which will be displayed using the Intel card. Bumblebee has now become officially supported in Saucy or newer. However, prior releases are supported by the [Bumblebee Project community](https://launchpad.net/~bumblebee) from Ubuntu version 12.04 up to 13.04.

## Installation

Basic Setup

You need to open your [terminal](http://askubuntu.com/questions/38162/what-is-the-terminal) and enter the commands below.

If on 12.04.3, replace linux-headers-generic with linux-headers-generic-lts-raring.

1.  (not needed for 13.10 Saucy and newer) <tt>sudo add-apt-repository ppa:bumblebee/stable</tt>
2.  Enable the Universe and Multiverse repositories (for bumblebee and nvidia packages respectively).
3.  <tt>sudo apt-get update</tt>
4.  Install Bumblebee using the default proprietary nvidia driver:<tt>sudo apt-get install bumblebee virtualgl linux-headers-generic</tt>
5.  Reboot
  Advanced Setups

For advanced users, if you do not want to use the proprietary nvidia driver or 32-bit libraries (for example, if you are only interested in power savings), you can do your custom installation.

Minimal setup : <tt>sudo apt-get install --no-install-recommends bumblebee</tt>

Depending on your needs, add to this line:

*   <tt>bumblebee-nvidia</tt>: proprietary nvidia driver support (if installed, become default over nouveau)
*   <tt>virtualgl</tt>: VirtualGL as backend
*   <tt>virtualgl-libs-ia32</tt>: 32bit support for VirtualGL on 64bit system, necessary to run 32bit app through optirun
*   <tt>primus</tt>: primus/primusrun as backend (virtualgl Stays default, you need to run <tt>optirun -b primus &lt;app&gt;</tt>)
*   <tt>primus-libs-ia32</tt>: 32bit support for primus/primurun on 64bit system, necessary to run 32bit app through optirun

## Usage

To run your application with the discrete NVIDIA card run in the terminal:

*   $ <tt>optirun [options] &lt;application&gt; [application-parameters]</tt>
  Example:

*   $ <tt>optirun firefox</tt>
  For a list of options for <tt>optirun</tt> run:

*   $ <tt>optirun --help</tt>
  Normally you do **not** use <tt>optirun</tt> for your window manager, installations or other non graphic heavy demanding programs. The <tt>optirun</tt> command is mainly used for graphic demanding programs or for games.

## Power Management

A primary goal of this project is to not only enable use of the discrete GPU for rendering, but also to enable smart power management of the dGPU when it's not in use. We're using either bbswitch (a module) or vga_switcheroo (kernel module, experimental) to do this in Bumblebee.

Since Bumblebee 3.0, this feature is enabled by default, using [bbswitch](https://github.com/Bumblebee-Project/bbswitch). This allow automatic power management, without any configuration needs.

If Power Management doesn't work on your laptop, please go to this [Power Management (PM)](http://wiki.bumblebee-project.org/Power-Management) page and help to improve Bumblebee.

## Troubleshooting

"Cannot access secondary GPU" error

In LTS 12.04.3, 13.04 and later, if your card seems to be inaccessible, i.e.<tt>[ERROR]Cannot access secondary GPU - error: [XORG] (EE) No devices detected.</tt> you need to edit the /etc/bumblebee/xorg.conf.nvidia (or /etc/bumblebee/xorg.conf.nouveau if using the noveau driver) and specify the correct BusID by following the instructions therein.

## Updating drivers

The Bumblebee project recommends you install drivers only through APT and not drivers provided by nvidia.com directly. This said, whenever you update your drivers through the supported repositories, you need to setup the correct config values in <tt>/etc/bumblebee/bumblebee.conf</tt>. See also [this FAQ on github](https://github.com/Bumblebee-Project/Bumblebee/wiki/Troubleshooting#bumblebeed-module-nvidia-is-not-found)

### Example update to nvidia-319 driver

E.g. to update to the latest update of 319.x driver, you need to install it through apt.

<tt>sudo apt-get install nvidia-319-updates nvidia-settings-319-updates</tt>

Then you need to edit <tt>/etc/bumblebee/bumblebee.conf</tt> and set:

<tt>KernelDriver=nvidia_319_updates</tt>

<tt>LibraryPath=/usr/lib/nvidia-319-updates:/usr/lib32/nvidia-nvidia-319-updates</tt>

<tt>XorgModulePath=/usr/lib/nvidia-319-updates/xorg,/usr/lib/xorg/modules</tt>

By running <tt>optirun nvidia-settings</tt> (or <tt>optirun -b none nvidia-settings -c :8</tt>) you can assert you are using the installed kernel module and driver.

&nbsp;

## IRC

Please join [#bumblebee](http://webchat.freenode.net/?channels=#bumblebee) channel on Freenode if you wish to help testing and creating the installer.

&nbsp;

## Reporting bugs/problems

First of all: If you have any problem, please read this article: [http://wiki.Bumblebee-Project.org/Troubleshooting](http://wiki.bumblebee-project.org/Troubleshooting)

If your issue is not solved, you can join the [#bumblebee](http://webchat.freenode.net/?channels=#bumblebee) IRC channel to ask for help (recommended). See also [http://wiki.Bumblebee-Project.org/Reporting-Issues](http://wiki.bumblebee-project.org/Reporting-Issues)

If you're asked to create a bugreport, run the next command in a terminal: <tt>sudo bumblebee-bugreport</tt>

&nbsp;

## Uninstall

If you're unsatisfied with Bumblebee, you can remove it via:

1.  <tt>sudo apt-get install ppa-purge</tt>
2.  <tt>sudo ppa-purge ppa:bumblebee/stable</tt>
  If you want to keep some programs from the bumblebee repository, you can also suffice by removing Bumblebee only (including its dependencies):

3.  <tt>sudo apt-get purge bumblebee</tt>
4.  <tt>sudo apt-get --purge autoremove</tt>
  &nbsp;

## Social Media

Follow us on: [Facebook](http://www.facebook.com/BumblebeeProject), [Twitter](https://twitter.com/#!/Team_Bumblebee) and [Google+](http://gplus.to/Bumblebee).

&nbsp;

## CUDA

There is sometimes confusion about CUDA. You don't need Bumblebee to run CUDA. Follow the [How-to](http://askubuntu.com/questions/131506/how-can-i-get-nvidia-cuda-or-opencl-working-on-a-laptop-with-nvidia-discrete-car) to get CUDA working under Ubuntu.

There is however a new feature (--no-xorg option for optirun) in Bumblebee 3.2, which makes it possible to run CUDA / OpenCL applications that does not need the graphics rendering capabilities.
