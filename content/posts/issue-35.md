---
title: "Use pyenv to build a full functional Python interpreter on macOS Big Sur(11.1)"
slug: "macos-pyenv-python-build-guide"
date: "2021-01-22T04:57:41+08:00"
tags: ['Python', 'macOS']
comments: true
---

- no build errors
- `tkinter` module enabled
- openssl from homebrew
- CPython with Framework support

```shell
brew install zlib bzip2 tcl-tk openssl
py_version="3.6.11"
CFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix bzip2)/include -I$(brew --prefix readline)/include -I$(xcrun --show-sdk-path)/usr/include -I$(brew --prefix tcl-tk)/include" \
LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/lib -L$(brew --prefix tcl-tk)/lib" \
PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I/usr/local/opt/tcl-tk/include' --with-tcltk-libs='-L/usr/local/opt/tcl-tk/lib -ltcl8.6 -ltk8.6' --enable-framework" \
pyenv install --patch $py_version < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch\?full_index\=1)
```

output:

```shell
pyenv install --patch 3.6.11 < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch\?full_index\=1)
python-build: use openssl@1.1 from homebrew
python-build: use readline from homebrew
Downloading Python-3.6.11.tar.xz...
-> https://www.python.org/ftp/python/3.6.11/Python-3.6.11.tar.xz
Installing Python-3.6.11...
patching file Misc/NEWS.d/next/macOS/2020-06-24-13-51-57.bpo-41100.mcHdc5.rst
patching file configure
Hunk #1 succeeded at 3375 (offset -51 lines).
patching file configure.ac
Hunk #1 succeeded at 495 (offset -15 lines).
python-build: use readline from homebrew
python-build: use zlib from xcode sdk
Installed Python-3.6.11 to /Users/ferstar/.pyenv/versions/3.6.11
```

test `tkinter` module

`python -m tkinter -c 'tkinter._test()'`

![image](https://user-images.githubusercontent.com/2854276/105448243-e4597700-5cb0-11eb-8c6a-90105ee869cd.png)

references

1. https://stackoverflow.com/a/60469203
2. https://github.com/pyenv/pyenv/issues/1375#issuecomment-549754431
3. https://github.com/pyenv/pyenv/wiki#which-shell-startup-file-do-i-put-pyenv-config-in
4. https://github.com/pyenv/pyenv/issues/1737#issuecomment-738080459

```
# NOTE: I am not responsible for any expired content.
created_date: 2021-01-22T04:57:41+08:00
update_date: 2021-02-12T22:03:34+08:00
comment_url: https://github.com/ferstar/blog/issues/35
