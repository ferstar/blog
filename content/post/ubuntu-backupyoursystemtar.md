---
date = "2013-11-02T15:49:59+08:00"
title = "Ubuntu-BackupYourSystem/TAR"
tags = ['OTHERS']
---

# [https://help.ubuntu.com/community/BackupYourSystem/TAR](https://help.ubuntu.com/community/BackupYourSystem/TAR "source site")

# Introduction to tar

This page is part of the [BackupYourSystem](https://help.ubuntu.com/community/BackupYourSystem) article, as such, ensure you've read that prior to continuing. This subpage will acquaint a user with the tar archival program, a CLI solution to the creation of compressed archival backups. It will detail the creation and restoration of archives, including operation over a network.<!--more-->

Before continuing users are encouraged to read the [TerminalHowto](https://help.ubuntu.com/community/TerminalHowto) page which explains many basic concepts related to working with a terminal.

![IconsPage/stop.png](https://help.ubuntu.com/community/IconsPage?action=AttachFile&amp;do=get&amp;target=stop.png "IconsPage/stop.png") Improper usage of any archival program can cause unintended data loss. Read the entire tutorial before proceeding and understand what you are doing.

&nbsp;

# Preparing for Backup

In preparation for a complete backup of the system, it is a good idea to empty the trash and remove any unwanted files and programs from your current installation. This includes the home folder which can be filled with many files not needed. Doing so will reduce the size of the archive created in relation to how much space is liberated.

A quick list of examples is below, decide for yourself what applies:

*   Delete all your emails.
*   Wipe your saved browser personal details and search history.

    *   If you are not worried about the security concerns, this step is not necessary. Many users explicitly **want** backups of their email and browser settings.

*   Unmount any external drives and remove any optical media such as CDs or DVDs that you do not want to include in the backup.

    *   This will reduce the amount of exclusions you need to type later in the process.

*   Go through the contents of your user folder in <tt>/home</tt> and delete all unwanted files in the subdirectories, often people download files and forget about them for instance.
&nbsp;

# Backing Up

To get started, please open up a terminal, in Ubuntu this can be done by **Applications Menu** -&gt; **Accessories** -&gt; **Terminal**. Some directories require root or superuser permissions to read and write (needed for backup), for an explanation on why see [FilePermissions](https://help.ubuntu.com/community/FilePermissions). To gain temporary root permission, simply preface any command you want to issue with sudo, as explained in [RootSudo](https://help.ubuntu.com/community/RootSudo).

For this example, we will change directories to root. This is where the backup will be made. This is an arbitrary decision, you should create the backup elsewhere. For instance to a mounted external hard drive, another partition or disk connected internally, even a folder in your home directory could be used. In all cases, ensure the location your saving the archive to has enough space. Simply use the cd command to navigate there.
<pre>cd /</pre>
The following is an exemplary command of how to archive your system.
<pre>tar -cvpzf backup.tar.gz --exclude=/backup.tar.gz --one-file-system /</pre>
To understand what is going on, we will dissect each part of the command.

*   **tar** - is the command that creates the archive. It is modified by each letter immediately following, each is explained bellow.

    *   **c** - create a new backup archive.
    *   **v** - verbose mode, tar will print what it's doing to the screen.
    *   **p** - preserves the permissions of the files put in the archive for restoration later.
    *   **z** - compress the backup file with 'gzip' to make it smaller.
    *   **f &lt;filename&gt;** - specifies where to store the backup, _backup.tar.gz_ is the filename used in this example. It will be stored in the current working directory, the one you set when you used the cd command.

*   **--exclude=/example/path** - The options following this model instruct tar what directories **NOT** to backup. We don't want to backup everything since some directories aren't very useful to include. The first exclusion rule directs tar not to back itself up, this is important to avoid errors during the operation.
*   **--one-file-system** - Do not include files on a different filesystem. If you want other filesystems, such as a <tt>/home</tt> partition, or external media mounted in <tt>/media</tt> backed up, you either need to back them up separately, or omit this flag. If you do omit this flag, you will need to add several more **--exclude=** arguments to avoid filesystems you do not want. These would be <tt>/proc</tt>, <tt>/sys</tt>, <tt>/mnt</tt>, <tt>/media</tt>, <tt>/run</tt> and <tt>/dev</tt> directories in root. <tt>/proc</tt> and <tt>/sys</tt> are virtual filesystems that provide windows into variables of the running kernel, so you do not want to try and backup or restore them. <tt>/dev</tt> is a tmpfs whose contents are created and deleted dynamically by udev, so you also do not want to backup or restore it. Likewise, <tt>/run</tt> is a tmpfs that holds variables about the running system that do not need backed up.
*   It is important to note that these exclusions are recursive. This means that all folders located within the one excluded will be ignored as well. In the example, excluding the <tt>/media</tt> folder excludes all mounted drives and media there.

    *   If there are certain partitions you wish to backup located in <tt>/media</tt>, simply remove the exclusion and write a new one excluding the partitions you don't want backed up stored within it. For example:

            *   <pre>--exclude=/media/unwanted_partition</pre>

*   **/** - After all options is the directory to backup. Since we want to backup everything on the system we use <tt>/</tt> for the root directory. Like exclusions, this recursively includes every folder below root not listed in the exclusions or other options.
See tips before operation for additional information.

Once satisfied with the command, execute it and wait until it has completed. The duration of the operation depends on the amount of files and compression choses. Once completed, check the directory you set to find the archive. In our example, backup.tar.gz would be located in the <tt>/</tt> directory once completed. This archive can then be moved to any other directory for long term storage.

Note: At the end of the process you might get a message along the lines of 'tar: Error exit delayed from previous errors' or something, but in most cases you can just ignore that.

&nbsp;

## Additional Tips

*   To keep good records, you should include the date and a description of backup in the filename.
*   Another option would be to use bzip2 to compress your backup instead of gzip. Bzip2 provides a higher compression ratio at the expense of speed. If compression is important to you, just substitute the <tt>z</tt> in the command with <tt>j</tt>, and change the file name to _.tar.bz2_. The rest of this guides examples use gzip, make the subsequent changes to the examples before using them.
*   If you want to exclude all other mounts other than the current - by this I mean partitions mounted to directories - then use the <tt>--one-file-system</tt> option appended before the exclusion rules. This has the effect of stopping tar from crossing into any other mounts in any directory including /mnt or /media. For instance, many users create a separate mount for <tt>/home</tt> to keep user folders separate from root, adding this option to our original example would exclude home's contents entirely.
&nbsp;

## Archive Splitting

If you want to burn the archive to discs, or transfer them to a filesystem with a limited max filesize (say FAT32 with a limit of 4GB per file) then you will have to split the file either during or after archive creation. A simple means is to use the <tt>split</tt> command. Below are examples of both scenarios. More information than conveyed here can be found in the man pages of split, use <tt>man split</tt> in a terminal to read. Ensure you keep these archives all together in a directory you label for extraction at a later date. Once the archives are split to a desirable size, they can be burned one at a time to disc.

**To Split During Creation**
<pre>tar -cvpz &lt;put options here&gt; / | split -d -b 3900m - /name/of/backup.tar.gz.</pre>

*   The first half until the pipe (|) is identical to our earlier example, except for the omission of the f option. Without this, tar will output the archive to standard output, this is then piped to the split command.
*   **-d** - This option means that the archive suffix will be numerical instead of alphabetical, each split will be sequential starting with 01 and increasing with each new split file.
*   **-b** - This option designates the size to split at, in this example I've made it 3900mB to fit into a FAT32 partition.
*   **-** - The hyphen is a placeholder for the input file (normally an actual file already created) and directs split to use standard input.
*   **/name/of/backup.tar.gz.** Is the prefix that will be applied to all generated split files. It should direct to the folder you want the archives to end up. In our example, the first split archive will be in the directory /name/of/ and be named backup.tar.gz.01 .
**To Split After Creation**
<pre>split -d -b 3900m /path/to/backup.tar.gz /name/of/backup.tar.gz.</pre>

*   Here instead of using standard input, we are simply splitting an existing file designated by /path/to/backup.tar.gz .
**To Reconstitute the Archive**
Reconstructing the complete archive is easy, first <tt>cd</tt> into the directory holding the split archives. Then simply use <tt>cat</tt> to write all the archives into one and send over standard output to tar to extract to the specified directory.

&nbsp;
<pre>cat *tar.gz* | tar -xvpzf - -C /</pre>

*   The use of * as a wild card before and after tar.gz tells cat to start with first matching file and add every other that matches, a process known as catenation, how the command got its name.
*   Afterwards, it simply passes all that through standard output to tar to be extracted into root in this example.
*   For a more complete explanation of restoration, see [Restoring](https://wiki.ubuntu.com/starcraft.man/Sandbox#Restoring).
&nbsp;

## Backup Over a Network

The command tar does not include network support within itself, but when used in conjunction with other programs this can be achieved. Two common options are netcat (nc) and ssh.

&nbsp;

### Netcat

The command <tt>nc</tt> is designed to be a general purpose networking tool. It sets up a simple connection between two networked machines. This connection survives until the user manually disconnects it, unlike normal connections such as tcp which terminate upon completion of a file.

**Receiving Computer**
On the receiving end you'll setup netcat to write the backup file as in the following example. This command will setup a machine to receive standard input from network to port 1024 then write it to the file backup.tar.gz. The choice of port is entirely up to the user, as long as it is 1024 or larger. A simple example:
<pre>nc -l 1024 &gt; backup.tar.gz</pre>
**Sending Computer**
On the machine to be backed up, the tar command will be piped to nc which will then send the backup over the network to the port in question to be written in the file. Take note, where it says &lt;receiving host&gt; replace with the name of the computer on the network. The f option was omitted since we are not writing to a local file, but moving the archive through standard output. The following is an example:
<pre>tar -cvpz &lt;all those other options like above&gt; / | nc -q 0 &lt;receiving host&gt; 1024</pre>
If all goes well the backup will be piped through the network without touching the file system being read.

&nbsp;

### SSH

You can also use SSH. For a complete explanation of its proper use see [SSH](https://help.ubuntu.com/community/SSH). The command below is an example of what is possible.
<pre>tar -cvpz &lt;all those other options like above&gt; / | ssh &lt;backuphost&gt; "( cat &gt; ssh_backup.tar.gz )"</pre>
In the example:

*   The tar half of the command is the same as above, with the omission of the f option to pipe the archive via standard output to ssh and onto the networked computer.
*   **ssh_backup.tar.gz** Is the name of the file that will be created on the machine indicated.
*   **&lt;backuphost&gt;** - Should be replaced with the name of the computer in question on the network.
&nbsp;

# Restoring

You will want to restore from a Live CD. If needed, first partition and format the drive. You can do this with <tt>gparted</tt>. Then simply mount the partition you are going to restore somewhere. If you open the drive in nautilus, it will be auto mounted somewhere under <tt>/media</tt>. Take a look to find out where with:
<pre>ls /media</pre>
**Restore Your Backup**
<pre>sudo tar -xvpzf /path/to/backup.tar.gz -C /media/whatever --numeric-owner</pre>
A brief explanation:

*   **x** - Tells tar to extract the file designated by the f option immediately after. In this case, the archive is <tt>/home/test/backup.tar.gz</tt>
*   **-C &lt;directory&gt;** - This option tells tar to change to a specific directory before extracting. In this example, we are restoring to the root (/) directory.
*   **--numeric-owner** - This option tells tar to restore the numeric owners of the files in the archive, rather than matching to any user names in the environment you are restoring from. This is due to that the user id:s in the system you want to restore don't necessarily match the system you use to restore (eg a live CD).
![IconsPage/warning.png](https://help.ubuntu.com/community/IconsPage?action=AttachFile&amp;do=get&amp;target=warning.png "IconsPage/warning.png") **This will overwrite every single file and directory on the designated mount with the one in the archive.** Any file created after the archive, will have no equivalent stored in the archive and thus will remain untouched

Allow the restoration the time it needs to complete. Once extraction is completed, you may need to recreate directories that were not included in the original archive because you excluded them with <tt>--exclude</tt>. This does not apply to filesystems excluded with <tt>--one-file-system</tt>. This can be done with the following command:
<pre>mkdir /proc /sys /mnt /media</pre>
Once finished, reboot and everything should be restored to the state of your system when you made the backup.

&nbsp;

## Restoring GRUB

For the system to boot, you will need to restore grub. To do this, you will need to reconfigure it in a chroot:
<pre>sudo -s
for f in dev dev/pts proc ; do mount --bind /$f /media/whatever/$f ; done
chroot /media/whatever
dpkg-reconfigure grub-pc</pre>
You will get a menu asking you what drive(s) grub should be installed on. Choose whatever drive(s) the computer will be booting from.

For more information on repairing grub, see [GrubHowto](https://help.ubuntu.com/community/GrubHowto#Backup,%20Repairing%20and%20Reinstalling%20GRUB)

&nbsp;

## Restoring Over a Network

This short guide, assumes you employed nc to make the original backup as described above.

**Receiving Computer**
Ensure the disk has been mounted and use the following command to accept input over the network that will then be extracted to the path indicated. In this example, the directory <tt>/mnt/disk</tt> will be extracted to.
<pre>nc -l 1024 | sudo tar -xvpzf - -C /media/whatever</pre>
**Sending Computer**
On the computer with the archive to send, use the following command:
<pre>cat backup.tar.gz | nc -q 0 &lt;receiving host&gt; 1024</pre>
A few comments:

*   The **-** character in the first command will tell tar to accept input from standard input rather than a file. In this case, input comes from the pipe.
*   The backup file will be expanded without being saved on the disk of receiving computer, the same as when the backup was made.
&nbsp;

# Additional Resources

*   ["Backing Up Ubuntu"](http://hddsaver.com/content/26/)
*   ["Wei’s world: HOWTO: backup my Ubuntu"](http://weichen.wordpress.com/2007/01/01/howto-backup-my-ubuntu/)
