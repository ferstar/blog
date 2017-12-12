---
date = "2013-10-31T20:33:46+08:00"
title = "梳理下hg255d完美刷op的步骤"
tags = ['LINUX', 'OPENWRT']

---

1.  <span style="line-height: 15px;">原版uboot下刷1102-0x20000_hg255d-squashfs-tftp.checksum2</span>
2.  备份本机eeprom：cat /dev/mtd2 &gt;/tmp/eeprom.bin
3.  TTL更换uboot
4.  刷op固件和之前备份的eeprom
5.  完成
