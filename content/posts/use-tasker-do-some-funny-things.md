---
title: "利用 Tasker 打造最强自动签到神器"
slug: "use-tasker-do-some-funny-things"
date: 2018-07-09T13:39:42+08:00
tags: ['ANDROID']
comments: true
---

> 本文不适合小白用户操作，搞机有风险，入坑须谨慎！

Android 上的 Tasker 绝对称得上是 Android 系统的神器之一， 可以完成很复杂多样的自定义任务。这里介绍一下利用他完成某 APP 自动签到的过程。

### 思路

保证手机正常联网，通过USB调试做以下步骤：

1. 解锁屏幕进入桌面
2. 打开签到 APP
3. 模拟点击 APP 中签到按钮
4. 退出签到 APP
5. 锁屏

### 准备

1. 能够安装 Magisk 的安卓手机一部
2. 安装 Magisk 模块：ADB & Fastboot for Android NDK，Busybox for Android NDK
3. 安装 APP：终端模拟器，RE文件管理器，Tasker，Secure Settings
4. 装有 adb tools 及 Git for Windows 的 PC 一台(用来计算模拟点击坐标)
5. 打开手机 USB 调试模式，并允许通过 USB 调试模拟点击
6. **保证Tasker，Secure Settings后台常驻** -- 非常重要！！！

### 唤醒屏幕

在进行模拟点击前，必须保证手机屏幕是唤醒状态，不然点了也没用。网上很多人说的采用`adb shell input keyevent 26`这种方法只有在亮屏时有用，相当于按下一次电源键，但熄屏状态并不起作用，所以我采用另一种办法：通过Tasker调用Secure Settings唤醒屏幕。

具体做法是

1. 打开Secure Settings然后 `enable System+ Modul`
2. 打开Tasker -> 任务 -> 新建任务 -> 插件 -> Secure Settings -> 配置 -> Actions -> Wake Device
3. **手机系统设置中找到设备管理器，激活 Secure Settings**

> 测试：可以在 Tasker 中设定一个延时任务测试下，比如延时三秒后亮屏

### 滑动解锁

亮屏后默认是系统的锁屏界面，简单起见，我已经把手机解锁密码去掉，只剩下滑动锁。滑动解锁处理起来比较容易，`adb shell input swipe x1 y1 x2 y2`即可，所以我们需要定起始和终止两个坐标点，来模拟滑动，继续往下看。

### 获得屏幕点击的位置坐标

此方法比较土，但胜在只要有adb tools就能用，不需要别的东西。

#### 计算比例

通过命令`adb shell getevent -p | grep -e "0035" -e "0036"`获得`event`体系里宽和高

我的手机输出如下信息：

```shell
0035  : value 0, min 0, max 1080, fuzz 0, flat 0, resolution 0
0036  : value 0, min 0, max 2248, fuzz 0, flat 0, resolution 0
```

我们需要的就是其中的 max

```shell
0035 max 1080 宽
0036 max 2248 高
```

手机分辨率是已知的，我手机是：1080 x 2248

计算比例：

```shell
rateW = 1080(手机屏幕的宽) / 1080(event里0035的max) = 1
rateH = 1920(手机屏幕的高) / 2248(event里0036的max) = 1
```

#### 计算点击位置坐标

执行命令`adb shell getevent | grep -e "0035" -e "0036"`

输出如下信息：

```shell
/dev/input/event3: 0003 0035 00000430 width
/dev/input/event3: 0003 0036 000005b1 height
```

把0035和0036后面的位置数据从16进制转化为10进制，祭出 Windows10 自带计算器，选程序员转换之得到十进制坐标为：(1072, 1457)

这是在`event`体系里的位置，将其转化为屏幕位置

```shell
screenW = width*rateW = 1072*1 = 1072
screenH = height*rateH = 1457*1 = 1457
```

所以得到刚才点击的屏幕坐标位置是(1072, 1457)

### 自己adb调试自己

一般我们是在 PC 端利用 adb 调试安卓手机，但实际上安卓自己也可以调试自己，这样可以只用手机就完成模拟点击操作，不需要电脑的帮助。还记得准备工作要求的安装 ADB & Fastboot for Android NDK，Busybox for Android NDK 这个 Magisk 模块么？就是来干这个的。

打开终端模拟器，输入代码：

```shell
su 2000 -c 'setprop service.adb.tcp.port  5555'   # 开启USB网络调试
su -c 'stop adbd && start adbd'                   # 重启USB调试服务
adb connect localhost:5555                        # 启动adb，接通本机5555端口
```

出来弹窗选择信任即可

### 打开签到 APP

这一步你当然可以通过模拟点击来打开相应 APP 来进行后续的操作，但这要求你手机解锁开屏后不能有别的 APP 占据屏幕，否则点击就乱套。这里我采用的是`am start -n ｛包(package)名｝/｛包名｝.{活动(activity)名称}`方法，APP 包名一般都能在对应的市场比如酷安应用详情中看到，钉钉的包名是`com.alibaba.android.rimet `。那么如何知道 APP 的 activity 名称呢？继续往下看。

