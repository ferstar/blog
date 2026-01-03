---
title: "Package is missing dependencies for libraries"
slug: "package-is-missing-dependencies-for-libraries"
date: "2013-12-08T18:22:50+08:00"
tags: ['LINUX']
comments: true
---


[](http://stackoverflow.com/questions/19184631/package-is-missing-dependencies-for-libraries-openwrt)

Finally got it, had to add change

`$(eval $(call BuildPackage,amld))`

to

`$(eval $(call BuildPackage,amld,+libopenssl))`
