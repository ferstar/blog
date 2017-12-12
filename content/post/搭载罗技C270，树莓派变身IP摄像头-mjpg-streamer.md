---
date = "2015-08-15T22:00:21+08:00"
title = "搭载罗技C270，树莓派变身IP摄像头(mjpg-streamer)"
tags = ['OTHERS']
---

最开始pi一代是搭配自带摄像头模块，采用这里的方案

[h264_v4l2_rtspserver](https://github.com/mpromonet/h264_v4l2_rtspserver)

最近pi二代推出，性能比一代强大了不少，可以装ubuntu跑ROS，顺路把玩了下罗技的C270摄像头

开始用`mjpg-streamer` `MJPEG`格式黑屏无显示，加了参数`-y`，也就是`YUV`格式，正常，但CPU占用超高，达90%，负载长期1.2不下，google大法一番后，代码杂交结果如下，[成功启用MJPEG格式](https://github.com/ferstar/mjpg-streamer-diy/blob/master/README.md)，延迟尚可，系统负载影响几乎没有，CPU平均1.3～效果拔群