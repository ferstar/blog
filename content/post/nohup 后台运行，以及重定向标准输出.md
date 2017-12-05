+++
date = "2015-09-17T23:16:00+08:00"
title = "nohup 后台运行，以及重定向标准输出和标准错误输出"
tags = ['SHELL', 'LINUX']

+++

nohup 加 &大家都知道是后台运行并把stdout输出到文件nohup.out中。其实&是后台运行的命令。
具体的命令我就不介绍了，
一般都是在linux下
nohup command_line
或者
nohup command_line &
这之间的差别是带&的命令行，即使terminal关闭，或者电脑死机程序依然运行（前提是你把程序递交到服务器上）；
它把标准输出（STDOUT）和标准错误（STDERR）结果输出到nohup.txt文件
这个看似很方便，但是当输出很大的时候，nohup.txt文件会非常大，或者多个后台命令的时候大家都会输出到nohup.txt文件，不利于查找结果和调试程序。
所以能够重定向输出会非常方便。
下面要介绍标准输出，标准输入 和标准错误了。
其实我门一直都在用，只是没有注意到，
比如
`>./command.sh > output`
\#这其中的>就是标准输出符号，其实是 1>output 的缩写
`>./command.sh 2> output`
＃这里的2>就是将标准错误输出到output文件里。
而0< 则是标准输入了。
下面步入正题，重定向后台命令
`>nohup ./command.sh > output 2>&1 &`
解释：前面的nohup 和后面的&我想大家都能明白了把。
主要是中间的 2>&1的意思
这个意思是把标准错误（2）重定向到标准输出中（1），而标准输出又导入文件output里面，
所以结果是标准错误和标准输出都导入文件output里面了。
至于为什么需要将标准错误重定向到标准输出的原因，那就归结为标准错误没有缓冲区，而stdout有。
这就会导致 >output 2>output 文件output被两次打开，而stdout和stderr将会竞争覆盖，这肯定不是我门想要的.
这就是为什么有人会写成：
`nohup ./command.sh >output 2>output`出错的原因了
最后谈一下/dev/null文件的作用
这是一个无底洞，任何东西都可以定向到这里，但是却无法打开。
所以一般很大的stdou和stderr当你不关心的时候可以利用stdout和stderr定向到这里
`>./command.sh >/dev/null 2>&1`

好，就到这里，enjoy youself！！！