---
date = "2017-05-27T09:06:00+08:00"
title = "使用conda安装qiime"
tags = ['OTHERS']

---

跟着官网安装说明做即可,注意装好conda后最好更换一下conda和pip源，不然网速会让你抓狂的
via <http://qiime.org/install/install.html>
```bash
System information
==================
         Platform:	linux2
   Python version:	2.7.13 |Continuum Analytics, Inc.| (default, Dec 20 2016, 23:09:15)  [GCC 4.4.7 20120313 (Red Hat 4.4.7-1)]
Python executable:	/home/ferstar/anaconda3/envs/qiime/bin/python

QIIME default reference information
===================================
For details on what files are used as QIIME's default references, see here:
 https://github.com/biocore/qiime-default-reference/releases/tag/0.1.3

Dependency versions
===================
          QIIME library version:	1.9.1
           QIIME script version:	1.9.1
qiime-default-reference version:	0.1.3
                  NumPy version:	1.10.4
                  SciPy version:	0.17.1
                 pandas version:	0.18.1
             matplotlib version:	1.4.3
            biom-format version:	2.1.5
                   h5py version:	Not installed.  # 这个不能装
                   qcli version:	0.1.1
                   pyqi version:	0.3.2
             scikit-bio version:	0.2.3
                 PyNAST version:	1.2.2
                Emperor version:	0.9.51
                burrito version:	0.9.1
       burrito-fillings version:	0.1.1
              sortmerna version:	SortMeRNA version 2.0, 29/11/2014
              sumaclust version:	SUMACLUST Version 1.0.00
                  swarm version:	Swarm 1.2.19 [Apr 12 2017 17:30:22]
                          gdata:	Installed.

QIIME config values
===================
For definitions of these settings and to learn how to configure QIIME, see here:
 http://qiime.org/install/qiime_config.html
 http://qiime.org/tutorials/parallel_qiime.html

                     blastmat_dir:	None
      pick_otus_reference_seqs_fp:	/home/ferstar/anaconda3/envs/qiime/lib/python2.7/site-packages/qiime_default_reference/gg_13_8_otus/rep_set/97_otus.fasta
                         sc_queue:	all.q
      topiaryexplorer_project_dir:	None
     pynast_template_alignment_fp:	/home/ferstar/anaconda3/envs/qiime/lib/python2.7/site-packages/qiime_default_reference/gg_13_8_otus/rep_set_aligned/85_otus.pynast.fasta
                  cluster_jobs_fp:	start_parallel_jobs.py
pynast_template_alignment_blastdb:	None
assign_taxonomy_reference_seqs_fp:	/home/ferstar/anaconda3/envs/qiime/lib/python2.7/site-packages/qiime_default_reference/gg_13_8_otus/rep_set/97_otus.fasta
                     torque_queue:	friendlyq
                    jobs_to_start:	1
                       slurm_time:	None
            denoiser_min_per_core:	50
assign_taxonomy_id_to_taxonomy_fp:	/home/ferstar/anaconda3/envs/qiime/lib/python2.7/site-packages/qiime_default_reference/gg_13_8_otus/taxonomy/97_otu_taxonomy.txt
                         temp_dir:	/tmp/
                     slurm_memory:	None
                      slurm_queue:	None
                      blastall_fp:	blastall
                 seconds_to_sleep:	1

QIIME base install test results
===============================
----------------------------------------------------------------------
Ran 9 tests in 0.022s

OK
```
## 关于ssh终端如何使用matplotlib画图的问题
via <http://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined>
方法有很多, 由于我是管理员, 所以选择一个全局的方案, 如下:
```
>>> import matplotlib
>>> matplotlib.matplotlib_fname()
u'/prodata/miniconda2/envs/qiime/lib/python2.7/site-packages/matplotlib/mpl-data/matplotlibrc'
```
打开这个文件, 把backend改成agg即可, 首字母a不区分大小写

## 更换清华大学conda源
```bash
$ vi ~/.condarc
channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
  - bioconda
  - r
  - defaults
  - conda-forge
show_channel_urls: true
```
## 更换阿里pip源
```bash
$ mkdir ~/.pip
$ vi ~/.pip/pip.conf
[global]
trusted-host =  mirrors.aliyun.com
index-url = http://mirrors.aliyun.com/pypi/simple
```
