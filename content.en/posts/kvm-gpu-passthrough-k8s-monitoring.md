---
title: "KVM GPU Passthrough and Single-Node K8s Monitoring"
slug: "kvm-gpu-passthrough-k8s-monitoring"
date: "2026-01-22T10:00:00+08:00"
tags: ["kvm","gpu","passthrough","kubernetes","prometheus","teleport","nvidia","ops"]
description: "GPU passthrough caused black screen and missing GPUs + tuned OVMF/PCI hole64/NUMA and wired monitoring + 8 GPUs with NVSwitch and metrics stable"
---

> I am not a native English speaker; this article was translated by AI.

This round was about a KVM VM on a GPU host: pass through 8 H800 GPUs and 4 NVSwitches, then run single-node K8s, GPU Operator, and Prometheus inside the VM.

The process was not fancy, but the traps were very familiar: black screen, not enough PCI resources, DHCP lease mismatch, and a ServiceMonitor label that did not line up. I am writing the path down in the order I debugged it, mostly so I do not have to dig through logs from scratch next time.

## Environment and goal

- Host: GPU node
- VM: `ubuntu_gpu` (KVM/libvirt, UEFI/OVMF)
- Goal: 8x H800 + 4x NVSwitch passthrough, GPU scheduling in single-node K8s, and DCGM metrics collected by Prometheus

## Rough troubleshooting path

{{< mermaid >}}
flowchart TD
  A[VM boot + GPU passthrough] --> B[Black screen / some GPUs fail to init]
  B --> C[Switch to non-Secure Boot OVMF]
  C --> D[Increase PCI hole64]
  D --> E[NUMA + vCPU pinning]
  E --> F[8 GPUs + NVSwitch OK]
  F --> G[K8s + GPU Operator + Prometheus]
  G --> H[DCGM metrics verified]
{{< /mermaid >}}

## 1. Black screen and PCI resource shortage

The first symptom looked scary: after GPU passthrough, VNC showed nothing, and the driver logs contained `PCI I/O region invalid`. For this kind of issue, I would not blame the driver too early. The 64-bit PCI hole on Q35 can be too small, especially with multiple GPUs plus NVSwitch.

I changed two things:

- switched OVMF to the non-secure version, to remove Secure Boot from the equation
- increased `pci-hole64-size` to 2048G

```xml
<!-- OVMF non-secure -->
<loader readonly='yes' type='pflash'>/usr/share/edk2/ovmf/OVMF_CODE.cc.fd</loader>

<!-- Q35 PCIe 64-bit hole -->
<qemu:commandline>
  <qemu:arg value='-global'/>
  <qemu:arg value='q35-pcihost.pci-hole64-size=2048G'/>
</qemu:commandline>
```

After that, GPU initialization and topology detection became normal. This option is easy to forget because most VMs never need it, but for multi-GPU passthrough it is one of the first places worth checking.

## 2. IP unreachable: just DHCP binding

There was also a very boring, very time-wasting network issue: the VM IP was unreachable. In the end, the NIC MAC had changed, so the DHCP binding no longer matched.

Restoring the old MAC brought the address back to `192.168.122.146`.

```bash
# old MAC
52:54:00:a9:a2:11
```

Logs are not always generous for this kind of problem. I had to compare the libvirt XML, DHCP lease, and routes by hand.

## 3. Memory, NUMA, and vCPU pinning

The VM memory was set to 256GB:

```xml
<memory unit='KiB'>268435456</memory>
<currentMemory unit='KiB'>268435456</currentMemory>
```

vCPUs were split into two groups and pinned to matching NUMA nodes. GPUs were placed according to NUMA locality as well. This does not always decide whether the VM can boot, but it does matter once real workloads start running, so I prefer to get it right early.

## 4. Verifying GPU, K8s, and monitoring

On the GPU side, check the devices, topology, and NVLink state:

```bash
nvidia-smi -L
nvidia-smi topo -m
nvidia-smi nvlink -s
```

On the K8s side, check the node and pods:

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

For Prometheus, query one DCGM metric directly:

```bash
curl http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_SM_CLOCK
```

If data comes back, the DCGM Exporter to Prometheus path is basically working.

## 5. Key config snippets

### containerd proxy

This machine cannot reach the public internet directly, so containerd needs a proxy for image pulls:

```ini
# /etc/systemd/system/containerd.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://100.64.0.5:8888"
Environment="HTTPS_PROXY=http://100.64.0.5:8888"
Environment="NO_PROXY=127.0.0.1,localhost,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10"
```

### GPU Operator and Prometheus

```bash
helm upgrade --install gpu-operator nvidia/gpu-operator \
  -n gpu-operator --create-namespace \
  --set driver.enabled=false --set dcgmExporter.enabled=true

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

### DCGM metrics into Prometheus

The easy-to-miss bit is the `ServiceMonitor` label. Prometheus usually only selects objects with the matching release label, so add it explicitly:

```bash
# ServiceMonitor must match Prometheus release label
kubectl -n gpu-operator label servicemonitor nvidia-dcgm-exporter release=kube-prometheus-stack --overwrite
```

## Notes for next time

- For multi-GPU passthrough failures, check OVMF and `pci-hole64-size` early
- Turn off Secure Boot while validating, otherwise there are too many variables
- If DHCP suddenly behaves strangely, verify whether libvirt changed the MAC
- Having DCGM Exporter running is not enough; the Prometheus `release` label must match

Most of the issues here were the annoying kind where one small config mismatch makes the whole thing look broken. Once fixed, the 8 GPUs, NVSwitches, single-node K8s, and monitoring path all stayed stable.