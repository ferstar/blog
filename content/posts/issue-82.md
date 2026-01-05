---
title: "Build my own patched Ubuntu mainline kernel"
slug: "build-ubuntu-mainline-kernel"
date: "2025-01-12T16:16:49+08:00"
tags: ['Default']
comments: true
series: ["Kernel Development"]
---
记录下用 ubuntu-mainline-kernel.sh 编译打补丁内核的过程

## 背景

Ubuntu 官方内核太保守，想用 mainline 最新内核，但又需要打自己的补丁（比如硬件驱动、性能优化之类的）

找到个不错的工具：[ubuntu-mainline-kernel.sh](https://github.com/pimlie/ubuntu-mainline-kernel.sh)

## 工具介绍

这个脚本可以：
- 从 Ubuntu Kernel PPA 直接下载安装 mainline 内核
- 本地编译内核（实验性功能）
- 支持 SecureBoot 签名
- 自动检查新版本

⚠️ **警告**：mainline 内核不受官方支持，生产环境慎用，记得保留默认内核做备份

## 安装脚本

```bash
# 安装依赖
sudo apt install wget

# 下载脚本
wget https://raw.githubusercontent.com/pimlie/ubuntu-mainline-kernel.sh/master/ubuntu-mainline-kernel.sh

# 赋予执行权限
chmod +x ubuntu-mainline-kernel.sh

# 移动到系统路径
sudo mv ubuntu-mainline-kernel.sh /usr/local/bin/
```

## 常用命令

### 查看可用版本
```bash
# 列出所有远程版本
ubuntu-mainline-kernel.sh -r

# 包括 RC 版本
ubuntu-mainline-kernel.sh -r --rc

# 搜索特定版本
ubuntu-mainline-kernel.sh -r 6.8
```

### 安装预编译内核
```bash
# 安装指定版本
sudo ubuntu-mainline-kernel.sh -i 6.8.0

# 包括 RC 版本
sudo ubuntu-mainline-kernel.sh -i 6.8-rc5 --rc

# 安装 low-latency 版本（低延迟优化）
sudo ubuntu-mainline-kernel.sh -i 6.8.0 --low-latency
```

### 卸载内核
```bash
# 列出已安装的内核
ubuntu-mainline-kernel.sh -l

# 卸载指定版本
sudo ubuntu-mainline-kernel.sh -u 6.8.0
```

### 本地编译（打补丁用这个）
```bash
# 本地编译并安装
sudo ubuntu-mainline-kernel.sh -b 6.8.0
```

## 本地编译打补丁流程

这是重点，可以在编译前打自己的补丁

### 准备工作

```bash
# 安装依赖
sudo apt install git docker.io

# 把自己加到 docker 组（避免每次 sudo）
sudo usermod -aG docker $USER
# 需要重新登录生效

# 预留空间：源码约 3GB，编译过程可能 10GB+
df -h /var/lib/docker
```

### 获取内核源码

脚本使用 Docker 编译，基于 TuxInvader 的 focal-mainline-builder 镜像

```bash
# 克隆源码（脚本会自动做，这里是手动方式）
git clone --depth=1 --branch v6.8 \
  git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git \
  linux-6.8

cd linux-6.8
```

### 打补丁

把自定义补丁放到源码目录：
```bash
# 示例：打个驱动补丁
cd linux-6.8
patch -p1 < ~/my-driver.patch

# 或者直接修改源码文件
vim drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c
```

### 修改配置（可选）

```bash
# 复制当前系统内核配置
cp /boot/config-$(uname -r) .config

# 更新配置（使用默认值）
make olddefconfig

# 或者手动配置
make menuconfig
```

### 开始编译

使用脚本编译：
```bash
# -b 参数会自动拉取 Docker 镜像并编译
sudo ubuntu-mainline-kernel.sh -b 6.8.0

# 编译完成后会自动安装
```

**编译参数调整**（修改脚本或手动 Docker 编译）：
```bash
# 手动 Docker 编译方式
docker run --rm -it \
  -v $(pwd):/build \
  tuxinvader/focal-mainline-builder:latest \
  /bin/bash

# 在容器内
cd /build
make -j$(nproc) bindeb-pkg LOCALVERSION=-custom
```

### 安装编译好的内核

```bash
# 如果是手动编译，会在上层目录生成 .deb 文件
cd ..
ls -lh *.deb

# 安装
sudo dpkg -i linux-*.deb

# 更新 GRUB
sudo update-grub
```

## SecureBoot 签名（需要的话）

如果启用了 SecureBoot，需要签名内核

### 生成签名密钥

```bash
# 创建密钥目录
mkdir -p ~/sb-keys
cd ~/sb-keys

# 生成 MOK 密钥对
openssl req -new -x509 -newkey rsa:2048 \
  -keyout MOK.priv \
  -outform DER \
  -out MOK.der \
  -days 36500 \
  -subj "/CN=My Kernel Signing Key/" \
  -nodes

# 注册 MOK 密钥（重启后会提示输入密码）
sudo mokutil --import MOK.der
# 设置一个临时密码，重启时输入
```

### 签名内核

```bash
# 签名内核和模块
sudo sbsign --key MOK.priv --cert MOK.der \
  /boot/vmlinuz-6.8.0-custom

# 签名模块（如果需要）
sudo find /lib/modules/6.8.0-custom -name "*.ko" -exec \
  sbsign --key MOK.priv --cert MOK.der {} \;
```

重启选择签名后的内核启动

## 常见问题

### 编译失败

Docker 镜像可能过期，尝试：
```bash
# 拉取最新镜像
docker pull tuxinvader/focal-mainline-builder:latest

# 或者手动编译不用 Docker
sudo apt install build-essential libncurses-dev \
  bison flex libssl-dev libelf-dev
make -j$(nproc) bindeb-pkg
```

### 缺少固件

某些驱动需要额外固件：
```bash
sudo apt install linux-firmware
```

### GRUB 不显示新内核

```bash
# 更新 GRUB
sudo update-grub

# 检查是否生成
grep menuentry /boot/grub/grub.cfg
```

## 参考资料

- [ubuntu-mainline-kernel.sh GitHub](https://github.com/pimlie/ubuntu-mainline-kernel.sh)
- [Ubuntu Kernel PPA](https://kernel.ubuntu.com/~kernel-ppa/mainline/)
- [TuxInvader 的 Docker 镜像](https://github.com/TuxInvader/focal-mainline-builder)
- [内核编译官方文档](https://www.kernel.org/doc/html/latest/)

文档已完成

---

```js
NOTE: I am not responsible for any expired content.
Created at: 2025-01-12T16:16:49+08:00
Updated at: 2025-11-02T07:01:28+08:00
Origin issue: https://github.com/ferstar/blog/issues/82
```
