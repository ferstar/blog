---
date = "2015-09-15T22:52:00+08:00"
title = "Remove Bluetooth Manager in Xubuntu"
tags = ['OTHERS']

---

[How to Remove Bluetooth Manager in Xubuntu](http://askubuntu.com/questions/305856/how-to-remove-bluetooth-manager-in-xubuntu)
## Q: I wanna remove bluetooth manager and its daemon from Xubuntu because my computer doesn't have bluetooth device. How should I do?
Note : I've searched questions http://askubuntu.com/search?q=Remove+Bluetooth but I find nothing. Wish I don't create duplicate question

## A: The following shell command will remove bluetooth and all its dependencies:

```
sudo apt-get purge "bluez*"
```
If this prompts you to remove the xubuntu-desktop meta-package, do not be alarmed. This is acceptable.

If installed, also remove the obex-data-server and the libopenobex package. The libbluetooth* package(s) must remain since too many stuff depends on it.

Afterwards, you should also run:
```
sudo apt-get autoremove
```
pretty good!