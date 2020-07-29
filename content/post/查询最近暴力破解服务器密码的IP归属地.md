---
title: "查询最近暴力破解服务器密码的IP归属地"
date: "2017-06-12T14:33:00+08:00"
tags: ['PYTHON', 'SHELL', 'LINUX']
comments: true
---


查询最近暴力破解服务器密码的IP归属地

```shell
cat /var/log/secure | awk '/Failed/ {print $(NF-3)}' > ip_list.txt
```

然后查询

```shell
python ip_query.py -i ip_list.txt -o out.csv
```

就是利用淘宝IP地址查询API挨个把IP地址归属地查询一遍，结果放在`csv`文件中，`Excel`打开长这样

![](~/14-41-30.jpg)

> 附: [ip_query.py](https://github.com/ferstar/learnote/tree/master/%E6%89%B9%E9%87%8F%E6%9F%A5%E8%AF%A2IP%E5%BD%92%E5%B1%9E%E5%9C%B0%E8%84%9A%E6%9C%AC)
