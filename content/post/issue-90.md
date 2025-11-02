---
title: "2025年了，为什么我还要root？"
date: "2025-10-04T14:42:47+08:00"
tags: ['Android']
comments: true
---

先列个单子，慢填（排名不分先后）

## 1. 我希望有新的内核特性，榨干硬件性能

厂商为了稳定性通常用老内核，但新内核有不少好东西：

- BBRv2 拥塞控制，联通4G网速提升明显
- f2fs 文件系统优化，配合 UFS 3.1 随机读写有感提升
- zstd 压缩的 ZRAM，压缩比比 lz4 高 20%+
- 自定义 CPU 调度器（试过 EAS），日常使用功耗降低 15% 左右

实际编译过 xaga 和 RMX3888 的内核，开了一堆厂商关掉的 feature，配合 KernelSU 比 Magisk 稳定。

工具：Franco Kernel Manager / UKMM

## 2. 干掉云控，防止厂商施法负优化

厂商最恶心的几个操作：
- OTA 后偷偷改配置（120Hz 变回 60Hz）
- 游戏识别后CPU降频（明明温度还低）
- 强推广告和全家桶app
- 收集隐私数据上传

我的做法：
```bash
# 冻结系统更新
pm disable com.xxx.ota

# hosts 屏蔽云控域名
echo "127.0.0.1 cloud.manufacturer.com" >> /system/etc/hosts

# LSPosed hook 系统服务拦截配置下发
```

实用模块：CorePatch（绕签名校验）、Shamiko（隐藏root）

## 3. 不想被特定生态绑定，迫不得已需要对某些app伪装机型

某些银行app限制机型（尤其国际版ROM），某些游戏锁区域，还有薅羊毛限定机型的

技术上就是 hook `android.os.Build` 类：
```java
XposedHelpers.setStaticObjectField(Build.class, "MODEL", "SM-G9980");
XposedHelpers.setStaticObjectField(Build.class, "MANUFACTURER", "samsung");
```

或者用现成的模块：Device Faker / Hide My Applist

## 4. 自动化记账（OCR、无障碍这种稳定性太差了，lsposed hook才是王道）

试过几种方案：
- 通知栏提取：漏记、重复记严重
- OCR识别：复杂场景识别率感人
- 无障碍服务：被系统kill是家常便饭

最后还是 LSPosed hook 靠谱，直接 hook 支付结果回调：
```java
// Hook 微信支付成功回调
findAndHookMethod("com.tencent.mm.plugin.wallet...", "onPaySuccess", 
    new XC_MethodHook() {
        protected void afterHookedMethod(MethodHookParam param) {
            // 拿到金额、商户等信息直接入库
            saveTransaction(param);
        }
    });
```

准确率100%，跑在app进程里不会被杀，还能区分支付/退款/红包

参考项目：AutoAccounting（开源）

## 5. 去广告

分几个层次：

**系统层面**：
- AdAway：hosts方式
- 精简内置广告apk（System/app下一堆）

**应用层面**：
- LSPosed + 各种去广告模块
- ReVanced（YouTube无广告）
- Bilibili HD（首页清爽不少）

**网络层面**：
```bash
# iptables 拦截广告域名
iptables -A OUTPUT -d ad.xxx.com -j REJECT

# 或者透明代理 + AdGuard DNS
```

激进点的可以反编译SystemUI去掉负一屏广告，重新打包刷入

## 6. CPU/GPU降压，调教续航

原理：同频率降低电压 = 降低功耗和发热

每颗 SoC 体质不同，我的 8 Gen2 测试结果：
```
原厂：大核 3.2GHz @ 1.05V, GPU 680MHz @ 0.90V
降压：大核 3.2GHz @ 0.98V (-70mV), GPU 680MHz @ 0.85V (-50mV)
效果：续航提升约 18%，温度降 2-3℃
```

操作方式：
- 改内核 device tree 电压表（需要重新编译）
- Franco Kernel Manager 实时调整（方便）

监控工具：CPU Float（实时频率温度）

## 7. 解温控、魔改充电协议

### 温控

厂商温控太保守，45℃就开始降频，实际芯片耐受温度在85℃以上

修改 `/sys/class/thermal/` 配置，提高降频阈值到 55℃左右
```bash
# 查看温控策略
cat /sys/class/thermal/thermal_zone*/temp

# 修改降频阈值（需要改内核或开机脚本）
echo 55000 > /sys/class/thermal/thermal_zone0/trip_point_0_temp
```

### 充电

限制充电功率保护电池（长期插电的设备）：
```bash
# 限制充电电流 2A
echo 2000000 > /sys/class/power_supply/battery/constant_charge_current_max

# 充到80%停止
echo 80 > /sys/class/power_supply/battery/charge_control_limit
```

实用模块：ACC (Advanced Charging Controller)，支持定时充电、智能充电等

## 8. Termux 完全体

无 root 的 Termux 限制太多：
- 不能访问 /data, /system
- 不能绑定 80/443 端口
- 不能用 tcpdump/iptables
- 某些系统调用受限

root 后解锁：
```bash
# 完整 Linux 发行版
proot-distro install debian

# 抓包分析
tcpdump -i wlan0 -w capture.pcap

# 跑 nginx 绑定 80 端口
nginx -c /data/nginx.conf

# 备份分区
dd if=/dev/block/by-name/boot of=/sdcard/boot.img

# 刷自编译内核
dd if=/sdcard/custom_boot.img of=/dev/block/by-name/boot
```

配合 Tasker 可以做很多自动化，比如：
- 连特定WiFi时启动 SSH/Samba
- 监控电池温度自动调性能
- 定时清理缓存、备份数据

---

## 总结

2025年root依然是刚需，主要是：
- 性能压榨（自定义内核）
- 隐私保护（去云控、去广告）
- 功能扩展（自动化、跨生态）
- 学习成长（系统底层知识）

当然也有风险：
- 保修失效（已过保无所谓）
- 安全风险（别乱授权）
- OTA升级麻烦（习惯手动刷）
- 部分app检测root（Shamiko能绕过大部分）

我的策略：**主力机保守，备机折腾**

折腾的过程本身就是学习和乐趣所在



---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-10-04T14:42:47+08:00
Updated at: 2025-11-02T06:52:43+08:00
Origin issue: https://github.com/ferstar/blog/issues/90
```
