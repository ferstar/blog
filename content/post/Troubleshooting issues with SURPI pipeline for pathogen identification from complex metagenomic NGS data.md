---
title: "Troubleshooting issues with SURPI pipeline for pathogen identification from"
date: "2016-07-01T16:56:00+08:00"
tags: ['OTHERS']
comments: true
---


from <https://www.biostars.org/p/118719/>
SURPI is a pipeline to find out the pathogens from clinical metagenomics samples. It is tested only on Ubuntu and it assumes many things about your installation. I recently installed in on CentOS. These are few key points you need to take care before running the pipeline.

> The taxonomy_lookup.pl program, at line 84 has sort --parallel=$cores, where you may need to remove --parallel=$cores option, if the sort utility on you machine does not support --parallel option

很明显, 老夫的rhel6.5自带sort是并没有支持并行的选项的, 老外删除这个参数显然是下下策, 我的办法是升升升, 然后发现还是好人多啊, 这里有个安全无痛升级系统自带软件的教程

<http://duntuk.com/how-upgrade-coreutils-latest-version-source>

嗯, 然而发现sort还是原来的sort, 好吧, 那就改一下taxonomy_lookup.pl里面的对应路径, bingo!
