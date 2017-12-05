+++
date = "2017-07-06T11:51:00+08:00"
title = "destroying old docker directories more safely"
tags = ['DOCKER', 'LINUX', 'CENTOS']

+++

清理docker lib目录时遇到如下的错误
```shell
rm: cannot remove `895b070402bd7d26d9595e939422c598e8cc1f4ade1b34e2a9659138ffe3c5c9/lost+found': Read-only file system
```

爬墙Google一番后找到如下解决脚本，实现原理就是批量卸载这些挂载点后再删除，要不嫌累一个个人肉卸载删除也可以~

[**nuke-graph-directory.sh**](https://github.com/moby/moby/blob/620339f166984540f15aadef2348646eee9a5b42/contrib/nuke-graph-directory.sh)

```shell
#!/bin/sh
set -e

dir="$1"

if [ -z "$dir" ]; then
	{
		echo 'This script is for destroying old /var/lib/docker directories more safely than'
		echo '  "rm -rf", which can cause data loss or other serious issues.'
		echo
		echo "usage: $0 directory"
		echo "   ie: $0 /var/lib/docker"
	} >&2
	exit 1
fi

if [ "$(id -u)" != 0 ]; then
	echo >&2 "error: $0 must be run as root"
	exit 1
fi

if [ ! -d "$dir" ]; then
	echo >&2 "error: $dir is not a directory"
	exit 1
fi

dir="$(readlink -f "$dir")"

echo
echo "Nuking $dir ..."
echo '  (if this is wrong, press Ctrl+C NOW!)'
echo

( set -x; sleep 10 )
echo

dir_in_dir() {
	inner="$1"
	outer="$2"
	[ "${inner#$outer}" != "$inner" ]
}

# let's start by unmounting any submounts in $dir
#   (like -v /home:... for example - DON'T DELETE MY HOME DIRECTORY BRU!)
for mount in $(awk '{ print $5 }' /proc/self/mountinfo); do
	mount="$(readlink -f "$mount" || true)"
	if dir_in_dir "$mount" "$dir"; then
		( set -x; umount -f "$mount" )
	fi
done

# now, let's go destroy individual btrfs subvolumes, if any exist
if command -v btrfs > /dev/null 2>&1; then
	root="$(df "$dir" | awk 'NR>1 { print $NF }')"
	root="${root#/}" # if root is "/", we want it to become ""
	for subvol in $(btrfs subvolume list -o "$root/" 2>/dev/null | awk -F' path ' '{ print $2 }' | sort -r); do
		subvolDir="$root/$subvol"
		if dir_in_dir "$subvolDir" "$dir"; then
			( set -x; btrfs subvolume delete "$subvolDir" )
		fi
	done
fi

# finally, DESTROY ALL THINGS
( set -x; rm -rf "$dir" )
```

