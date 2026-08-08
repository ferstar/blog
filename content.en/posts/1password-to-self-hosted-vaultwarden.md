---
title: "1Password Raised Its Price Again, So I Moved to Self-Hosted Vaultwarden"
slug: "1password-to-self-hosted-vaultwarden"
date: "2026-08-08T10:00:00+08:00"
tags: ["1Password", "Vaultwarden", "Bitwarden", "Self-hosting", "Security"]
description: "After my 1Password Families annual price rose from US$59.85 to US$71.88, I moved to self-hosted Vaultwarden and completed the migration of regular credentials and passkeys with backups, invitations, and recovery in place."
---

> I am not a native English speaker; this article was translated by AI.

The trigger was simple: 1Password raised its price again.

My three-member Families plan used to cost US$59.85 per year. The billing page showed that the next renewal would be US$71.88 per year, roughly a 20% increase. The price is reasonable, yet I no longer wanted to keep following every subscription increase. So I started looking for an alternative and eventually moved my personal vault to Vaultwarden on a VPS I run myself.

The migration itself was not especially difficult. The time went into everything around it: passkeys follow a different path from ordinary login items, a broken server can lock away the recovery credentials along with the vault, and bulk organization can trigger version conflicts.

This post records one real migration and keeps only the deployment details that matter to the move. The real hostname is replaced with `vault.example.com` here.

## The short version

- For personal or family use, Vaultwarden is lightweight enough, and the official Bitwarden browser, desktop, and mobile clients can still be used.
- Regular data such as passwords, usernames, OTPs, and notes migrated successfully; the in-app Android import moved everything, including passkeys, in this real-world test.
- I did not use `.1pux` or any export file in this migration. Everything was imported directly from another app on Android, including regular data and passkeys.
- 1Password should not be deleted immediately after the first successful import. The real completion criteria are a working new client, readable backups, and a recovery path that does not depend on the vault itself.

{{< mermaid >}}
flowchart LR
    A["1Password"] --> B["Export / CXP"]
    B --> C["Vaultwarden"]
    C --> D["Client verification"]
    C --> E["Backups"]
    D --> F["Keep 1Password until verified"]
{{< /mermaid >}}

## Why Vaultwarden

I compared three routes at the time:

- **Vaultwarden**: lightweight, with a complete Bitwarden client ecosystem, and a good fit for personal or family use. Its server is an independent implementation, so compatibility needs to be checked against the actual versions in use.
- **Passbolt**: stronger team permissions, auditing, and sharing, but with a heavier deployment and more supporting services.
- **KeePassXC**: the smallest server trust surface, but essentially a synchronized database file, which is less natural for real-time multi-user sharing.

I already had a VPS and 1Panel, so I chose Vaultwarden: keep the data on a dedicated data disk, run it with Docker, and reuse 1Panel/OpenResty for HTTPS and reverse proxying.

## The work that is easy to underestimate

### 1. Decide on the data disk and directory first

I added a 150 GiB disk to the VPS, mounted it at `/data`, and fixed the Vaultwarden data directory as:

```text
/data/services/vaultwarden
```

I ended up choosing ext4. I did compare XFS in practice: it provided somewhat more free space on an empty disk, but it cannot be shrunk. Since I might move to a smaller disk later, I prioritized room for recovery and migration over saving a little space.

There is no universal answer here. For a password manager, keeping future migration options open matters more than theoretical performance.

### 2. DNS, certificates, and the proxy are easier to break than the container

Before exposing the service, verify that DNS points to the right VPS. I hit an old IPv6 record during the process, so requests were not reaching the new machine even though the container itself was fine.

In the final setup, 1Panel manages the certificate for `vault.example.com`, using the existing Cloudflare DNS account for issuance and renewal. OpenResty reverse-proxies the hostname to Vaultwarden. This leaves one certificate manager instead of having standalone certbot and the panel maintain the same certificate at the same time.

During acceptance, do not check only whether the container is `healthy`. Check HTTPS from the public internet, redirects, the Vaultwarden health endpoint, and a real login. One later access failure turned out to be a transient DNS problem on my Mac; the remote service had stayed healthy and returned 200 all along.

### 3. Separate public sign-up from invitations

At first I disabled both public sign-up and invitations. When I wanted to share with a friend, I kept public registration closed and enabled invitations only:

```env
SIGNUPS_ALLOWED=false
INVITATIONS_ALLOWED=true
```

The friend uses their own email address and master password, then joins an Organization and Collection. Personal passwords stay in the personal vault; only items that need to be shared go into the shared collection.

