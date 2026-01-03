---
title: "百度在线翻译demo for Python3"
slug: "baidu-translate-api-python3-demo"
date: "2017-01-01T13:56:00+08:00"
tags: ['OTHERS']
comments: true
---


百度提供的demo是Python2，在Python3上各种报错，于是小改了下，凑合能用
via <http://api.fanyi.baidu.com/api/trans/product/apidoc>

```python
# /usr/bin/env python
# coding='utf8'

import http.client
import json
import random
from hashlib import md5
from urllib.parse import quote

appid = '20151113000005349'
secretKey = 'osubCEzlGjzvw8qdQc41'

myurl = '/api/trans/vip/translate'
q = 'Long time no see'
fromLang = 'en'
toLang = 'zh'
salt = random.randint(32768, 65536)

sign = appid + q + str(salt) + secretKey
m1 = md5()
m1.update(sign.encode(encoding='utf-8'))
sign = m1.hexdigest()
myurl = myurl + '?appid=' + appid + '&q=' + quote(q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
    salt) + '&sign=' + sign

try:
    # httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
    httpClient = http.client.HTTPSConnection('fanyi-api.baidu.com')
    httpClient.request('GET', myurl)

    # response是HTTPResponse对象
    response = httpClient.getresponse()
    result = json.loads(response.read().decode(encoding='utf-8'))
    print(result)
    print(result['trans_result'][0]['dst'])
except Exception as e:
    print(e)
finally:
    if httpClient:
        httpClient.close()
```
打印结果：
```bash
{'from': 'en', 'to': 'zh', 'trans_result': [{'src': 'Long time no see', 'dst': '好久不见'}]}
好久不见
```
