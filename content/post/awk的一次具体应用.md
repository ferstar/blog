---
date = "2016-07-13T17:31:00+08:00"
title = "awk的一次具体应用"
tags = ['OTHERS']
---

## 源文件
### 1. classification.txt
```
#Sequence_Id	Database_OTU	FLAG	MAPQ	Classification
OLK8A:00020:00034	536000	0	1	Bacteria; Actinobacteria; Actinobacteria; Actinomycetales; Actinomycetaceae; Candidatus Ancillula; Unclassified; otu_536000
OLK8A:00025:00021	196980	0	1	Bacteria; Firmicutes; Clostridia; Clostridiales; Unclassified; otu_196980
OLK8A:00015:00043	940035	16	1	Bacteria; Proteobacteria; Gammaproteobacteria; Oceanospirillales; Alcanivoracaceae; Alcanivorax; Unclassified; otu_940035
OLK8A:00008:00025	223895	16	1	Bacteria; Firmicutes; Clostridia; Clostridiales; Lachnospiraceae; Coprococcus; Unclassified; otu_223895
OLK8A:00019:00023	9665	16	1	Bacteria; Proteobacteria; Gammaproteobacteria; Enterobacteriales; Enterobacteriaceae; Unclassified; otu_9665
OLK8A:00025:00016	1109247	16	1	Bacteria; Proteobacteria; Gammaproteobacteria; Enterobacteriales; Enterobacteriaceae; Unclassified; otu_1109247
OLK8A:00048:00028	289261	16	1	Bacteria; Proteobacteria; Gammaproteobacteria; Enterobacteriales; Enterobacteriaceae; Unclassified; otu_289261
...
```
### 2. LJ.fasta
```
>OLK8A:00004:00009
ACTGAGACACGGTCCAGACTCCTACGGGAGGCAGCAGTGGGGGAATATTGGACAATGGGGGAACCCTGATCCAGCCATGCCGCGTGTGTGAAGAAGGCCTTTTGGTTGTAAAGCACTTTAAGCGAGGAGGAGGCTACCGAGATTAATACTCTTGGATAGTGGACGTTACTCGCAGAATAAGCACCGGCTAACTCTGTGCCAGCAGCCGCGGTAATAC
>OLK8A:00004:00023
GGCGGACGGGTGAGTAATGTCTGGGAAACTGCCTGATGGAGGGGGATAACTACTGGAAACGGTAGCTAATACCGCATAACGTCGCAAGACCAAAGAGGGGGACCTTCGGGCCTCTTGCCATCGGATGTGCCCAGATGGGATTAGCTAGTAGGTGGGGTAACGGCTCACCTAGGCGACGTCCCTAGCTGGTCTGAGAGGATGACCAGCCACACTGGAACTGAGACACGGTCCAGACTCCTACGGGAGGCAGC
>OLK8A:00004:00026
CGATTACTAGCGACTCCGACTTCATGGAGTCGAGTTGCAGACTCCAATCCGGACTACGATAGATTTTCTGGGATTGGCTCCCGCTCACGCGTTGGCTTCCCTCTGTATCTACCATTGTAGCACCGTGTGTAGCCCTGGTCATAAAGGCCATCGATGACTTGACGTCATCCCCACCTTCCTCCGGTTTGTCACCGGCGGTCTCCTTA
...
```
## 要求
classification.txt数据是对LJ.fasta样本数据的分析结果, 其中Classification列表示所标记序列对应的菌种, 但是有可能并没有识别到种, 只识别到属或者更粗放的结果. 所以问题来了: 把样本数据中只定到属未定到具体种的序列提取出来

## 解决方案
### 1. 先取出只分出属未分出种的序列编号
`awk -F ";" '{print $1 $6}' classification.txt | grep "Unclassified" | awk '{print $1}' > genus.txt`
### 2. 然后逐一遍历`genus.txt`找出具体`Sequence_Id`及其碱基序列
```
for i in $(cat genus.txt)
do
    line=$(grep -n $i LJ.fasta | awk -F: '{print $1}')
    awk 'NR=='"$line"'' LJ.fasta >> /tmp/out.fasta
    awk 'NR=='"$(($line + 1))"'' LJ.fasta >> /tmp/out.fasta
done
```
### 3. 验证后写成脚本执行然后等待结果即可

## 并行加速
上述脚本虽然可以解决问题, 但是运行效率实在太低, 大概每秒能处理不到100行的样子, 实际数据有近百万行, 等搞完黄花菜都凉了, 所以需要改进一下, 最好能让多核跑起来, 也就是传说中的并行化处理, 所以shell看来是不行了, 不熟, 然后愉快的开始python大法
```
#!/usr/bin/env python
import subprocess
from multiprocessing import Pool

def get_unclassified_rows(item):
    handle = subprocess.Popen("grep -n %s YL.fasta | awk -F: '{print $1}'" % item, stdout=subprocess.PIPE, shell=True)
    line = int(handle.stdout.read().strip())
    handle = subprocess.Popen("awk 'NR>={0}&&NR<={1}' YL.fasta".format(line, line + 1), stdout=subprocess.PIPE, shell=True)
    with open("YL_unclassified.fasta", "a") as fh:
        fh.write(handle.stdout.read())

def main():  
    with open("genus.txt", "r") as fh:
        lst = [i.strip() for i in fh]
    pool = Pool()
    pool.map(get_unclassified_rows, lst)
    pool.close()
    pool.join()

if __name__ == "__main__":
    main()
```
主要就是用到了`pool.map()`这个东西, 效果很赞, 本来需要3小时甚至更久的的任务缩短到几分钟就欧了

```
# 找出指定内容的具体列数
sed 's/\t/:/g' XJ-C-16.NT.snap.matched.fl.Bacteria.annotated.noRibo.annotated.species.counttable | awk -F: '
NR==1{for(i=1;i<=NF;++i); if($i=="bar#AGGCAGAA+ATAGAGAG"); num=i-1}
{print $num}'
```