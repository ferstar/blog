+++
date = "2017-07-27T17:41:00+08:00"
title = "random.org的随机数调用api"
tags = ['PYTHON', 'RANDOM']

+++

via: https://api.random.org/json-rpc/1/basic

这货号称是真随机, 看起来好屌的样子

API 使用一般都是两步

1. 申请`key`

   点右上角那个`Get Beta Key`即可, 需要填个邮箱接收`key`

2. 调`HTTP request`参数

   直接放码

   ```python
   import requests
   import json

   url = "https://api.random.org/json-rpc/1/invoke"

   payload = {
       "jsonrpc": "2.0",
       "method": "generateIntegers",
       "params": {
           "apiKey": "4125d851-2fed-41c6-8fb4-9aa8ccb20bd7",  # key
           "n": 100,  # 希望获取多少个随机数
           "min": 100,  # 随机数从何开始
           "max": 150,  # 从何结束
           "replacement": True,
           "base": 10  # 进制
       },
       "id": 18289  # 暂时目测5位随机数
   }

   headers = {
       'content-type': "application/json",
       'cache-control': "no-cache"
   }

   response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
   print(json.loads(response.text))
   ```

   得到的正确响应大概是这样:

   ```shell
   {
       "jsonrpc": "2.0", 
       "result": {
           "random": {
               "data": [
                   108, 
                   125, 
                   133, 
                   149, 
                   112, 
                   101, 
                   123, 
                   101, 
                   103, 
                   135
               ], 
               "completionTime": "2017-07-27 09:49:04Z"
           }, 
           "bitsUsed": 57, 
           "bitsLeft": 22138, 
           "requestsLeft": 988, 
           "advisoryDelay": 210
       }, 
       "id": 18289
   }
   ```

   具体异常直接看官网文档