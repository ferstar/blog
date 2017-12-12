---
title: "How to remove snapd from Ubuntu 16.04 (Xenial Xerus)"
date: "2016-07-06T11:02:00+08:00"
tags: ['OTHERS']
comments: true
---


via <https://www.howtoinstall.co/en/ubuntu/xenial/snapd?action=remove>
Uninstall snapd
To remove just snapd package itself from Ubuntu 16.04 (Xenial Xerus) execute on terminal:

sudo apt-get remove snapd
Uninstall snapd and it's dependent packages
To remove the snapd package and any other dependant package which are no longer needed from Ubuntu Xenial.

sudo apt-get remove --auto-remove snapd
Purging snapd
If you also want to delete configuration and/or data files of snapd from Ubuntu Xenial then this will work:

sudo apt-get purge snapd
To delete configuration and/or data files of snapd and it's dependencies from Ubuntu Xenial then execute:

sudo apt-get purge --auto-remove snapd

为什么要删呢, 因为跟surpi用到的snap版本冲突, 所以只能牺牲这个我并不会用到的软件了