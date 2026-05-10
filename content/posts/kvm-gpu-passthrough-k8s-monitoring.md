---
title: "KVM GPU 直通与单节点 K8s 监控落地记录"
slug: "kvm-gpu-passthrough-k8s-monitoring"
date: "2026-01-22T10:00:00+08:00"
tags: ["kvm","gpu","passthrough","kubernetes","prometheus","teleport","nvidia","ops"]
description: "GPU 直通后黑屏且部分卡不可用 + 调整 OVMF/PCI hole64/NUMA 并完善监控链路 + 8 卡 NVSwitch 与指标采集稳定"
---

这次折腾的是一台 GPU 节点上的 KVM 虚拟机：把 8 张 H800 和 4 个 NVSwitch 直通进去，再在里面跑单节点 K8s、GPU Operator 和 Prometheus。

过程不复杂，但坑都挺经典：黑屏、PCI 资源不够、DHCP 租约乱掉、ServiceMonitor 标签没对上。这里按我实际排障顺序记一遍，免得下次又从头翻日志。

## 环境和目标

- 宿主机：GPU 节点
- 虚拟机：`ubuntu_gpu`（KVM/libvirt, UEFI/OVMF）
- 目标：8 卡 H800 + 4 NVSwitch 直通，单节点 K8s 能调度 GPU，Prometheus 能抓到 DCGM 指标

## 大致排障路线

{{< mermaid >}}
flowchart TD
  A[VM 启动 + GPU 直通] --> B[黑屏 / 部分 GPU 无法初始化]
  B --> C[切换 OVMF 非 Secure Boot]
  C --> D[扩大 PCI hole64]
  D --> E[NUMA + vCPU 亲和]
  E --> F[8 GPU + NVSwitch 正常]
  F --> G[K8s + GPU Operator + Prometheus]
  G --> H[DCGM 指标验证通过]
{{< /mermaid >}}

## 1. 黑屏和 PCI 资源不足

最开始的现象比较吓人：GPU 直通后 VNC 没画面，进系统后驱动日志里还能看到 `PCI I/O region invalid`。这类问题先别急着怀疑驱动，Q35 的 64-bit PCI hole 很容易不够用，尤其是多卡加 NVSwitch。

我这里做了两件事：

- OVMF 换成 non-secure 版本，先排除 Secure Boot 干扰
- 把 `pci-hole64-size` 拉到 2048G

```xml
<!-- OVMF non-secure -->
<loader readonly='yes' type='pflash'>/usr/share/edk2/ovmf/OVMF_CODE.cc.fd</loader>

<!-- Q35 PCIe 64-bit hole -->
<qemu:commandline>
  <qemu:arg value='-global'/>
  <qemu:arg value='q35-pcihost.pci-hole64-size=2048G'/>
</qemu:commandline>
```

改完后，GPU 初始化和拓扑识别就正常了。这个参数平时很少碰，一旦多卡直通出怪问题，值得优先看一眼。

## 2. IP 不通：其实是 DHCP 绑定

中间还遇到一个很没技术含量但很浪费时间的问题：虚拟机 IP 不通。最后发现是网卡 MAC 被改过，DHCP 绑定没匹配上。

恢复旧 MAC 后，地址回到 `192.168.122.146`。

```bash
# 旧 MAC
52:54:00:a9:a2:11
```

这种问题日志不会多热情地提醒你，只能老老实实把 libvirt XML、DHCP lease 和路由都对一遍。

## 3. 内存、NUMA 和 vCPU 亲和

虚拟机内存调到 256GB：

```xml
<memory unit='KiB'>268435456</memory>
<currentMemory unit='KiB'>268435456</currentMemory>
```

vCPU 分两组 pin 到对应 NUMA node，GPU 也按 NUMA 归属放置。多卡环境里这一步不一定决定能不能启动，但会影响后面跑任务时的稳定性和延迟，顺手做好比较省心。

## 4. 验证 GPU、K8s 和监控

GPU 侧先确认卡、拓扑和 NVLink：

```bash
nvidia-smi -L
nvidia-smi topo -m
nvidia-smi nvlink -s
```

K8s 侧确认节点和 Pod：

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

Prometheus 侧直接查一条 DCGM 指标：

```bash
curl http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_SM_CLOCK
```

能查到数据，说明 DCGM Exporter 到 Prometheus 这条链路基本通了。

## 5. 关键配置片段

### containerd 代理

这台机器没有直连外网，containerd 需要走代理拉镜像：

```ini
# /etc/systemd/system/containerd.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://100.64.0.5:8888"
Environment="HTTPS_PROXY=http://100.64.0.5:8888"
Environment="NO_PROXY=127.0.0.1,localhost,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10"
```

### GPU Operator 和 Prometheus

```bash
helm upgrade --install gpu-operator nvidia/gpu-operator \
  -n gpu-operator --create-namespace \
  --set driver.enabled=false --set dcgmExporter.enabled=true

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

### DCGM 指标接入 Prometheus

这里最容易漏的是 `ServiceMonitor` 标签。Prometheus 默认只抓自己 release 标签匹配的对象，所以要补上：

```bash
# ServiceMonitor 需要有与 Prometheus release 一致的标签
kubectl -n gpu-operator label servicemonitor nvidia-dcgm-exporter release=kube-prometheus-stack --overwrite
```

## 复盘

- 多 GPU 直通出问题，先看 OVMF 和 `pci-hole64-size`
- Secure Boot 先关掉验证，别把变量留太多
- DHCP 突然不对劲时，检查 MAC 是否被 libvirt 改过
- DCGM Exporter 有了不代表 Prometheus 能抓到，`release` 标签要对齐

这次的坑基本都是“配置差一点点就完全不工作”的类型。好在修完以后，8 卡、NVSwitch、单节点 K8s 和监控链路都稳定了。