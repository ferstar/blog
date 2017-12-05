+++
date = "2016-07-14T19:47:00+08:00"
title = "批量转换bam到fastq"
tags = ['OTHERS']

+++

额, 果然不能闭门造车啊, 摊上事先找轮子, 实在找不到再造也不迟
现成的轮子在此
<http://rpm.pbone.net/index.php3/stat/4/idpl/23502611/dir/centos_6/com/tophat-2.0.6-6.1.i686.rpm.html>
中间有个软件叫`bam2fastx`

`bam2fastq.py`作用就是批量转换指定目录下面所有bam格式到fastq格式, 如果有的话
需要系统提前预置`samtools`软件
via <http://www.htslib.org/>
```
#!/usr/bin/env python  

import getopt
import os
import subprocess
import sys
from multiprocessing.dummy import Pool as ThreadPool


def usage(argv):
    print("Usage: %s -i <bam_dir>" % argv)
    print("*.fastq files will in ./fastq.")


def bam_lst(bam_dir):
    if os.path.exists(bam_dir):
        lst = []
        for root, dirs, files in os.walk(bam_dir):
            for file in files:
                if file.endswith(".bam"):
                    lst.append(os.path.join(root, file))
    else:
        print("The directory (%s) you just entered doesn't exist." % bam_dir)
        sys.exit(2)
    if lst:
        return lst
    else:
        print("No *.sam file found in \"%s\"" % bam_dir)
        sys.exit(2)


def bam2fastq(ifile):
    file_name = ifile.split(".")[0].split("/")[1]
    subprocess.call("samtools fastq %s > fastq/%s.fastq" % (ifile, file_name), shell=True)
    return None


def main(argv):
    input_dir = ""
    try:
        opts, args = getopt.getopt(argv[1:], "hi:", ["ifile=", ])
    except getopt.GetoptError:
        usage(argv[0])
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--ifile"):
            input_dir = arg
        elif opt == "-h":
            usage(argv[0])
            sys.exit()
    files = bam_lst(input_dir)
    if not os.path.exists("fastq"):
        os.makedirs("fastq")
    print("Start converting...")
    pool = ThreadPool()
    pool.map(bam2fastq, files)
    pool.close()
    pool.join()
    print("All done!")


if __name__ == "__main__":
    main(sys.argv)
```