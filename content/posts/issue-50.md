---
title: "Remove old kernel"
slug: "ubuntu-remove-old-kernels"
date: "2021-11-20T03:17:30+08:00"
tags: ['Linux', 'Snippet']
comments: true
---

```python
#!/usr/bin/env python3

import subprocess
import logging
import re
import sys
from collections import defaultdict

kernel_version_p = re.compile(r"[\d\-\.]{8,}")


def run_command(command, ignore_exception=False, timeout=60 * 60 * 24, no_out=False):
    logging.debug('exec command :"%s"', command)
    if no_out:
        return subprocess.Popen(command, shell=True)
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    try:
        outs, errs = [o.decode() for o in proc.communicate(timeout=timeout)]
    except subprocess.SubprocessError as exp:
        outs, errs = "", str(exp)
        if ignore_exception:
            logging.warning(errs)
        else:
            raise exp
    finally:
        proc.kill()
    return outs, errs


def parse(kernels):
    generic_kernels = defaultdict(set)
    oem_kernels = defaultdict(set)
    for k in kernels:
        match = kernel_version_p.search(k)
        if not match:
            logging.warning(f"wrong: {k}")
            continue
        num_k = int(match[0].replace("-", ".").replace(".", ""))
        if "edge" in k:
            oem_kernels[num_k].add(k)
        else:
            generic_kernels[num_k].add(k)

    for k in kernels:
        match = kernel_version_p.search(k)
        if not match:
            logging.warning(f"wrong: {k}")
            continue
        num_k = int(match[0].replace("-", ".").replace(".", ""))
        for d in [generic_kernels, oem_kernels]:
            if num_k in d:
                d[num_k].add(k)
    return generic_kernels, oem_kernels


if __name__ == "__main__":
    cli = "dpkg --get-selections | egrep -i 'linux-[himo]' | awk '{print $1}' | grep -v $(egrep -i '^DISTRIB_RELEASE=' /etc/lsb-release | awk -F '=' '{print $NF}')"
    outs, errors = run_command(cli)
    print(outs)
    if errors:
        sys.exit(errors)
    kernels = [
        i for i in outs.split("\n") if i and not re.search(r"[a-z]+\-generic$", i)
    ]
    for d in parse(kernels):
        for _, k in sorted(d.items(), key=lambda x: x[0], reverse=True):
            cmd = f"apt purge {' '.join(k)} -y"
            op = input(cmd).strip()
            if op.lower() == 'y':
                run_command(cmd)
```



```
# NOTE: I am not responsible for any expired content.
create@2021-11-20T03:17:30+08:00
update@2021-11-20T03:19:06+08:00
comment@https://github.com/ferstar/blog/issues/50
```
