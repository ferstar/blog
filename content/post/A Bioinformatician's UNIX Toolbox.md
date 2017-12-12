---
date = "2016-09-05T10:28:00+08:00"
title = "一个生物信息工作者的UNIX工具箱"
tags = ['OTHERS']

---

译自 <http://lh3lh3.users.sourceforge.net/biounix.shtml>

很多生物信息(以下简称: 生信)工作者知道如何使用 Perl 或者 Python 分析数据. 然而, 有些人并没有意识到编程有时并不是必要的. 有些情形下, 使用 UNIX 自带的命令会更加便利, 可以节省大量不必要的无聊等待时间.
这里列出我在数据分析过程中经常会使用到的一些 UNIX 命令, 结合实例介绍他们最有用的一些功能, 而不是全功能科普.

## Xargs

Xargs 是我最常用到的 UNIX 命令, 悲剧的是很多 UNIX 使用者忽视了这家伙的强大.

1. 删除目录下所有以`txt`为后缀的文件
    `find . -name "*.txt" | xargs rm`
2. 打包目录下所有`pl`后缀文件
    `find . -name "*.pl" | xargs tar -zcf pl.tar.gz`
3. 杀死所有`something`匹配到的进程
    ```ps -u `whoami` | awk '/something/{print $1}' | xargs kill```
4. 将所有`txt`重命名为`bak`
    `find . -name "*.txt" | sed "s/\.txt$//" | xargs -i echo mv {}.txt {}.bak | sh`
5. 重复运行某程序`N`次(以 bootstraing 为例)
    `perl -e 'print "$_\n"for(1..100)' | xargs -i bsub echo bsub -o {}.out -e {}.err some_cmd | sh`
6. 按行提交一个脚本中的所有命令(每行一个命令)
    `cat my_cmds.sh | xargs -i echo bsub {} | sh`

> 后三个例子只工作在 GNU 版的 xargs, BSD xargs 不支持`-i`参数

## Find

在一个目录中查找满足指定条件的所有文件. 你可以写出更复杂的命令, 不过我觉得以下的例子会更有用(常用): 

1. 找到所有以`txt`为后缀的文件(包括子目录)
    `find . -name "*.txt"`
2. 查找所有目录
    `find . -type d`

## Awk

Awk 是一个专门用来快速处理空格相隔数据的编程语言. 尽管它的所有功能你都可以用 Perl 实现, 但在很多实际应用场合 awk 会更简单. 你可以找到很多关于 awk 的在线指南. 这里我只列出一些我自己常用的例子.

1. 筛选出所有第三列大于第五列的行
    `awk '$3 > $5' input.txt > output.txt`

2. 筛选出2, 4, 5列内容
 ```awk '{print $2,$4,$5}' input.txt > output.txt
awk 'BEGIN{OFS="\t"}{print $2,$4,$5}' input.txt```

3. 显示第 20 到 80 行之间的内容
  `awk 'NR>=20&&NR<=80' input.txt > output.txt`

4. 计算第二列内容的平均值
  `awk '{x+=$2}END{print x/NR}' input.txt`

5. 正则表达
 `awk '/^test[0-9]+/' input.txt`

6. 计算第2, 3两列的和将其放置在每行的最末端或者替换掉第一列
  ```awk '{print $0,$2+$3}' input.txt
awk '{$1=$2+$3;print}' input.txt```

7. 合并两个文件为一列(写的有问题)
  `awk 'BEGIN{while((getline<"file1.txt")>0)l[$1]=$0}$1 in l{print $0"\t"l[$1]}' file2.txt > output.txt`

8. 统计第二列元素重复次数
  `awk '{l[$2]++}END{for (x in l) print x,l[x]}' input.txt`

9. 只对第二行去重, 每个重复只显示第一个出现的值
  `awk '!($2 in l){print;l[$2]=1}' input.txt`

10. 统计不同词的出现次数(原文有误, 会漏掉最后一列, 我已改正)
  `awk '{for(i=1;i!=NF+1;++i)c[$i]++}END{for (x in c) print x,c[x]}' input.txt`

11. 处理简单`csv`文件
  `awk -F, '{print $1,$2}'`

12. 字符替换(这种情形使用`sort`会更简便)
  `awk '{sub(/test/, "no", $0);print}' input.txt`

## Cut

Cut 命令用来切割指定的列, 默认的分隔符是**一个单`TAB`**

1. 切割1, 2, 3, 5, 7以及后面的列
 `cut -f 1-3,5,7- input.txt`

2. 切割得到第三列, 指定定界符为一个空格`single SPACE`
 `cut -d" " -f 3 input.txt`

> 需要注意的是, Perl 中的 split 以多个连续的空字符为定界符, 而 Cut 只接收处理一个字符为定界符

## Sort

几乎所有的脚本语言都有内置的 Sort 函数, 但是都没有像 Sort 命令一样灵活. 此外, GNU sort 命令空间利用率也是非常高效. 我曾用不到 2GB 的内存排序一个 20GB 的文件. 如此强大的 sort 你自己实现的话会很难.

1. 对以空格为定界符的文件排序, 如果第一列相同, 则比第二列, 第二列相同, 则比第三列, 以此类推
  `sort input.txt`

2. 对一个超大文件进行排序(只适用于GNU Sort)
  `sort -S 1500M -t $/HOME/tmp input.txt > sorted.txt`

3. 跳过前两列从第三列开始排序
  `sort +2 input.txt`

4. 对第二列按数字降序排列, 如果相同, 则对第三列按字符升序排列
  `sort -k2,2nr -k3,3 input.txt`

5. 以第二列的第四个字符按数字排序, 默认升序
  `sort -k2,4n input.txt`

## 其他 Tips

1. 使用括号()
  ```(echo hello; echo world; cat foo.txt) > output.txt
(cd foo; ls bar.txt)```

2. 保存标准错误输出内容到具体文件
  `some_cmd 2> output.err`

3. 重定向标准错误输出到标准输出
  ```some_cmd 2>&1 | more
some_cmd >output.outerr 2>&1```

4. 查看一个文件(定义 TAB 长度为 4, 不折行)
  `less -S -x4 text.txt`

5. 正则替换`foo(\d+)-->(\d+)bar`
  ```sed "s/foo\([0-9]*\)/\1bar/g"
perl -pe 's/foo(\d+)/$1bar/g"```

6. 统计第二列中重复字符的个数
  `cut -f2 input.txt | uniq -c`

7. 找出文件中所有"--enable"(使用`--`参数防止`grep`把`--`解析为命令参数)
  `grep -- "--enable" input.txt`