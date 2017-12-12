---
title: "Package ros-indigo-gazebo-ros has no installation candidate"
date: "2015-08-12T10:58:00+08:00"
tags: ['ROS', 'LINUX']
comments: true
---


x，又找不见这个包。。。

奶奶的，装之

`sudo -H apt-get install -y ros-indigo-gazebo-ros`

然后提示没有这个包，好吧，通配符匹配之

`sudo -H apt-get install -y ros-indigo-gazebo-*`

似乎也没搞定，挂起，等待后续解决

## 暂时跳过，方法：

`~/kobuki/src/kobuki_desktop$ mv kobuki_gazebo_plugins .kobuki_gazebo_plugins`

即移开`kobuki_gazebo_plugins`这个包

## 两种补全依赖包的做法

1.  `rosdep install --from-paths src -i -y`
2.  `sudo -H apt-get install -y ros-indigo-***` 提示缺啥补上即可

## 与之相关连的一个包`kobuki_qtestsuite`也需要跳过，跳过后发现官方有deb包提供，所以尝试安装

`sudo apt-get install ros-indigo-kobuki-qtestsuite`

于是又安装了一坨deb。。。不过还好这个包算是装上了

## 编译到`turtlebot`的时候，上面提到的跳过大法似乎失灵，所以只能暴力删除

`~/turtlebot/src/turtlebot_create_desktop$ rm -r create_gazebo_plugins`

## 总结

顺利编译完成，只有`kobuki_gazebo_plugins`和`create_gazebo_plugins`两个包没有编译，其余全部搞定！

## 附加

修改catkin_ws/devel中
```
# environment at generation time
CMAKE_PREFIX_PATH = '/home/ubuntu/catkin_ws/devel;/home/ubuntu/turtlebot/devel;/home/ubuntu/kobuki/devel;/home/ubuntu/rocon/devel;/opt/ros/indigo'.split(';')
```
环境变量
`～/.bashrc`中只需要添加

`source ~/catkin_ws/devel/setup.bash`

即可