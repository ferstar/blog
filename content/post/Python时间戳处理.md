---
date = "2017-07-24T16:05:00+08:00"
title = "Python时间戳处理"
tags = ['PYTHON']
---

> 转自 [python 时间戳处理](http://funhacks.net/2016/03/19/python%20%E6%97%B6%E9%97%B4%E6%88%B3%E5%A4%84%E7%90%86/)

# 1. python 时间戳处理

[Unix 时间戳](http://funhacks.net/2015/04/29/Unix-timestamp/)根据精度的不同，有 10 位（秒级），13 位（毫秒级），16 位（微妙级）和 19 位（纳秒级）。在 python 中，我们可以将一个整数的时间戳转换为字符串格式，如 `'2016-02-25 20:21:04'`，也可以将其转换为 python 中的[datetime](https://docs.python.org/2/library/datetime.html) 格式。反之，也可以将整数的时间戳转换为字符串格式和 datetime 格式。用图展示如下：

``` shell
             +------------+             
             | timestamp  |             
       +---->|            |<-----+      
       |     +------------+      |      
       |                         |      
       |                         |      
       |                         |      
       v                         v      
+------------+            +------------+
|  datetime  |            |   string   |
|            |<---------->|            |
+------------+            +------------+
```

要注意的是，由于每个时区都有自己的本地时间（北京在东八区），因此也产生了世界标准时间（UTC, Universal Time Coordinated）。所以，在将一个时间戳转换为普通时间（比如 2016-01-01 12:00:00）时，要注意是要本地时区的时间还是世界时间等。

# 2. local time (北京时间)

```python
# -*- coding: utf-8 -*-

import time
from datetime import datetime

def timestamp_to_strtime(timestamp):
    """将 13 位整数的毫秒时间戳转化成本地普通时间 (字符串格式)

    :param timestamp: 13 位整数的毫秒时间戳 (1456402864242)
    :return: 返回字符串格式 {str}'2016-02-25 20:21:04.242000'
    """
    local_str_time = datetime.fromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')
    return local_str_time

def timestamp_to_datetime(timestamp):
    """将 13 位整数的毫秒时间戳转化成本地普通时间 (datetime 格式)

    :param timestamp: 13 位整数的毫秒时间戳 (1456402864242)
    :return: 返回 datetime 格式 {datetime}2016-02-25 20:21:04.242000
    """
    local_dt_time = datetime.fromtimestamp(timestamp / 1000.0)
    return local_dt_time

def datetime_to_strtime(datetime_obj):
    """将 datetime 格式的时间 (含毫秒) 转为字符串格式

    :param datetime_obj: {datetime}2016-02-25 20:21:04.242000
    :return: {str}'2016-02-25 20:21:04.242'
    """
    local_str_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
    return local_str_time

def datetime_to_timestamp(datetime_obj):
    """将本地(local) datetime 格式的时间 (含毫秒) 转为毫秒时间戳

    :param datetime_obj: {datetime}2016-02-25 20:21:04.242000
    :return: 13 位的毫秒时间戳  1456402864242
    """
    local_timestamp = long(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
    return local_timestamp

def strtime_to_datetime(timestr):
    """将字符串格式的时间 (含毫秒) 转为 datetiem 格式

    :param timestr: {str}'2016-02-25 20:21:04.242'
    :return: {datetime}2016-02-25 20:21:04.242000
    """
    local_datetime = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S.%f")
    return local_datetime

def strtime_to_timestamp(local_timestr):
    """将本地时间 (字符串格式，含毫秒) 转为 13 位整数的毫秒时间戳

    :param local_timestr: {str}'2016-02-25 20:21:04.242'
    :return: 1456402864242
    """
    local_datetime = strtime_to_datetime(local_timestr)
    timestamp = datetime_to_timestamp(local_datetime)
    return timestamp

def current_datetime():
    """返回本地当前时间, 包含datetime 格式, 字符串格式, 时间戳格式

    :return: (datetime 格式, 字符串格式, 时间戳格式)
    """
    # 当前时间：datetime 格式
    local_datetime_now = datetime.now()

    # 当前时间：字符串格式
    local_strtime_now = datetime_to_strtime(local_datetime_now)

    # 当前时间：时间戳格式 13位整数
    local_timestamp_now = datetime_to_timestamp(local_datetime_now)

    return local_datetime_now, local_strtime_now, local_timestamp_now


if __name__ == '__main__':

    time_str = '2016-02-25 20:21:04.242'

    timestamp1 = strtime_to_timestamp(time_str)
    datetime1 = strtime_to_datetime(time_str)

    time_str2 = datetime_to_strtime(datetime1)
    timestamp2 = datetime_to_timestamp(datetime1)

    datetime3 = timestamp_to_datetime(timestamp2)
    time_str3 = timestamp_to_strtime(timestamp2)

    current_time = current_datetime()

    print 'timestamp1: ', timestamp1
    print 'datetime1: ', datetime1
    print 'time_str2: ', time_str2
    print 'timestamp2: ', timestamp2
    print 'datetime3: ', datetime3
    print 'time_str3: ', time_str3

    print 'current_time: ', current_time
```

```shell
# 输出
timestamp1:  1456402864242
datetime1:  2016-02-25 20:21:04.242000
time_str2:  2016-02-25 20:21:04.242000
timestamp2:  1456402864242
datetime3:  2016-02-25 20:21:04.242000
time_str3:  2016-02-25 20:21:04.242000
current_time:  (datetime.datetime(2016, 3, 19, 14, 11, 4, 901903), '2016-03-19 14:11:04.901903', 1458367864901L)
```

# 3. utc time

```python
# -*- coding: utf-8 -*-

import calendar
from datetime import datetime

def timestamp_to_utc_strtime(timestamp):
    """将 13 位整数的毫秒时间戳转化成 utc 时间 (字符串格式，含毫秒)

    :param timestamp: 13 位整数的毫秒时间戳 (1456402864242)
    :return: 返回字符串格式 {str}'2016-02-25 12:21:04.242000'
    """
    utc_str_time = datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')
    return utc_str_time

def timestamp_to_utc_datetime(timestamp):
    """将 13 位整数的毫秒时间戳转化成 utc 时间 (datetime 格式)

    :param timestamp: 13 位整数的时间戳 (1456402864242)
    :return: 返回 datetime 格式 {datetime}2016-02-25 12:21:04.242000
    """
    utc_dt_time = datetime.utcfromtimestamp(timestamp / 1000.0)
    return utc_dt_time

def utc_datetime_to_timestamp(utc_datetime):
    """将 utc 时间 (datetime 格式) 转为 utc 时间戳

    :param utc_datetime: {datetime}2016-02-25 20:21:04.242000
    :return: 13位 的毫秒时间戳 1456431664242
    """
    utc_timestamp = long(calendar.timegm(utc_datetime.timetuple()) * 1000.0 + utc_datetime.microsecond / 1000.0)
    return utc_timestamp

def datetime_to_strtime(datetime_obj):
    """将 datetime 格式的时间 (含毫秒) 转为字符串格式

    :param datetime_obj: {datetime}2016-02-25 20:21:04.242000
    :return: {str}'2016-02-25 20:21:04.242'
    """
    local_str_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
    return local_str_time

def strtime_to_datetime(timestr):
    """将字符串格式的时间 (含毫秒) 转为 datetiem 格式

    :param timestr: {str}'2016-02-25 20:21:04.242'
    :return: {datetime}2016-02-25 20:21:04.242000
    """
    local_datetime = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S.%f")
    return local_datetime

def utc_strtime_to_timestamp(utc_timestr):
    """将 utc 时间 (字符串格式) 转为 13 位的时间戳

    :param utc_timestr: {str}'2016-02-25 20:21:04.242'
    :return: 1456431664242
    """
    # 先将字符串的格式转为 datetime 格式
    utc_datetime = strtime_to_datetime(utc_timestr)

    # 再将 datetime 格式的时间转为时间戳
    timestamp = utc_datetime_to_timestamp(utc_datetime)
    return timestamp

def utc_current_datetime():
    """返回 utc 当前时间, datetime 格式, 字符串格式, 时间戳格式

    :return: (datetime 格式, 字符串格式, 时间戳格式)
    """
    # utc 当前时间: datetime 格式
    utc_datetime_now = datetime.utcnow()

    # utc 当前时间: 字符串格式
    utc_strtime_now = datetime_to_strtime(utc_datetime_now)

    # utc 当前时间: 时间戳格式 13位整数
    utc_timestamp_now = utc_datetime_to_timestamp(utc_datetime_now)

    return utc_datetime_now, utc_strtime_now, utc_timestamp_now


if __name__ == '__main__':

    time_str = '2016-02-25 20:21:04.242'

    # 1456431664242
    timestamp1 = utc_strtime_to_timestamp(time_str)
    datetime1 = strtime_to_datetime(time_str)

    time_str2 = datetime_to_strtime(datetime1)
    timestamp2 = utc_datetime_to_timestamp(datetime1)

    datetime3 = timestamp_to_utc_datetime(timestamp2)
    time_str3 = timestamp_to_utc_strtime(timestamp2)

    utc_current_time = utc_current_datetime()

    print 'timestamp1: ', timestamp1
    print 'datetime1: ', datetime1
    print 'time_str2: ', time_str2
    print 'timestamp2: ', timestamp2
    print 'datetime3: ', datetime3
    print 'time_str3: ', time_str3

    print 'utc_current_time: ', utc_current_time
```

```shell
# 输出
timestamp1:  1456431664242
datetime1:  2016-02-25 20:21:04.242000
time_str2:  2016-02-25 20:21:04.242000
timestamp2:  1456431664242
datetime3:  2016-02-25 20:21:04.242000
time_str3:  2016-02-25 20:21:04.242000
utc_current_time:  (datetime.datetime(2016, 3, 19, 7, 7, 2, 217055), '2016-03-19 07:07:02.217055', 1458371222217L)
```

# 4. 参考资料

- [python-datetime-time-conversions](http://www.saltycrane.com/blog/2008/11/python-datetime-time-conversions/)