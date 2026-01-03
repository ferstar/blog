---
title: "Compiling Python with latest OpenSSL on earlier version macOS"
slug: "macos-compile-python-latest-openssl"
date: "2021-01-21T23:48:52+08:00"
tags: ['Python', 'macOS']
comments: true
---

I used to write some Python scripts, and some of them crashed when run on earlier version of macOS(<10.15.x).

A typical exception may like this:

```shell
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(
host='xxx.com', port=443): Max retries exceeded with url: /
(Caused by SSLError(SSLError(1, '[SSL: TLSV1_ALERT_PROTOCOL_VERSION]
tlsv1 alert protocol version (_ssl.c:720)'),))
```
This was caused by macOS using an outdated OpenSSL version.

I found [this page](https://fman.io/blog/battling-with-macos/#appendix) on Google and follow these steps to solve the problem:

```shell
brew update
brew install openssl
# brew install pyenv  # I skipped this line because I used pyenv too
PYTHON_CONFIGURE_OPTS="--enable-shared" CFLAGS="-I$(brew --prefix openssl)/include" LDFLAGS="-L$(brew --prefix openssl)/lib" pyenv install 3.6.9
```
After using this newly compiled Python interpreter, the problem disappeared

```
# NOTE: I am not responsible for any expired content.
created_date: 2021-01-21T23:48:52+08:00
update_date: 2021-02-12T21:44:52+08:00
comment_url: https://github.com/ferstar/blog/issues/34
