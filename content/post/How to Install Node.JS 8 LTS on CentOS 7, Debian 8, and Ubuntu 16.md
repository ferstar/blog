---
title: "How to Install Node.JS 8 LTS on CentOS 7, Debian 8, and Ubuntu 16"
date: 2018-02-24T15:06:46+08:00
tags: ['LINUX', 'NODEJS']
comments: true
---

## What is Node.js?

Node.js is an open source, cross-platform runtime environment for developing server-side and networking applications. Node.js applications are written in JavaScript and can be run within the Node.js runtime on OS X, Microsoft Windows, and Linux. Node.js also provides a rich library of various JavaScript modules which simplifies the development of web applications using Node.js to a great extent.

## What is NPM?

NPM, short for Node Package Manager, is two things: first and foremost, it is an online repository for the publishing of open-source Node.js projects. second, it is a command-line utility for interacting with the said repository that aids in package installation, version management, and dependency management. Plenty of Node.js libraries and applications are published on NPM, and much more are added every day.

We are assuming that you have root permission, otherwise, you may start commands with “sudo”.

![img](https://www.hugeserver.com/kb/wp-content/uploads/2017/11/Java-9-The-Advanced-Java-SE-9-Platform-its-Dynamic-Features.jpg)

## Install Node.js and NPM

If you want to install Node.js 8 and NPM 5 you have to install them via RPM/DEB packages.

### On Debian 8 and Ubuntu 16

Execute following commands one by one to install Node.JS 8 on Debian and Ubuntu:

```
apt-get update

apt-get install curl sudo

curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
```

Now you can install Node.js and NPM easily by typing:

```
apt-get install nodejs
```

You can check the version of your Node.js and NPM with:

```
nodejs -v

v8.9.0

npm -v

5.5.1
```

### On CentOS 7

Issue the following commands to install Node.JS and NPM on your CentOS:

```
curl -sL https://rpm.nodesource.com/setup_8.x | bash -

yum install nodejs
```

It’s done, check the version of Node.js and NPM:

```
nodejs -v

v8.9.0

npm -v

5.5.1
```

via <https://www.hugeserver.com/kb/install-nodejs8-centos7-debian8-ubuntu16/>