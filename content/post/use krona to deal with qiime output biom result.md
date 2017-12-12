---
title: "利用krona可视化处理QIIME结果"
date: "2017-06-30T14:29:00+08:00"
tags: ['OTHERS']
comments: 
---


>  这个需求的起因就是因为 QIIME 自带 `plot_taxa_summary.py` 脚本生成的图表太难看, 所以就着手处理了一下

本来是想在`biostar`上面找现成的轮子, 结果没找到, 只有自己做了.

附上在[biostar.org](https://www.biostars.org/p/191933/#260267)上的回答内容

> Hi, hope this answer is not too late. :)

## convert biom to tsv format

```shell
biom convert -i single_sample.biom -o single_sample.tsv --to-tsv --table-type "OTU table" --header-key taxonomy
```

## remove the first two rows with comment

```shell
# take a look at single_sample.tsv
$ head single_sample.tsv 
# Constructed from biom file
#OTU ID H2O taxonomy
346085  140.0   Bacteria; Proteobacteria; Alphaproteobacteria; Caulobacterales; Caulobacteraceae; Brevundimonas; Brevundimonas_bullata
10298   2.0 Bacteria; Proteobacteria; Gammaproteobacteria; Enterobacteriales; Enterobacteriaceae; Photorhabdus; Photorhabdus_temperata
122823  3.0 Bacteria; Proteobacteria; Betaproteobacteria; Burkholderiales; Oxalobacteraceae; Massilia; EF516371_s
130468  2.0 Bacteria; Proteobacteria; Alphaproteobacteria; Sphingomonadales; Sphingomonadaceae; Sphingopyxis; Sphingopyxis_witflariensis
139977  38.0    Bacteria; Proteobacteria; Alphaproteobacteria; Sphingomonadales; Erythrobacteraceae; Erythrobacter; Erythrobacter_flavus
121751  2.0 Bacteria; Firmicutes; Clostridia; Clostridiales; Lachnospiraceae; Catonella; JX096343_s
96934   10.0    Bacteria; Proteobacteria; Gammaproteobacteria; Pseudomonadales; Pseudomonadaceae; Pseudomonas; Pseudomonas_guguanensis
95181   4.0 Bacteria; Proteobacteria; Gammaproteobacteria; Pseudomonadales; Moraxellaceae; Acinetobacter; Acinetobacter_radioresistens

# remove the comments
$ egrep -v "^#" single_sample.tsv > sample_no_comment.tsv
```

## remove the first column

```shell
$ cut sample_no_comment.tsv -f 2- > sample.tsv
$ head -n2 sample.tsv 
140.0   Bacteria; Proteobacteria; Alphaproteobacteria; Caulobacterales; Caulobacteraceae; Brevundimonas; Brevundimonas_bullata
2.0 Bacteria; Proteobacteria; Gammaproteobacteria; Enterobacteriales; Enterobacteriaceae; Photorhabdus; Photorhabdus_temperata
```

## replace the "; " with "\t"

```shell
$ sed -i 's/;\s*/\t/g' sample.tsv
$ head -n2 sample.tsv 
140.0   Bacteria    Proteobacteria  Alphaproteobacteria Caulobacterales Caulobacteraceae    Brevundimonas   Brevundimonas_bullata
2.0 Bacteria    Proteobacteria  Gammaproteobacteria Enterobacteriales      Enterobacteriaceae   Photorhabdus    Photorhabdus_temperata
```

## now we can make a pie chart with ktImportText(One of the Krona tools)

```shell
$ ktImportText -n enjoy_your_life -o sample.krona.html sample.tsv
```

## open sample.krona.html with your web browser, you'll see this

![Krona_snapshot_enjoy_your_life](https://preview.ibb.co/hLhkoQ/Krona_snapshot_enjoy_your_life.png)

## all in one command(optional)

```shell
$ awk -F '\t|;' 'BEGIN{OFS="\t"} FNR > 2 {$1=""; print $0}' single_sample.tsv | cut -f 2- > sample.tsv
```