Invitation email also requires SMTP. I used Mailgun SMTP and ran two separate checks: first a STARTTLS login handshake, then a real invitation email. A successful handshake only confirms SMTP authentication; delivery still needs its own test, so record the two results separately.

## The migration route that worked

### Step 1: Keep 1Password around

Before migrating, make sure the 1Password account still unlocks normally and prepare an encrypted backup. A successful login to the new service alone does not confirm that the old data is safely migrated.

### Step 2: Import directly inside the Android app

I did not use `.1pux` or create an export file first. The entire migration happened inside the Bitwarden Android app: configure the self-hosted server, then open:

`Settings → Vault → Import items → Import from another app → 1Password`

This path imported both regular data and passkeys completely. The migration relied on the app's direct app-to-app import and used no exported file.

After importing, check at least the following:

- whether usernames and passwords are complete;
- whether OTPs generate the right codes;
- whether notes, custom fields, and attachments are still there;
- whether folders need to be redesigned;
- whether a second import accidentally created duplicates.

For a first run, it is still sensible to sample a small number of important items, verify login, autofill, and passkeys on the new device, and keep the old 1Password vault available until that check is done.

Useful references:

- [Bitwarden: Import from 1Password](https://bitwarden.com/help/import-from-1password/)
- [Vaultwarden project](https://github.com/dani-garcia/vaultwarden)

### Step 3: Accept each client separately

The browser extension, desktop app, and mobile app all need the self-hosted server selected before login. The address looks like this:

```text
https://vault.example.com
```

I also tested the Bitwarden CLI. The minimal self-hosted configuration path is:

```bash
bw config server https://vault.example.com
bw config server
bw login your-email@example.com
bw status
```

There was a client-side trap unrelated to the server: at the time, the CLI installed globally with pnpm failed under Node 26.3.0 with `Cannot find module 'buffer/'`. The actual problem was the combination of the global dependency links and the runtime. Installing the same CLI version with npm and running it with Node 22 fixed it.

When the CLI fails, check how `bw` was installed, which Node version it is using, and which server it is targeting before restarting Vaultwarden.

## Vault organization taught me a practical lesson

After the migration, I wanted to reorganize 261 records that had all been sitting in `No Folder`. Classification was easy; bulk updates were not.

I made an encrypted backup first, then changed only folder ownership. I did not edit passwords, notes, or OTPs, and I did not delete duplicates. During concurrent updates, a version race in Vaultwarden temporarily moved six same-name Mattermost items to the trash. After resyncing and restoring them one by one, the item IDs matched the backup again.

That left me with a few rules:

1. Make a recoverable backup before bulk writes.
2. Treat a one-field update as a real data change.
3. Concurrent requests are not always faster; stale client copies can create races.
4. Final verification should compare totals, item IDs, and the trash, not just HTTP 200.

The vault is now organized into Work and Internal, Development and Cloud Services, Personal Accounts, Communication and Social, Finance and Identity, Home and Devices, and Security and Keys. All 261 items left `No Folder`. I did not delete duplicates without review.

## A backup is not “export one JSON file”

Self-hosting changes the psychology of the problem: you own the recovery responsibility.

This is how I closed the loop:

- the database, attachments, and configuration live under `/data`;
- the VPS creates backups on a schedule;
- only after the local backup succeeds, it syncs over SSH to another host, `DO_NEW`;
- backup files use an encrypted format and produce verifiable results;
- recovery credentials for the cloud account, DNS, email, and VPS are not all stored in this vault; at least one independent break-glass path remains.

A copy stored only on the same VPS provides no off-site protection. A backup also needs a restore test before it can be trusted. Perform at least one temporary restore and verify the database, attachments, configuration, and client login.

## Final judgment

This migration convinced me that Vaultwarden can replace 1Password for personal or family use. Starting the container is only the first step.

You give up part of the managed service and take on DNS, TLS, SMTP, upgrades, logs, backups, and recovery. Ordinary password data moves easily. Passkeys, sharing permissions, and disaster recovery are where the careful work belongs.

If the only goal is to save the subscription fee and you do not want to maintain backups and recovery, the trade-off may not be worthwhile. If you care more about data control and client freedom, and are willing to operate it like a small production service, Vaultwarden is a practical option.

For me, migration was complete only when all four answers were yes:

- a new device can log in and autofill;
- OTPs and important attachments have been sampled;
- passkeys have been verified in the target client, or have an explicit site-by-site recreation plan;
- if the VPS disappears, there is still an independent recovery route and a verifiable backup.
