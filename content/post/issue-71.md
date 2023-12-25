---
title: "gRPC小记"
date: "2023-01-24T01:23:27+08:00"
tags: ['Linux', 'Python']
comments: true
---

老早前给公司内部写了一个 gRPC 小框架叫 aipod，主要是做模型的搬运工，数据流向大概是这样：

`model <-->[train/predict/log]<--> aipod <--> web app`

本来是个小玩意，基本跑的还算愉快，但是随着业务发展，传输的数据到M再到G级别时，问题出现了，各种花式断连，不得不重构之，主要干了这么些事情：

1. 改进默认配置
2. 改变传输模式：从简单`Unary RPC`到`Bidirectional Streaming RPC`
3. 同步改异步，支持更高的并发
4. zstd 压缩
5. 引入万能方法，解决多 aipod 实例无法被同 Nginx 分流&负载均衡的问题

### 改配置

实际部署中其实你根本不知道前面会套多少层类似 Nginx 的代理，任意一层超时链接就会被掐掉，所以这里的配置主要是为了降低不必要的断连而准备的，另外增加了超时重试的机制。我直接贴代码，就不解释了

```shell
json_config = json.dumps(
    # https://github.com/grpc/proposal/blob/master/A6-client-retries.md
    # https://docs.microsoft.com/en-us/aspnet/core/grpc/retries?view=aspnetcore-6.0#streaming-calls
    {
        "methodConfig": [
            {
                "name": [{"service": "ai.AI"}],
                "retryPolicy": {
                    "maxAttempts": 5,
                    "initialBackoff": "1s",
                    "maxBackoff": "30s",
                    "backoffMultiplier": 2,
                    "retryableStatusCodes": [
                        grpc.StatusCode.INTERNAL.name,
                        grpc.StatusCode.UNAVAILABLE.name,
                        grpc.StatusCode.UNKNOWN.name,
                    ],
                },
                # "retryThrottling":{
                #     "maxTokens": 10,
                #     "tokenRatio": 0.1
                # }
            }
        ]
    }
)
COMMON_OPTIONS = (
    # default is -1, which is unlimited
    ("grpc.max_send_message_length", -1),
    ("grpc.max_receive_message_length", -1),
    ("grpc.default_compression_algorithm", CompressionAlgorithm.gzip),
    ("grpc.grpc.default_compression_level", CompressionLevel.high),
    # References:
    # https://grpc.github.io/grpc/core/group__grpc__arg__keys.html
    # https://cs.mcgill.ca/~mxia3/2019/02/23/Using-gRPC-in-Production
    # https://gist.github.com/xiamx/6f5258511dc9180d3279adef4ffb212a
    # send keepalive ping every 5 second, default is 2 hours
    ("grpc.keepalive_time_ms", 5000),
    # keepalive ping time out after 120 seconds, default is 20 seconds
    ("grpc.keepalive_timeout_ms", 120000),
    # allow keepalive pings when there's no gRPC calls
    ("grpc.keepalive_permit_without_calls", True),
    # allow unlimited amount of keepalive pings without data
    ("grpc.http2.max_pings_without_data", 0),
    # allow grpc pings from client every 5 seconds
    ("grpc.http2.min_time_between_pings_ms", 5000),
    # allow grpc pings from client without data every 5 seconds
    ("grpc.http2.min_ping_interval_without_data_ms", 5000),
)

DEFAULT_CLIENT_OPTIONS = COMMON_OPTIONS + (
    ("grpc.enable_retries", 1),
    ("grpc.service_config", json_config),
)
DEFAULT_SERVER_OPTIONS = COMMON_OPTIONS + (
    # 0 allows the server to accept any number of bad pings
    ("grpc.http2.max_ping_strikes", 0),
)
```

### 改传输模式

还是为了解决长阻塞任务被中断的问题，关于 Unary RPC 转 Bidirectional Streaming RPC 官方文档都有详细的解释，这里不赘述。本来正常的操作应该是想办法避免、降低长阻塞任务，尽量在超时范围内返回任务结果，但实际上你根本不知道调用方的任务是什么玩意，比如一个预测任务，抠搜客户只给配 CPU 那跑个大几十秒十几分钟都是稀松平常，完全无法控制，也根本无法定一个相对安全的超时时间。所以只能从自己身上下刀了：**分一个线程出来，专门负责给客户端响应心跳，另一个线程等待阻塞任务结束。**这样你甚至不用关心中间到底过多少 Nginx，每个节点的超时时间是多少，再低也不会低于1秒吧？只要下游真正写好异步任务，不阻塞 IO，那么就不会被掐掉链接。

