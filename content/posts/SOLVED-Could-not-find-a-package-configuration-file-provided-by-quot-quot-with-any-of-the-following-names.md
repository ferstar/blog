---
title: "[SOLVED]Could not find a package configuration file provided by &quot;***&quot; with any   of the following names"
slug: "solved-could-not-find-a-package-configuration-file-provided-by-quot-quot-with-any-of-the-following-names"
date: "2015-08-12T09:17:00+08:00"
tags: ['OTHERS']
comments: true
---


[进行到Workspaces](http://wiki.ros.org/turtlebot/Tutorials/indigo/Turtlebot%20Installation)

源码编译果然坑

`rocon catkin_make`时报错如题，解决方法如下：

`sudo apt-get install ros-indigo-***`

其中***可以替换为任意报错的包名字即可

有些包可能提示的是下划线，比如`yocs_msgs`，对应的deb包名字应该是`ros-indigo-yocs-msgs`
