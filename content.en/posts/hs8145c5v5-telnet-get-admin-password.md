---
title: "HS8145C5/V5 ONT: One Command to Dump the telecomadmin Password"
slug: "hs8145c5-v5-telnet-get-admin-password"
date: "2026-05-27T18:30:00+08:00"
tags: ['NETWORK', '光猫']
comments: true
description: "Stuck with useradmin on your ISP-provided ONT? No flashing, no config editing — one display command dumps the encrypted super-admin password, decrypt it, and log in as telecomadmin with full access."
---

> I am not a native English speaker; this article was translated by AI.

The HS8145C5 (or V5) ONT from China Telecom ships with only `useradmin` privileges by default — many settings are hidden. Most tutorials online tell you to modify config files or flash the Huawei firmware. But if all you need is the super-admin password, there is a more direct way.

### Prerequisite: Telnet already enabled

Newer ONTs have Telnet disabled by default. You will need an **ONT V3-V5 enablement tool** once to turn it on:

1. Unplug all cables from the ONT, only LAN1 connected to your computer
2. Set your computer IP to `192.168.1.x` (x ≠ 1)
3. Open the enablement tool, select V5 enable, pick your network interface, click start
4. Wait until a green **success** appears in the device list (all ONT LEDs stay lit), click stop, then power-cycle the ONT

Telnet stays open after reboot. You only need to do this once — it persists unless the ONT is factory-reset.

### One command to retrieve the super-admin password

Telnet into the ONT and run:

```shell
telnet 192.168.1.1
root
adminHW
su
display current-configuration grep telecomadmin
```

The output will show the line containing `telecomadmin`, something like:

```
<X_HW_WebUserInfoInstance InstanceID="2" ModifyPasswordFlag="1" UserName="telecomadmin" Password="$2;xxxxxxxxxxxxxxxxxx$" UserLevel="0" Enable="1" .../>
```

The portion between `$2;` and the trailing `$` in the `Password` field is the encrypted admin password.

### Decrypting the $2 ciphertext

Copy the entire `$2;...$` string into a **Huawei configuration decryption tool** (easily found online), use the "decrypt" function, and the plaintext password will be revealed.

Alternatively, search for a local standalone version of the same tool.

### Log in as telecomadmin

Open `192.168.1.1` in your browser, enter `telecomadmin` as the username and the decrypted plaintext as the password. You now have full admin access to the ONT — bridge mode, DMZ, TR069 deletion, any configuration you need.