### 快速获取当前Activity类名

据说有个叫`re-sign.jar`的小工具可以干这个，但我这里总是报OOM的错，懒得深究，直接上 adb 敲如下命令

`adb shell dumpsys activity activities | findstr "应用包名" `，输入之后信息会有很多，过滤一下，主要找`包名.`开头的，比如钉钉是`com.alibaba.android.rimet.ui.activity.StartActivity`（版本不同可能会有差异，需要自己琢磨），找到后用如下命令启动 APP：

```shell
am start -n com.alibaba.android.rimet/com.alibaba.android.rimet.ui.activity.StartActivity
```

打开 APP 后模拟点击完签到流程，最后退出

```shell
am force-stop com.alibaba.android.rimet
```

### 熄屏

屏幕老亮着太费电，还是关了的好，有两种方法

1. `adb shell input keyevent 26` 相当于按电源键
2. Tasker 调用 Secure Settings 插件，选择 Lock Device（步骤类似[唤醒屏幕](#唤醒屏幕)）

### 只在工作日签到

Tasker 自带的定时功能并不能满足这个需求，我们需要借助第三方 API 接口来判断当天是否为工作日，是工作日才签到。类似的第三方接口很多，有开发能力的机油甚至可以自己写，这里我用的是[免费节假日API](http://tool.bitefu.net/jiari/)提供的接口。

整个自动签到脚本内容如下：

```shell
#!/system/bin/sh
# file: auto_login
# 具体坐标及延时请视自己手机而定，不要照搬

# 查询当天是否为工作日
# 0 - 工作日，1 - 假日，2 - 节日
DAY=$(curl -s http://tool.bitefu.net/jiari/?d=$(date +%Y%m%d))

# 只有工作日才签到
if [ ${DAY}x == '0x' ]; then
  # 延时一秒再模拟滑动解锁
  sleep 1
  adb shell input swipe 538 1033 555 536
  
  # 延时三秒再打开APP
  sleep 3
  am start -n com.alibaba.android.rimet/com.alibaba.android.rimet.ui.activity.StartActivity
  
  # 视手机性能及网络影响，APP完全打开需要一定时间，所以延时最好多延几秒
  sleep 10
  
  # 模拟点击签到按钮
  adb shell input tap 133 730
  sleep 5
  adb shell input tap 433 830
  sleep 5
  # 完成点击后停止APP
  am force-stop com.alibaba.android.rimet
fi

exit 0
```

### ALL IN

使用 RE 管理器将上述`auto_login`移动到`/system/xbin/`目录下，改可执行权限。剩下的操作均在 Tasker 应用中完成：

1. 新建配置文件，时间选每天上下班时间，关联任务名字随便取
2. 唤醒屏幕前最好随机睡段时间（睡多久自己把控）
3. 唤醒屏幕
4. 调用`auto_login`脚本完成签到流程
5. 锁屏

**懒人福利**：Tasker 配置文件(复制保存为xml后缀文件，可直接在应用内导入还原)：

```xml
<TaskerData sr="" dvi="1" tv="5.0u7m">
	<Profile sr="prof8" ve="2">
		<cdate>1531101968896</cdate>
		<edate>1531122746414</edate>
		<id>8</id>
		<mid0>6</mid0>
		<nme>上班</nme>
		<Time sr="con0">
			<fh>8</fh>
			<fm>16</fm>
			<th>-1</th>
			<tm>-1</tm>
		</Time>
	</Profile>
	<Task sr="task6">
		<cdate>1531100883059</cdate>
		<edate>1531122706060</edate>
		<id>6</id>
		<nme>自动流程</nme>
		<pri>100</pri>
		<Action sr="act0" ve="7">
			<code>545</code>
			<Str sr="arg0" ve="3">%SLEEP_TIME</Str>
			<Int sr="arg1" val="3"/>
			<Int sr="arg2" val="180"/>
		</Action>
		<Action sr="act1" ve="7">
			<code>123</code>
			<Str sr="arg0" ve="3">sleep %SLEEP_TIME</Str>
			<Int sr="arg1" val="0"/>
			<Int sr="arg2" val="1"/>
			<Str sr="arg3" ve="3"/>
			<Str sr="arg4" ve="3"/>
			<Str sr="arg5" ve="3"/>
			<ConditionList sr="if">
				<Condition sr="c0" ve="3">
					<lhs>%SLEEP_TIME</lhs>
					<op>12</op>
					<rhs></rhs>
				</Condition>
			</ConditionList>
		</Action>
		<Action sr="act2" ve="7">
			<code>1563799945</code>
			<Bundle sr="arg0">
				<Vals sr="val">
					<com.intangibleobject.securesettings.plugin.extra.BLURB>Screen &amp; Keyboard Lights On
1 Second</com.intangibleobject.securesettings.plugin.extra.BLURB>
					<com.intangibleobject.securesettings.plugin.extra.BLURB-type>java.lang.String</com.intangibleobject.securesettings.plugin.extra.BLURB-type>
					<com.intangibleobject.securesettings.plugin.extra.SETTING>wake_device</com.intangibleobject.securesettings.plugin.extra.SETTING>
					<com.intangibleobject.securesettings.plugin.extra.SETTING-type>java.lang.String</com.intangibleobject.securesettings.plugin.extra.SETTING-type>
					<com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_DURATION>1000</com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_DURATION>
					<com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_DURATION-type>java.lang.Long</com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_DURATION-type>
					<com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_TYPE>full</com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_TYPE>
					<com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_TYPE-type>java.lang.String</com.intangibleobject.securesettings.plugin.extra.WAKE_LOCK_TYPE-type>
					<com.twofortyfouram.locale.intent.extra.BLURB>Screen &amp; Keyboard Lights On
1 Second</com.twofortyfouram.locale.intent.extra.BLURB>
					<com.twofortyfouram.locale.intent.extra.BLURB-type>java.lang.String</com.twofortyfouram.locale.intent.extra.BLURB-type>
					<net.dinglisch.android.tasker.subbundled>true</net.dinglisch.android.tasker.subbundled>
					<net.dinglisch.android.tasker.subbundled-type>java.lang.Boolean</net.dinglisch.android.tasker.subbundled-type>
				</Vals>
			</Bundle>
			<Str sr="arg1" ve="3">com.intangibleobject.securesettings.plugin</Str>
			<Str sr="arg2" ve="3">com.intangibleobject.securesettings.plugin.Activities.TabsActivity</Str>
			<Int sr="arg3" val="0"/>
		</Action>
		<Action sr="act3" ve="7">
			<code>123</code>
			<Str sr="arg0" ve="3">auto_login</Str>
			<Int sr="arg1" val="0"/>
			<Int sr="arg2" val="1"/>
			<Str sr="arg3" ve="3"/>
			<Str sr="arg4" ve="3"/>
			<Str sr="arg5" ve="3"/>
		</Action>
		<Action sr="act4" ve="7">
			<code>1563799945</code>
			<Bundle sr="arg0">
				<Vals sr="val">
					<com.intangibleobject.securesettings.plugin.extra.BLURB>Lock Device</com.intangibleobject.securesettings.plugin.extra.BLURB>
					<com.intangibleobject.securesettings.plugin.extra.BLURB-type>java.lang.String</com.intangibleobject.securesettings.plugin.extra.BLURB-type>
					<com.intangibleobject.securesettings.plugin.extra.SETTING>force_lock</com.intangibleobject.securesettings.plugin.extra.SETTING>
					<com.intangibleobject.securesettings.plugin.extra.SETTING-type>java.lang.String</com.intangibleobject.securesettings.plugin.extra.SETTING-type>
					<com.twofortyfouram.locale.intent.extra.BLURB>Lock Device</com.twofortyfouram.locale.intent.extra.BLURB>
					<com.twofortyfouram.locale.intent.extra.BLURB-type>java.lang.String</com.twofortyfouram.locale.intent.extra.BLURB-type>
					<net.dinglisch.android.tasker.subbundled>true</net.dinglisch.android.tasker.subbundled>
					<net.dinglisch.android.tasker.subbundled-type>java.lang.Boolean</net.dinglisch.android.tasker.subbundled-type>
				</Vals>
			</Bundle>
			<Str sr="arg1" ve="3">com.intangibleobject.securesettings.plugin</Str>
			<Str sr="arg2" ve="3">com.intangibleobject.securesettings.plugin.Activities.TabsActivity</Str>
			<Int sr="arg3" val="0"/>
		</Action>
	</Task>
</TaskerData>

```

### 参考

1. [Run adb command inside the terminal emulator or programmatically without root](https://android.stackexchange.com/questions/142533/run-adb-command-inside-the-terminal-emulator-or-programmatically-without-root)
2. [使用工具re-sign.jar获取android的包名和主类名](https://blog.csdn.net/wugang8023/article/details/39941659)
3. [Android使用ADB启动应用程序](https://blog.csdn.net/u012041204/article/details/53957664)
4. [免费节假日API](http://tool.bitefu.net/jiari/)
5. [Android快速获取当前Activity类名的三种方法](https://blog.csdn.net/android_cmos/article/details/73382573)
6. [Android adb shell 获得点击屏幕的位置坐标](https://blog.csdn.net/liu_zhen_wei/article/details/12559277)
7. [Tasker FAQ](https://tasker.joaoapps.com/guides.html)
8. [Magisk - The Universal Systemless Interface, to create an altered mask of the system without changing the system itself.](https://forum.xda-developers.com/apps/magisk)
