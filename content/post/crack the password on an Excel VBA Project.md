---
title: "Crack the Password on an Excel VBA Project"
date: 2017-12-21T09:18:47+08:00
tags: ['OFFICE', 'VBA']
comments: true
---

昨天拿到一个xlsm文件，模板写的有点问题，打算修改下凑合用，然而发现工程有密码保护，于是Google一番，发现这个回答挺靠谱，完美解决：

[https://stackoverflow.com/a/31073075/6001263](https://stackoverflow.com/a/31073075/6001263)

粘一下步骤：

1. Change the extension of the `.xlsm` file to `.zip`.
2. Open the .zip file (with WinZip or WinRar etc) and go to the xl folder.
3. Extract the `vbaProject.bin` file and open it in a Hex Editor.
4. Search for `DPB` and replace with `DPx` and save the file.
5. Replace the old `vbaProject.bin` file with this new on in the zipped file.
6. Change the file extension back to `.xlsm`.
7. Open workbook skip through the warning messages.
8. Open up Visual Basic inside Excel.
9. Go to Tools > VBAProject Properties > Protection Tab.
10. Put in a new password and save the `.xlsm` file.
11. Close and re open and your new password will work.