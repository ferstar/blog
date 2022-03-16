---
title: "Cloudflare Argo Tunnels+Brook 一种非主流的科学上网姿势"
date: "2022-03-16T23:10:03+08:00"
tags: ['Idea']
comments: true
---

先把用到的东西摆出来:

1. https://blog.cloudflare.com/argo-tunnels-that-live-forever/
2. https://txthinking.github.io/brook/#/brook-wsserver

用`Cloudflare Argo Tunnels`(以下简称`cft`)的目的主要是薅`Cloudflare`的`CDN`网络为自己的垃圾`VPS`加速

食用方法:

1. 把上面两样东西装好
2. [启动 cft](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/) `cloudflared tunnel run --url http://localhost:8888 hello`
3. 启动 brook ws: `brook wsserver --listen 127.0.0.1:8888 --password auok`
4. 虽然小众, 但基本该有的[客户端](https://txthinking.github.io/brook/#/install-gui-client)都有
5. 注意客户端需要以 wss 的方式链接, 因为要过 cft

优点:

1. 背靠 cft , VPS 的 IP 几乎不可能被封
2. 如果你的 VPS 恰好是那种纯 docker 型或者网络出口有限制(有v6无v4)的话, `cft`也能帮你突破`VPS`所在域的网络限制
3. 有 CDN 加持, 垃圾线路也可以轻松满速
4. 相比 ss/v2ray 这种盛名在外的方案, brook ws 还是个小众的东西, 墙也许不那么敏感

缺点:

1. 延时高(>500ms), 所以不适合臭打游戏的
2. `cft`当前免费有 1TB/month 的流量, 但不确定未来收费水平
3. 移动端比较耗电



```
# NOTE: I am not responsible for any expired content.
create@2022-03-16T23:10:03+08:00
update@2022-03-16T23:28:44+08:00
comment@https://github.com/ferstar/blog/issues/56
```
