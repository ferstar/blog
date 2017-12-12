---
date = "2017-06-09T14:25:00+08:00"
title = "Downloading Data On Demand By Using SRA-tool from NCBI DataBase"
tags = ['BIO', 'LINUX']

---

vi <https://github.com/ncbi/sra-tools/wiki/Download-On-Demand>

The majority of **sra-tools** have the ability to locate and download data from the NCBI SRA on-demand, removing the need for a separate download step, and most importantly downloading only the data that are required. This feature can reduce the bandwidth, storage, and time taken to perform tasks that use less than 100% of the data contained in a run.

**sra-tools** utilize [**VDB** name resolution](https://github.com/ncbi/ncbi-vdb/wiki/Name-Resolution-Process), enabling them to accept simple accessions as parameters instead of filesystem paths. The **VDB** name resolver will generate _URLs_ into the NCBI SRA for any object not found locally, allowing the object to be opened and retrieved over _https_.

------

#### Example 1 - Download Then Convert

```
$ prefetch SRR000001

2016-12-01T15:51:52 prefetch.2.8.0: 1) Downloading 'SRR000001'...
2016-12-01T15:51:52 prefetch.2.8.0:  Downloading via http...
2016-12-01T15:52:22 prefetch.2.8.0: 1) 'SRR000001' was downloaded successfully
```

This demonstrates using `prefetch` to download a run, in this case over _https_. _[NB - the tool still states that it is using **http** even though it may be using **https**. This is a cosmetic defect and will be fixed in the next release.]_ For higher throughput, **Aspera** downloads can be used if installed on your system.

The actual file has been downloaded to a cache area in your filesystem:  

```
$ srapath SRR000001
/home/you/ncbi/public/sra/SRR000001.sra
```

The run file is compressed, occupying about 311M on disk:  

```
$ ls -l /home/you/ncbi/public/sra/SRR000001.sra
-rw-rw-r-- 1 you you 325788509 2014-11-19 16:45 /home/you/ncbi/public/sra/SRR000001.sra
```

Now convert to fastq _(NOTE - runs downloaded with prefetch are now located by accession)_:  

```
$ sff-dump SRR000001
Read 470985 spots for SRR000001
Written 470985 spots for SRR000001
```

This run contains 454 data with signals. Here it is in SFF format (about 746M):  

```
$ ls -l SRR000001.sff
-rw-rw-r-- 1 you you 782054672 2014-11-19 16:59 SRR000001.sff
```

In this example, the run was first downloaded using `prefetch` and stored in the user's public cache. Next, the run was converted into SFF, passing only the simple accession as an argument, but all data were read from cache.

------

#### Example 2 - Directly Convert

```
$ cache-mgr --report
-----------------------------------
0 cached file(s)
1 complete file(s)
325,788,509 bytes in cached files
325,788,509 bytes used in cached files
0 lock files
```

Here, we've checked the contents of our cache. It tells us that there are no _partially_ cached files, 1 complete file _(our SRR000001.sra from example 1)_, and the corresponding bytes. The file was completely downloaded by `prefetch`.

Let's clear the cache entirely:  

```
$ cache-mgr --clear
-----------------------------------
1 files removed
0 directories removed
325,788,509 bytes removed
```

Now, we can run `fastq-dump` on the accession without prior download. To verify that the run will be found remotely, we can use `srapath` to tell us where the **complete** object is located:  

```
$ srapath SRR000001
https://sra-download.ncbi.nlm.nih.gov/srapub/SRR000001
```

We see that the path is now remote. Let's convert on-the-fly:  

```
$ fastq-dump SRR000001
Read 470985 spots for SRR000001
Written 470985 spots for SRR000001
```

Looking at the _fastq_ file, we can see it is complete:  

```
$ ls -l SRR000001.fastq
-rw-rw-r-- 1 you you 301196578 2014-11-19 17:17 SRR000001.fastq
$ wc -l SRR000001.fastq
1883940 SRR000001.fastq
$ expr 1883940 / 4
470985
```

Notice that the fastq is slightly _smaller_ than the original SRA file. This is due to the fact that this SRA file also carries 454 **signal** and **clipping** data, as well as inlined **linker** sequences that are not used by fastq. *(This is true for all data submitted as SFF.)*

Let's look again at the cache contents:  

```
-----------------------------------
1 cached file(s)
0 complete file(s)
325,788,832 bytes in cached files
121,351,760 bytes used in cached files
0 lock files
```

The report tells us that there is 1 _partially_ cached file, and no complete files. This is because `fastq-dump` only needs read **names**, read **sequences**, and **qualities**. In this case, the amount of data cached is shown as 121,351,760 bytes, instead of the full 325,788,832 contained in the original SRR.