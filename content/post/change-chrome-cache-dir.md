+++
date = "2013-12-08T18:27:04+08:00"
title = "linux下更改chrome浏览器cache路径"
tags = ['LINUX']

+++

gedit /etc/chromium-browser/default

<pre class="lang:default decode:true " ># Default settings for chromium-browser. This file is sourced by /bin/sh from
# /usr/bin/chromium-browser

# Options to pass to chromium-browser
CHROMIUM_FLAGS="--disk-cache-dir=/tmp/Chromium/"</pre> 