```python
async def chaos(self, request_iter, context):
    raw = Raw(data=b"")
    with tempfile.TemporaryDirectory() as tmp_dir:
        await asyncio.gather(
            self._receive_stream(context, request_iter, raw, tmp_dir),  # 这个方法负责等待阻塞任务结束，收结果。
            self._send_stream(context, raw),
        )

@staticmethod
async def _send_stream(context, var: Raw):
    while not var.data:
        # 没结果就一直发心跳包给客户端
        await context.write(Raw(data=PONG.encode()))
        await asyncio.sleep(1)
    await context.write(var)
```

### 改异步

这个没说的，别让 CPU 闲着嘛，多浪费。gRPC 官网有很好的示例代码，我顺路增加了 health check 以及 graceful shutdown 支持。

```python
def _configure_maintenance_server(
    server: grpc.Server, address: str
) -> health.HealthServicer:
    server.add_insecure_port(address)
    # Create a health check servicer. We use the non-blocking implementation
    # to avoid thread starvation.
    health_servicer = health.HealthServicer()

    # Create a tuple of all the services we want to export via reflection.
    services = tuple(
        service.full_name for service in ai_pb2.DESCRIPTOR.services_by_name.values()
    ) + (reflection.SERVICE_NAME, health.SERVICE_NAME)

    # Mark all services as healthy.
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    for service in services:
        health_servicer.set(service, health_pb2.HealthCheckResponse.SERVING)
    reflection.enable_server_reflection(services, server)
    return health_servicer


async def sig_handler(serve_instance: "Serve", sig_num):
    logger.warning("Signal number: %s received, shutting down...", sig_num)
    serve_instance.health_servicer.enter_graceful_shutdown()
    serve_instance.model_instance.instance_pool.enter_graceful_shutdown()
    while serve_instance.model_instance.instance_pool.pool:
        if serve_instance.model_instance.instance_pool.release():
            break
        logger.warning("Waiting for model instance to be released...")
        await asyncio.sleep(1)
    await serve_instance.server.stop(30)
    logger.info("RPC server shutdown complete")



class Server:
    ...
    async def __aenter__(self):
        self.server = grpc.aio.server(
            futures.ThreadPoolExecutor(
                max_workers=self.rpc_max_workers or None,
            ),
            options=merge_options(DEFAULT_SERVER_OPTIONS, self.options),
        )
        self.model_instance = AIServicer(self.model)
        self.clear_work_dirs(self.model_instance.instance_pool.datapath)
        ai_pb2_grpc.add_AIServicer_to_server(self.model_instance, self.server)
        self.server.add_insecure_port(self.address)
        self.health_servicer = _configure_maintenance_server(self.server, self.address)
        await self.server.start()
        logger.info(f"listening address: {self.address}")
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(sig_handler(self, s))
            )
        return self
```

### zstd 压缩

这玩意比 gzip 压缩率大还快，没理由不用，但 gRPC 暂时还没有支持，咋办？魔改呗，把大二机制参数值用 zstd 自己压一遍，收的时候再解就 OK，虽然费了手续，但能省可观的网络 IO，可太值了。

