---
title: "python处理二进制数据"
date: "2015-09-18T09:29:00+08:00"
tags: ['OTHERS']
comments: true
---


<http://pymotw.com/2/struct/index.html>
3.x的修正版
原地址的sample太老旧2.7x, 已经不适用于3.x, 我修正了下, 3.x测试通过
```python
#!/usr/bin/env python3
import struct
import binascii
values = (1, b'ab', 2.7)
s = struct.Struct('I 2s f')
packed_data = s.pack(*values)
print('Original values:', values)
print('Format string  :', s.format)
print('Uses           :', s.size, 'bytes')
print('Packed Value   :', binascii.hexlify(packed_data))
```
终端输出应该是这样的
```
$ python3 struct_pack.py 
Original values: (1, b'ab', 2.7)
Format string  : b'I 2s f'
Uses           : 12 bytes
Packed Value   : b'0100000061620000cdcc2c40'
```
解包，应该是这样:
```python
#!/usr/bin/env python3
 
import struct
import binascii
 
packed_data = binascii.unhexlify('0100000061620000cdcc2c40')
 
s = struct.Struct('I 2s f')
unpacked_data = s.unpack(packed_data)
print('Unpacked Values:', unpacked_data)
```
输出结果:
```
$ ./struct_unpack.py 
Unpacked Values: (1, b'ab', 2.700000047683716)
```
struct_endianness.py
```python
#!/usr/bin/env python3
import struct
import binascii
values = (1, b'ab', 2.7)
print('Original values:', values)
endianness = [
    ('@', 'native, native'),
    ('=', 'native, standard'),
    ('<', 'little-endian'),
    ('>', 'big-endian'),
    ('!', 'network'),
    ]
for code, name in endianness:
    s = struct.Struct(code + ' I 2s f')
    packed_data = s.pack(*values)
    print
    print('Format string  :', s.format, 'for', name)
    print('Uses           :', s.size, 'bytes')
    print('Packed Value   :', binascii.hexlify(packed_data))
    print('Unpacked Value :', s.unpack(packed_data))
```
运行结果:
```
./struct_endianness.py 
Original values: (1, b'ab', 2.7)
Format string  : b'@ I 2s f' for native, native
Uses           : 12 bytes
Packed Value   : b'0100000061620000cdcc2c40'
Unpacked Value : (1, b'ab', 2.700000047683716)
Format string  : b'= I 2s f' for native, standard
Uses           : 10 bytes
Packed Value   : b'010000006162cdcc2c40'
Unpacked Value : (1, b'ab', 2.700000047683716)
Format string  : b'< I 2s f' for little-endian
Uses           : 10 bytes
Packed Value   : b'010000006162cdcc2c40'
Unpacked Value : (1, b'ab', 2.700000047683716)
Format string  : b'> I 2s f' for big-endian
Uses           : 10 bytes
Packed Value   : b'000000016162402ccccd'
Unpacked Value : (1, b'ab', 2.700000047683716)
Format string  : b'! I 2s f' for network
Uses           : 10 bytes
Packed Value   : b'000000016162402ccccd'
Unpacked Value : (1, b'ab', 2.700000047683716)
```
Buffers
```python
#!/usr/bin/env python3
import struct
import binascii
s = struct.Struct('I 2s f')
values = (1, b'ab', 2.7)
print('Original:', values)
print
print('ctypes string buffer')
import ctypes
b = ctypes.create_string_buffer(s.size)
print('Before  :', binascii.hexlify(b.raw))
s.pack_into(b, 0, *values)
print('After   :', binascii.hexlify(b.raw))
print('Unpacked:', s.unpack_from(b, 0))
print
print('array')
import array
a = array.array('u', '\0' * s.size)
print('Before  :', binascii.hexlify(a))
s.pack_into(a, 0, *values)
print('After   :', binascii.hexlify(a))
print('Unpacked:', s.unpack_from(a, 0))
```
运行结果: 
```
./struct_buffers.py
Original: (1, b'ab', 2.7)
ctypes string buffer
Before  : b'000000000000000000000000'
After   : b'0100000061620000cdcc2c40'
Unpacked: (1, b'ab', 2.700000047683716)
array
Before  : b'000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
After   : b'0100000061620000cdcc2c40000000000000000000000000000000000000000000000000000000000000000000000000'
Unpacked: (1, b'ab', 2.700000047683716)
```
实战应用: 
读写二进制数组数据
<http://python3-cookbook.readthedocs.org/zh_CN/latest/c06/p11_read_write_binary_arrays_of_structures.html>
server.py
```python
#!/usr/bin/env python3
import socketserver, subprocess, sys
from threading import Thread
import struct
HOST = ''
PORT = 9527
BUF_SIZE = 1024
def unpack_records(data):
    '''
    解码
    '''
    # 从头部取得str长度
    llen = struct.unpack_from('!I', data, 0)[0]
    # 略过头部4byte取出x,y,body部分内容
    text = struct.unpack_from('!II%ds' % llen, data, 4)
    return text
class SingleTCPHandler(socketserver.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def handle(self):
        # self.request is the client connection
        print('client connected:', self.client_address)
        data = self.request.recv(BUF_SIZE)
        text = unpack_records(data)
        print("Received: {}".format(data))
        print("x = ", text[0])
        print("y = ", text[1])
        print("str is", bytes.decode(text[2]))
        self.request.send("{}".format(text).encode())
class SimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True
if __name__ == "__main__":
    server = SimpleServer((HOST, PORT), SingleTCPHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
```
client.py
```python
#!/usr/bin/env python3
import socket
import struct
import sys
BUF_SIZE = 1024
server_addr = ('127.0.0.1', 9527)
x = 1234
y = 4321
str = 'Hello, I\'m Baymax!'
def pack_records(x, y, str):
    '''
    编码整形
    4byte int len/4byte int x/4byte int y/{len}byte string body
    '''
    llen = len(str)
    values = (llen, x, y, bytes(str, 'utf8'))
    format = struct.Struct('!I I I %ds' % llen)
    data = format.pack(*values)
    return data
try :
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as msg :
    print("Creating Socket Failure. Error Code : " + str(msg[0]) + " Message : " + msg[1])
    sys.exit()
try:
    client.connect(server_addr)
    data = pack_records(x, y, str)
    client.sendall(data)
    received = client.recv(BUF_SIZE).decode()
finally:
    client.close()
print ("Sent: {}".format(data))
print ("Received: {}".format(received))
```