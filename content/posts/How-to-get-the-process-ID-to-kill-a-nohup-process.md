---
title: "How to get the process ID to kill a nohup process?"
slug: "how-to-get-the-process-id-to-kill-a-nohup-process"
date: "2015-08-31T23:19:47+08:00"
tags: ['LINUX']
comments: true
---

When using `nohup`, it will give you the `PID` at the command prompt. If your plan is to manually manage the process, you can save that `PID` and use it later to kill the process if needed, via `kill PID` or `kill -9 PID` (if you need to force kill). Alternatively, you can find the PID later on by `ps -ef output | grep "command name"` and locate the PID from there. Note that nohup does not appear in the ps output.

If you used a script, you could do something like:
```
nohup my_command > my.log 2>&1&
echo $! > save_pid.txt
```
This will run my_command saving all output into my.log (in a script, `$!` represents the PID of the last process executed). If the command sends output on a regular basis, you can check the output occasionally with tail my.log, or if you want to follow it "live" you can use `tail -f my.log`. Finally, if you need to kill the process, you can do it via:
```
kill -9 `cat save_pid.txt`
```
来源： <http://stackoverflow.com/questions/17385794/how-to-get-the-process-id-to-kill-a-nohup-process>
