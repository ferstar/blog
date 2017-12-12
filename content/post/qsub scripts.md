---
title: "qsub scripts"
date: "2016-07-15T09:30:00+08:00"
tags: ['OTHERS']
comments: 
---


via <https://github.com/kundajelab/training_camp/wiki/1.2:-Shell-scripts-and-job-submission>
一个例子`sample_script.job`
```
#!/bin/bash
# pass all environment variables to the job (environment variables are like settings specific to your login session; you often want to pass these settings to the job so that the commands will behave the same way they do when you type them into your login session).
#$ -V
# name of your job
#$ -N jobname
# send an email when the job ends or aborts
#$ -m ea
# whom to email
#$ -M youremail@stanford.edu
# Execute the job in the current working directory (you also usually want this option set)
#$ -cwd
# specifies the file to write the output that would (in the absence of qsub) would be printed to the screen (technically "stdout" or "standard output")
#$ -o /path/to/jobname.stdout
# specifies the file to write error messages to (in the absence of qsub, these would also be printed to the screen; technically "stderr" or "standard error")
#$ -e /path/to/jobname.stderr
# verify options and abort if there is an error
#$ -w e
#$ -S /bin/bash

[your job commands go here]
```