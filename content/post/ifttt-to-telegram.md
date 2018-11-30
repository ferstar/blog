---
title: "利用 IFTTT webhooks 服务给 Telegram 发送消息"
date: 2018-07-20T15:32:29+08:00
tags: ['SaaS']
comments: true
---

发现之前的[自动签到](https://blog.ferstar.org/post/use-tasker-do-some-funny-things/#%E5%8F%AA%E5%9C%A8%E5%B7%A5%E4%BD%9C%E6%97%A5%E7%AD%BE%E5%88%B0)方案还是不甚完美：签到成功与否没有消息通知。

所以就想到用 IFTTT 结合 Telegram 来搞一搞这个签到反馈，实现的效果是这样的：

![签到完成](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/jpg/2018/7/4f0fbde53b682d2ac8b039096d178a4d.jpg)

需要在 IFTTT 中开一个 applets

![ifttt_sign](https://blog-1253877569.cos.ap-chengdu.myqcloud.com/ext/jpg/2018/7/b185adb9739049077f0b23f613974a04.jpg)

脚本加点新内容：

```shell
#!/system/bin/sh
# file: auto_login
# 具体坐标及延时请视自己手机而定，不要照搬

# 查询当天是否为工作日
# 0 - 工作日，1 - 假日，2 - 节日
DAY=$(curl -s http://tool.bitefu.net/jiari/?d=$(date +%Y%m%d))

# webhook url
IFTTT="https://maker.ifttt.com/trigger/sign_in_office/with/key/{your-key}"

send_msg(){
curl -X POST -H "Content-Type: application/json" -d '{"value1": "'$1'"}' $IFTTT
}

if [ ${DAY}x == 'x' ]; then
  send_msg "网络故障或节假日API不可用"
elif [ ${DAY}x == '0x' ]; then
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
  send_msg "签到完成"
else
  send_msg "节假日不用签到"
fi

exit 0
```

搞定！
