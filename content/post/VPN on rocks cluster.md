---
date = "2016-06-18T03:38:00+08:00"
title = "VPN on rocks cluster"
tags = ['OTHERS']

---

## 安装相关软件包
```
yum install ppp pptp pptp-setup
Setting up Install Process
Resolving Dependencies
--> Running transaction check
---> Package ppp.x86_64 0:2.4.5-5.el6 will be updated
---> Package ppp.x86_64 0:2.4.5-10.el6 will be an update
---> Package pptp.x86_64 0:1.7.2-8.1.el6 will be installed
---> Package pptp-setup.x86_64 0:1.7.2-8.1.el6 will be installed
--> Finished Dependency Resolution

Dependencies Resolved

==============================================================================
 Package            Arch           Version                 Repository    Size
==============================================================================
Installing:
 pptp               x86_64         1.7.2-8.1.el6           base          62 k
 pptp-setup         x86_64         1.7.2-8.1.el6           base          12 k
Updating:
 ppp                x86_64         2.4.5-10.el6            base         328 k

Transaction Summary
==============================================================================
Install       2 Package(s)
Upgrade       1 Package(s)

Total download size: 402 k
Downloading Packages:
(1/3): ppp-2.4.5-10.el6.x86_64.rpm                     | 328 kB     00:00     
(2/3): pptp-1.7.2-8.1.el6.x86_64.rpm                   |  62 kB     00:00     
------------------------------------------------------------------------------
Total                                         328 kB/s | 402 kB     00:01     
Running rpm_check_debug
Running Transaction Test
Transaction Test Succeeded
Running Transaction
  Updating   : ppp-2.4.5-10.el6.x86_64                                    1/4 
  Installing : pptp-1.7.2-8.1.el6.x86_64                                  2/4 
  Installing : pptp-setup-1.7.2-8.1.el6.x86_64                            3/4 
  Cleanup    : ppp-2.4.5-5.el6.x86_64                                     4/4 
  Verifying  : ppp-2.4.5-10.el6.x86_64                                    1/4 
  Verifying  : pptp-1.7.2-8.1.el6.x86_64                                  2/4 
  Verifying  : pptp-setup-1.7.2-8.1.el6.x86_64                            3/4 
  Verifying  : ppp-2.4.5-5.el6.x86_64                                     4/4 

Installed:
  pptp.x86_64 0:1.7.2-8.1.el6        pptp-setup.x86_64 0:1.7.2-8.1.el6       

Updated:
  ppp.x86_64 0:2.4.5-10.el6                                                   

Complete!
```
## 创建vpn拨号
`pptpsetup --create aws --server xxx --user xxx --password xxx --encrypt -start`
## 具体见我的知乎回答
<https://www.zhihu.com/question/31220460/answer/103939079>