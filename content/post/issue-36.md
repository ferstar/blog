---
title: "Lenovo XiaoXinPro13 2109 hackintosh"
date: "2021-02-14T14:47:15+08:00"
tags: ['macOS']
comments: true
---

## 电脑配置
|规格 | 详细信息|
|:-: | :-:|
|电脑型号| 联想小新pro13 2019笔记本电脑 |
|操作系统| 11.2 (20D64)|
|处理器| 英特尔 酷睿 i7-10710U |
|内存| 16GB板载无法更换 |
|硬盘| ~~原装三星981A 512GB~~ 更换为 三星PM961 1TB |
|显卡| Intel HD Graphics CFL CRB（UHD620）|
|显示器| 13.3 英寸 IPS 2560x1600 华星光电 |
|声卡| Realtek ALC257 |
|网卡| ~~原装Intel AX201NGW~~ 更换为 BCM94360CS2(需加转接卡) |
|SMBIOS| MacBookPro16,2 |

## 使用说明【请仔细阅读】

### 注意

- 强烈建议不要使用`OpenCore Configurator`来修改`config.plist` `OpenCore Configurator`更新缓慢与`OpenCore`版本不匹配，推荐使用`ProperTree`   
  - Win下修改`config.plist`请下载群文件`ProperTree中文版-WIN`来修改`config.plist`
- 小新由于安装过程中触摸板可能无法驱动，使用U盘安装macOS会占用仅仅一个USB接口,建议安装之前先买个usb拓展,用于插入鼠标,来进行安装步骤选项设定。
- 安装或更新系统完成后请使用`终端`输入`sudo kextcache -i /`清理缓存并重启，触控板才能正常使用

### BISO设置 【重要】

- 需要更新`BIOS`【重要】
  - [`BIOS`下载](https://pan.baidu.com/s/1bNwPFp6RHZvGNAaPx_IcJA) 密码: dpoe

- 解锁 `DVMT` 、 `CFG` 【或参考@Donald 《修改DVMT Pre-Allocated数值方法》】
  - `DVMT` =`64M`;位置:`Advanced` ->` System Agent` -> `Graphics Configura` -> `DVMT Pre- Allocated` 【重要】
  - `CFG` =`disable`;位置:`Advanced` -> `Power Performanc` -> `CPU Power Manage` -> `CPU Lock Configura`【重要】
  
- `Security `【重要】
  - `Intel Platform Trust Technology `= `Disable`
  - `Intel SGX Control` = `Disable` 【建议】
  - `Secure Boot` =`Disable`

### SMBIOS

- 默认 `MacBookPro16,2`
  - 使用其它机型`SMBIOS`时请修改`USBPorts.kext`-`Contents`-`Info.plist`
![image](https://user-images.githubusercontent.com/2854276/107879595-bc0e1280-6f14-11eb-8a16-f21c7896b2df.png)

### 关闭触摸板快捷键

- 组合键: FN+F6

### 唤醒方法

- 电源键

### 不正常工作

- ~~睡眠~~ (小新PRO13不能真正睡眠，可以仿真睡眠。唤醒比较困难，`OC` 下唤醒方法是：`电源键`唤醒)
- 声卡MIC(`暂时解决方法`：启动台-声音-输入：手动切换到“`外接可用麦克风设备`”)
<details>
<summary>关于 小新PRO13(2019/2020/13S Intel版本) 没有S3睡眠延展</summary>
<p>D0 就是正常工作状态，S0 是 D0 的电源管理，S0睡眠应该是不存在的，说 S0 睡眠，本质就是 D0 状态下进入了空闲，所以有了空闲状态下的电源管理，这个机器没有 S3睡眠，没有设计相关硬件</p>
<p>但因 ACPI 有了 S3才导致苹果试图进入睡眠，但因缺少必须的硬件最终失败，对于 Windows 不妨碍</p>更详细的说明移步<a href="https://github.com/daliansky/OC-little/tree/master/01-%E5%85%B3%E4%BA%8EAOAC" target="_blank">OC-little</a>
<p>实测选择省电的SSD可有效延长待机时间。如：三星PM961+BCM94360CS2并使用SleepWithoutBluetoothAndWifi盒盖一小时耗电仅需0.86%，而西数SN750+BCM94360CS2并使用SleepWithoutBluetoothAndWif则需要3%每小时</p>   
</details>

### 哪些可以工作更好
- 开启 [HIDPI](https://github.com/xzhih/one-key-hidpi) 来提升系统UI质量, `可能会出现花屏现象`

| AAPL,ig-platform-id | device-id | 备注                   |
| ------------------- | --------- | ---------------------- |
| 0500A53E            | A53E0000  | 解决i7-10710u花屏/闪屏 |
| 0400A53E            | A53E0004  | 解决i7-10710u花屏/闪屏 |
| 0500A63E            | A63E0000  | 通用                   |

### 镜像下载
  
- [[**黑果小兵的部落阁**] :【黑果小兵】原版镜像](https://blog.daliansky.net/categories/下载/镜像/)
        
### 感谢
- 本EFI所使用的`ACPI`均来自 @宪武 大佬
- daliansky黑果小兵
- 感谢PS@Donald提供的解锁`DVMT` `CFG lock`工具
- 感谢群友QQ876310253提供的`解锁dvmt及cfglock.docx`教程    
- 感谢群友Dreamn提供的[`SleepWithoutBluetoothAndWifi`](https://github.com/dreamncn/SleepWithoutBluetoothAndWifi)工具        

    ......
        
## 本人自用EFI
[点击下载->>EFI.zip<<-](https://github.com/ferstar/blog/files/5977914/EFI.zip)

1. 机型`MacBookPro16,2`
2. 添加`CPUFriend`以改善变频效果`实测10710U单核可跑到4.7GHz` - [附GeekBench5跑分](https://browser.geekbench.com/v5/cpu/6501218)
3. `Scan Policy配置为524547`仅扫描并引导macOS
4. `Show Picker=False`, 跳过OC引导菜单直接进入系统
5. 三码为空, 需要自行修改适配

> 意外发现还保留了当年卡特琳娜的跑分记录, 当时用的型号是`MacBookAir9,1`, 看起来单核能跑4.7GHz对于跑分而言, 意义不大

> https://browser.geekbench.com/v5/cpu/compare/2194367?baseline=6535363

![image](https://user-images.githubusercontent.com/2854276/108083812-708f6c00-70ae-11eb-8d1c-b316e2658909.png)

养老了养老了, 受不了 bugsur, 果断退回Catalina, 本子宛如新生, 香~

PS: 时光机恢复了两遍才恢复成功, 先是用 bigsur 的 recovery 恢复, 结果卡苹果, 万幸重启以后变成 Catalina 的 recovery 了, 忐忑之中又恢复了一把, 搞定

```
# NOTE: I am not responsible for any expired content.
create@2021-02-14T14:47:15+08:00
update@2021-03-15T07:49:36+08:00
comment@https://github.com/ferstar/blog/issues/36
```
