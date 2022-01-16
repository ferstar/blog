---
title: "Build a simple Python GUI and an associated installer with fbs and github actions"
date: "2022-01-16T07:19:22+08:00"
tags: ['Python']
comments: true
---

> Over the past few years I've written a few little tools in Python to improve productivity, and when I shared them with colleagues, it was a pain to package them until I met [fbs](https://build-system.fman.io/)

In this post I will show you [a demo](https://github.com/ferstar/fbs_demo) which can do build things automatically with the github actions service.

### Setup a fbs env

```shell
mkdir fbs_demo
cd fbs_demo
python3 -m venv fbs
source fbs/bin/activate
pip3 install pip -U
pip3 install fbs
pip3 install PyQt5==5.9.2
```

### Start a project

```shell
fbs startproject
```

### Run it

```shell
fbs run
```

### Build it

See my [workflow file](https://github.com/ferstar/fbs_demo/blob/main/.github/workflows/build.yml) for different platforms(Ubuntu, macOS and Windows)

Thanks to the github actions, the only thing you need to care is about the code, not the build environment.



```
# NOTE: I am not responsible for any expired content.
create@2022-01-16T07:19:22+08:00
update@2022-01-16T07:19:22+08:00
comment@https://github.com/ferstar/blog/issues/52
```
