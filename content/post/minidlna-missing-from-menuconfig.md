+++
date = "2014-02-17T20:48:41+08:00"
title = "minidlna Missing From Menuconfig"
tags = ['OPENWRT', 'LINUX']

+++

To summarize the fix for no minidlna selection:

written_direcon wrote:

    ./scripts/feeds update packages

    ./scripts/feeds install -d m minidlna

<!--more-->

Then:

In "make menuconfig" select: Libraries -> libffmpeg-full

Then select: Multimedia -> minidlna

And/or you can select

minidlna support in the LuCI -> Applications section of "make menuconfig"