```python
# 发
def _prepare_stream_data(
    self, binary_data: Union[bytes, Path, str], *, raw_input=False, **kwargs
) -> Generator[Union[Raw, StreamInput], None, None]:
    assert all(
        not k.startswith("_aipod") for k in kwargs
    ), 'The key argument must not start with "_aipod"'
    buffer_size = io.DEFAULT_BUFFER_SIZE * 4  # Usually 8k * 4
    cctx = zstandard.ZstdCompressor()
    if isinstance(binary_data, bytes):
        size = len(binary_data)
        if size > buffer_size:
            logger.warning(
                f"Binary data size {size} is larger than buffer size {buffer_size}, please pass the original path or iterable object instead of binary data"
            )
        bytes_io = io.BytesIO(binary_data)
        bytes_io.seek(0)
        bin_iter = cctx.read_to_iter(bytes_io, write_size=buffer_size)
    elif isinstance(binary_data, (str, Path)):
        path = Path(binary_data) if isinstance(binary_data, str) else binary_data
        size = path.stat().st_size
        bin_iter = read_in_zstd_chunks(path, cctx=cctx, chunk_size=buffer_size)
    else:
        raise TypeError(
            f'"binary_data" must be bytes, str or Path, got {type(binary_data)}'
        )
    kwargs_json = encode_data({**kwargs, BIN_SIZE_KEY: size}, cctx=cctx)
    if raw_input:
        yield Raw(data=kwargs_json)
        for chunk in bin_iter:
            yield Raw(data=chunk)
    else:
        # send params first
        yield StreamInput(
            kwargs_json=kwargs_json,
            version=self.version,
            raw=Raw(data=b""),
        )
        # then send binary data in chunks
        for chunk in bin_iter:
            yield StreamInput(
                kwargs_json=b"{}",
                version="",
                raw=Raw(data=chunk),
            )

    kw_len = len(kwargs_json)
    if kw_len > buffer_size:
        logger.warning(
            f"Kwargs size {kw_len} is larger than buffer size {buffer_size}, please use binary_data instead of kwargs to send large data"
        )

# 收
async def _receive_stream(self, context, request_iter, var: Raw, work_dir):
    meta = dict(context.invocation_metadata())
    logger.info(f"Got stream request: {meta}")
    kwargs = None
    model = None
    dctx = zstandard.ZstdDecompressor()
    lock = FileLock(os.path.join(work_dir, ".lock"))
    compressed_path = os.path.join(work_dir, "compressed")
    decompressed_path = os.path.join(work_dir, "decompressed")
    with lock:
        with open(compressed_path, "wb") as file_obj:
            async for raw in request_iter:
                if kwargs is not None:
                    file_obj.write(raw.data)
                    continue
                kwargs = decode_data(raw.data, dctx=dctx)
                model = self.instance_pool.get(kwargs.get("version"))
                if not hasattr(model, meta.get("x-func-name", "chaos")):
                    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
                    context.set_details(
                        f"\"{model.__class__}.{meta.get('x-func-name', 'chaos')}\" not implemented yet"
                    )
                    var.data = PONG.encode()
                    return
        with open(compressed_path, "rb") as file_in, open(
            decompressed_path, "wb"
        ) as file_out:
            for chunk in dctx.read_to_iter(file_in):
                file_out.write(chunk)
        # 这里是我上面说的万能方法，客户端可以通过meta data选择服务端的func
        result = await getattr(model, meta["x-func-name"])(
            context, decompressed_path, **kwargs
        )
        var.data = encode_data(
            result.decode() if isinstance(result, bytes) else result
        )
```

### 多实例 Nginx 均衡

鉴于本框架带载能力太强，实测单次超4GB都稳如老狗，所以渐渐有他组产品也来套用，这时候问题来了：protocol 是固定的，假如我接了 xxx yyy zzz 三个模型，这三个模型不巧又同时被一个 Nginx 代理，他们的 location 是一样的`/ai.AI` 那咋分流呢？改 protocol 是不可能改的，我懒，走了另一条道，其实包括万能方法`chaos`以内，都已经体现在上面代码里了。剩下 Nginx 的配置简单提一下：

```shell
# x-func-name 可以指定 server 端用哪个方法来处理数据
# 至于数据处理以及不同服务分流、负载均衡等均可以利用 gRPC 的 metadata 功能由客户端自由控制（在服务端实现了相应功能`hello`的前提下）
# result = asyncio.run(model.chaos(bin_path, metadata=[('x-upstream', 'xxx'), ('x-func-name', 'hello')], **kwargs))

upstream xxx {
    server 192.168.90.9:1082;
    server 192.168.90.9:1083;
    keepalive 2000;
}

upstream yyy {
    server 192.168.90.10:1082;
    server 192.168.90.10:1083;
    keepalive 2000;
}

upstream zzz {
    server 192.168.90.11:1082;
    server 192.168.90.11:1083;
    keepalive 2000;
}

server {
    location /ai.AI/chaos {
        # 客户端可以通过 metadata.x-upstream 参数来指定具体的后端服务
        # 不指定默认为 chaos
        grpc_pass $http_x_upstream;
        grpc_read_timeout 600s;
        grpc_send_timeout 600s;
        grpc_socket_keepalive on;
        client_max_body_size 0;
    }
}
```

## gRPC Health Checking

参考：https://github.com/grpc/grpc/tree/master/examples/python/xds 实现了 Health Checking 支持，可以通过命令行工具`grpcurl`进行健康检查

```shell
> grpcurl --plaintext localhost:50051 grpc.health.v1.Health.Check

{
  "status": "SERVING"  // "NOT_SERVING"即表示该实例处于graceful shutdown状态, 不能再接受新的请求
}
```

使用 Nginx 时，可以参考：https://www.nginx.com/blog/nginx-plus-r23-released/#New-Features-in-Detail 为服务添加健康检查



```
# NOTE: I am not responsible for any expired content.
create@2023-01-24T01:23:27+08:00
update@2023-12-25T03:25:57+08:00
comment@https://github.com/ferstar/blog/issues/71
```
