---
title: "Upload Tmp File to Tmplink"
date: 2019-09-18T14:52:03+08:00
tags: ['PYTHON']
comments: false
---

> 这服务可能是要收费了, 最近不停的修改API, 蛋疼, 还好改一下还能用

```python
#!/usr/bin/env python3
import http.client
import json
import mimetypes
import os
import sys
from urllib.parse import quote
from uuid import uuid4


def read_in_chunks(file_object, chunk_size=1024):
    """
    Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k.
    """
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def body_iter(boundary, fields):
    for key, value in fields.items():
        yield '--{}\r\n'.format(boundary).encode('ascii')
        if key == 'file':
            yield 'Content-Disposition: form-data; name={}; filename={}\r\n'.format(key, quote(os.path.basename(value))).encode('ascii')
            file_type = mimetypes.guess_type(value)[0] or 'application/octet-stream'
            yield 'Content-Type: {}\r\n'.format(file_type).encode('ascii')
            yield '\r\n'.encode('ascii')
            if not os.path.isfile(value):
                sys.exit('File not found: {}'.format(value))
            with open(value, 'rb') as file_obj:
                for chunk in read_in_chunks(file_obj):
                    yield chunk
            yield '\r\n'.encode('ascii')
        else:
            yield 'Content-Disposition: form-data; name={}\r\n'.format(key).encode('ascii')
            yield '\r\n'.encode('ascii')
            yield '{}\r\n'.format(value).encode('ascii')
        yield '--{}--\r\n'.format(boundary).encode('ascii')


def upload_file(file_path):
    boundary = uuid4().hex
    headers = {'content-type': "multipart/form-data; boundary=%s" % boundary}
    conn = http.client.HTTPSConnection("connect.tmp.link")
    meta = {'action': 'token'}
    conn.request("POST", "/api_v2/user", body_iter(boundary, meta), headers)
    res = conn.getresponse()
    token = ''
    if res.code == 200:
        data = json.loads(res.read().decode("utf-8"))
        token = data.get('data')
    meta = {'action': 'upload', 'model': 0, 'token': token, 'file': file_path}
    conn.request("POST", "/api_v2/file", body_iter(boundary, meta), headers)
    res = conn.getresponse()
    if token and res.code == 200:
        data = json.loads(res.read().decode("utf-8"))
        if data.get('data', {}).get('url'):
            return 'Here is your temp link: ' + data['data'].get('url', '')
    return 'Something wrong with the tmp.link service'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: {} <file_path_you_want_to_upload>'.format(sys.argv[0]))
    print(upload_file(sys.argv[1]))

```
