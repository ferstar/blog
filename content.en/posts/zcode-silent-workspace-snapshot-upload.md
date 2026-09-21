---
title: "Inside ZCode: Silently Uploading Your Entire Git History to the Cloud"
slug: "zcode-silent-workspace-snapshot-upload"
date: "2026-09-18T02:00:00+08:00"
lastmod: "2026-09-21T14:45:00+08:00"
tags: ["Security", "Privacy", "AI Coding", "Reverse Engineering"]
description: "ZCode silently uploads full Git history to the cloud; this post provides a block rule and source review — checkpoint claims fall apart against the code."
---

> I am not a native English speaker; this article was translated by AI.

It started with a routine check while freeing up disk space: `~/.zcode` was taking up over 700MB. After digging into it intermittently, I confirmed something pretty wild:

**Whenever you are logged in, ZCode (Zhipu's official AI coding desktop app) silently packages your entire workspace — complete `.git` history, LFS asset cache, reflogs, and global app configs — encrypts it, and uploads it directly to Aliyun OSS.**

Even more ironic: **the RSA public key used for encryption is delivered on the fly by the server, while the private key lives exclusively in the cloud.** You cannot decrypt that multi-hundred-megabyte ciphertext sitting right on your own disk, and neither can the ZCode client itself.

Here is the complete record of the investigation, the evidence chain, and a one-liner defense that permanently shuts it down.

*(Note: Following official responses and open-source updates, see the Sep 21 section below for code verification and clarifications; first-time readers can jump straight to the technical breakdown below.)*

## Update, 2026-09-21

This morning (Sep 21) at 09:23, ZCode officially posted a [statement on X](https://x.com/zcode_ai/status/2101844704933621971) and dropped their supposed open-source core repository ([GitHub: zai-org/ZCode](https://github.com/zai-org/ZCode)). With the source code now public alongside third-party audit reports, official explanations can finally be cross-referenced line by line against the actual codebase.

### 1. Code Review: A Stripped-Down Two-Commit Drop (PRs Locked, Issues Disabled)

Digging into the newly published Git repository, the picture matches expectations of standard corporate defense:
- **Historical Git commits completely wiped**: The repository contains only two commits — an empty initial commit, followed by a massive `feat: open source` commit dumping 6,973 files and 1.03 million lines of code at once. The internal development commit history of the open-source repo itself was entirely flattened; there is no way to trace the evolution of the old upload sidecar, nor any commit diff showing how the `repoSnapshot` pipeline was excised. Moreover, the repo locked PRs and closed Issues, making it strictly a one-way code dump.
- **License**: Apache-2.0.
- **Upload pipeline fully purged**: Searching the codebase for the previously captured `/api/v1/snapshot/upload-credential`, direct `PostObject` OSS uploads, AES-256-CTR encryption, and public key delivery returned zero matches. The pipeline has been stripped clean with not a single line remaining.
- **Repo Wiki thoroughly scrubbed**: Except for an external Wikipedia reference, all mentions of Repo Wiki have been removed. Code indexing and symbol search have reverted entirely to local processes utilizing bundled `ripgrep 14.1.1` and `bfs 4.1.1` — proving that local codebase retrieval never needed full-repo uploads in the first place.
- **An ultra-defensive NOTICE.md**: Even more revealing is the 27KB `NOTICE.md` in the root directory. Legal counsel armored every outbound network request and added disclaimers to even the hollowed-out Computer Use placeholders, while conspicuously leaving out any mention of whole-repo uploads.

### 2. The Checkpoint Mechanism Exposed: Code Confirms Purely Local Git

The official statement originally claimed that uploading repository snapshots was necessary for "session checkpoint rollback." Looking at the source, I located the actual implementation of checkpoints (`packages/services/src/git/gitCheckpointService.ts` and `gitCheckpointRepo.ts`):
- **How it works**: It runs purely on the local system's Git CLI, executing `git diff --name-status` and `git diff --numstat` based on commit OIDs scoped strictly to the current workspace.
- **Storage**: Metadata is persisted locally as JSON files under `~/.zcode/checkpoints/`.
- **The verdict**: The open-source code confirms that checkpoints are strictly local Git diff utilities with zero cloud dependencies, having nothing to do with whole-repo packaging. The official claim that "checkpoint rollback necessitated full-repo uploads" completely falls apart against the code.

### 3. Third-Party Audits and "Bucket Deletion"

The official statement cited assessment conclusions from the China Academy of Information and Communications Technology (CAICT) and NSFOCUS:
- **Findings**: Both confirmed that the `zcode-prod` Alibaba Cloud OSS bucket is empty and the bucket itself has been deleted; they also confirmed that client v3.14.0 removed the local snapshot upload workflow.
- **Objective takeaway**: Deleting the bucket is a necessary containment move. But in technical terms, **deleting a temporary transit bucket only proves the bucket is gone now — it cannot prove whether data previously dumped into it was decrypted, cloned, or used to fine-tune models during its active lifecycle**. An audit agency checking an empty bucket on Sep 20 cannot retroactively reconstruct what took place before Sep 18.

### 4. Community Clarifications and a Bit of Real-World Irony

With the [original post](https://x.com/ferstar_org/status/2100805861002355154) crossing 1.6 million impressions and traffic normalizing, a few ongoing community narratives deserve clarification:
1. **Neither a "Community Developer" nor an "Overseas Hacker"**: The official statement vaguely thanked "community developers who identified issues" (without ever @-tagging or even obliquely naming me) — classic PR minimization. I was never a contributor or community developer of ZCode; I was simply a paying Coding Plan subscriber who uncovered unannounced exfiltration of private code and published the packet capture evidence. Similarly, rumors labeling me a "mysterious foreign hacker" or "reverse engineering master" are pure nonsense; the investigation relied on basic local networking tools and unpacking. As for the absurd accusation of "handing knives to foreign adversaries to smear domestic AI" — when a paying engineer discovers commercial code being silently exfiltrated behind their back, publishing packet captures is basic self-preservation. If pointing at the elephant in the room is "handing knives", is staying silent while code is quietly siphoned supposed to be "support"? Real engineering safety is never achieved by sweeping leaks under the rug.
2. **The Truth Behind the "2:00 AM Midnight Post" Myth**: Many cited the post header timestamp, assuming I stayed up until 2:00 AM to publish the write-up. In reality, this serves as a textbook real-world irony that **trusting AI blindly is worse than having no AI at all**: my actual Git commit timestamp was `Fri Sep 18 10:35:05 2026 +0800` — broad daylight on Friday morning. The `02:00:00` in the front matter occurred simply because I got lazy and used an AI helper to generate Hugo metadata after drafting the technical notes. The AI hallucinated that timestamp, and in my rush to verify the network blocking, I didn't double-check it. While writing a post cautioning developers against blindly trusting AI tools behind their backs, I got burned by an unchecked AI-generated timestamp, inadvertently spawning an internet myth about a "midnight raid." Laugh it off, but take it as the most grounded reminder: the moment you get lazy and trust an AI blindly, it will find a way to bite you in the rear.

## Update, 2026-09-19

Following widespread community attention after this post, Z.ai released an official statement in their user community on Sep 18 at 17:44 (with tech media like IT Home picking up the story later that evening). This section provides an objective cross-check. The original investigation below remains unchanged.

### What the company said

Z.ai posted their statement on Sep 18 at 17:44; public coverage can be found on [IT Home](https://www.ithome.com/1/004/310.htm). Key points:

- The issue came from "codebase indexing", used for local indexes, session checkpoint restore, and Repo Wiki;
- Generating Wiki pages in the cloud "may" trigger an upload of repository data;
- After the Wiki is generated, the uploaded data is destroyed immediately and is not stored;
- The feature was on by default in its early launch period; some users were affected; the issue "has been fixed";
- ZCode will be open-sourced soon, with third-party review; all users get one extra weekly quota reset.

The fact that uploads occurred is no longer contested by Zhipu. What remains in question is the actual upload scope, user toggles, and how anyone outside the company is supposed to verify "destroyed immediately".

### Reverse Engineering & Local Evidence vs. Official Claims (Old Version 3.12.3 vs. 3.14.0 vs. Official Statement)

To prevent confusion between client versions, here is a direct comparison between the affected old version (3.12.3) when caught, the reverse-engineered 3.14.0 release, and the official statement:

| Dimension | Official Statement (Sep 18 17:44) | 3.12.3 Client Audit (Affected Version) | 3.14.0 Client Audit (Remediated Version) |
|---|---|---|---|
| **What was sent** | Repository data (for Wiki) | Full-workspace snapshots, ~87% `.git` — objects, LFS, reflogs | Upload pipeline code physically stripped; only local checkpoints remain |
| **Trigger mechanism** | Wiki page generation "may" upload | Upload sidecar resident with login; `captureBeforePrompt` (before every prompt) and `repo-wiki-update` trigger unconditionally | Upload sidecar dismantled; no longer triggers cloud packaging |
| **Can you turn it off** | No mention of a switch to stop uploads | Disabling "Optimize Experience" and "Repo Snapshot Indexing" still packaged and attempted direct OSS uploads | Code pipeline physically removed |
| **Cloud-side handling** | Destroyed immediately after generation | Not verifiable from outside (and logically contradicts the claimed "checkpoint restore" feature) | Cloud `upload-credential` endpoint pulled (returns 404) |
| **Retained data** | Claims data is not stored post-Wiki | Snapshot of a 538-file public repo accepted by server; retention/decryption rights unaddressed | Whether existing cloud snapshots were physically wiped cannot be verified externally |

One thing the original post left easy to misread: the 313MB commercial project sat in `pending` (`failureCount: 564`) and **did not upload successfully**. A separate, tiny public-repo workspace did: 538 files, about 15KB after compression and encryption, status accepted by the server. So "did anything actually leave the machine" — yes, at least that one.

Someone else reproduced the same directory layout and state files on Windows, including multiple small workspaces with no failure record that look accepted: [NodeSeek](https://www.nodeseek.com/post-935260-1). Another local cross-check: [silencestar](https://blog.silencestar.com/posts/zcode-repo-snapshot/).

I archived the [privacy policy](https://zcode.z.ai/cn/privacy) on Sep 18. The page still said it was last updated 2026-06-15, and still did not mention full-workspace snapshots or cloud sync.

### A Few Personal Clarifications

1. **Did the 313MB commercial project actually get uploaded?**: To be 100% clear, that 313MB commercial repo snapshot failed 564 times because it exceeded size limits, remaining stuck in local `pending` — **it was never successfully uploaded**. I run an OpenWrt router at home; checking connection tracking and traffic flow records confirmed those encrypted chunks never left the local network.
2. **Definitely not a "reverse engineering wizard" — credit goes to my base-spec MBA**: Some people online started calling me a "reverse engineering expert," which is completely unnecessary. The entire trigger was laughably mundane: thanks to Apple's storage being priced like solid gold, my base-spec 256GB MacBook Air is perpetually starved for disk space. I was freeing up space when I noticed `~/.zcode` mysteriously devouring over 700MB. My engineering spider-sense tingled, so I unpacked `app.asar` to see what the hell was going on (on my other machine with a 2TB NVMe running Arch Linux, I wouldn't have blinked twice at a measly few hundred megs). Besides, given the state of modern AI, anyone with a coding agent is effectively a reverse engineer now — pull any decent agent off the shelf, feed it this post and the source files, and it'll break down the entire architecture with flawless clarity. It’s hardly some exclusive black magic; it was just basic engineering curiosity and troubleshooting.
3. **The bitter irony**: I was actually a long-term subscriber and supporter of GLM Coding Max myself. The funniest part is that on the evening of Sep 17, I was enthusiastically pitching ZCode to peers in a developer group chat. Less than half a day later, reality hit me right in the face when I caught this silent whole-repo packaging routine myself.

### Does the mitigation still matter

Yes. Even though 3.14.0 removed the code and the gateway route returns 404, the desktop client can still receive hot updates. The filesystem lock below remains active as a tripwire. The NodeSeek post has the Windows ACL equivalent.

### Still unanswered

1. How do you prove "destroyed immediately" from the outside? Have existing cloud-stored encrypted snapshots been physically purged, and who holds private key decryption rights?
2. The claimed "checkpoint restore" contradicts "destroyed immediately" — what exactly was retained in the cloud?
3. Will the open-source drop include the historical upload sidecar that was caught, or only the latest sanitized commit? *(Sep 21 source code confirms: commit history was completely flattened into 2 commits, see Sep 21 update above)*

*(Note: Open-source code verification has been added to the Sep 21 section above)*

## The Starting Point: A 313MB Archive Stuck in Pending

`~/.zcode` is the data root of ZCode. The size breakdown looked roughly like this:
- `cli/`: ~257MB (session databases, execution logs)
- `computer-use/`: ~130MB (bundled app and runtime dependencies)
- `v2/checkpoints/`: ~303MB (the main suspect)

Inside `v2/checkpoints/`, I found a 313MB `.enc` file alongside a state metadata file:

```json
{
  "workspacePath": "/Users/ferstar/myprojects/<a commercial project>",
  "lastCompressedSize": {
    "encryptedSizeBytes": 313070842,
    "workspaceSizeBytes": 345549173
  },
  "kind": "baseline",
  "failureCount": 564
}
```

The story was straightforward:
1. The client scanned my active commercial project, excluded `node_modules` and a few others, and packaged the remaining 345MB into a 313MB encrypted archive labeled `baseline` (full snapshot);
2. It recorded 564 failed upload attempts, leaving it sitting in the local `pending/` directory waiting for the next retry.

The repository totaled 10GB; minus dependencies, the remaining 345MB was almost entirely core intellectual property.

## Where It Goes: From Logs to asar Reverse Engineering

The logs contained no explicit upload URLs, so I cracked open the client's `app.asar`. The reconstructed upload flow:

{{< mermaid >}}
sequenceDiagram
    participant C as ZCode client
    participant S as zcode.z.ai
    participant O as Aliyun OSS
    C->>S: POST /api/v1/snapshot/upload-credential
    S-->>C: snapshot_id + RSA public key + max_size + OSS form credentials + callback
    C->>C: tar.gz pack → AES-256-CTR encrypt → RSA-OAEP wrap key
    C->>O: PostObject direct upload of tar.gz.enc
    O->>S: callback confirms receipt
{{< /mermaid >}}

The pipeline runs in two stages:

1. **Request credentials from coordinator**: The client calls `https://zcode.z.ai` (`VITE_ZCODE_ENDPOINT_ORIGIN` in code). The server returns OSS form signatures (`policy`, `x-oss-signature`), a dynamic Object Key, size limits, and the RSA public key for this encryption round;
2. **Direct form POST to OSS**: After archiving and streaming encryption locally, the client **bypasses ZCode's own application servers and posts `tar.gz.enc` directly to Aliyun OSS via an HTTP POST form**. OSS then calls back to Zhipu's backend to register the snapshot.

Inspecting active sockets confirmed this: the running ZCode process maintained persistent HTTPS connections to `zcode.z.ai` IP endpoints plus two Aliyun OSS storage nodes.

## The Most Ironic Part: The Key Belongs to the Server

The encryption implementation uses textbook envelope encryption:

```javascript
keyId: String(i.encryption.key_version),
keyWrapAlgorithm: "rsa-oaep-sha256",
publicKeySpkiPem: Ylt(i.encryption.public_key)
```

- Content is encrypted using an ephemeral symmetric key via AES-256-CTR;
- The symmetric key is wrapped using RSA-OAEP-SHA256 with the public key supplied by the server.

The critical catch is that public key: **it is handed down by the server during credential negotiation, and the corresponding private key never touches your machine.** Unwrapping the envelope key with all local private keys on my system failed, as expected.

In other words: that 313MB ciphertext on your drive cannot be opened by you or the client. Only Zhipu's backend holds the key to unlock it.

If this feature were genuinely built for user-facing rollback or cross-device sync, the keys would live locally (just like Git or Time Machine). **A key that only the server can use serves exactly one purpose: making sure the server can read your code whenever it wants.**

## What Gets Packed: Nearly 90% Is .git

Even though the ciphertext is locked, the Manifest (file inventory) generated during packaging is saved locally in plaintext. Breaking down a snapshot of 42,411 files:

| Content | Size | Proportion | Information Contained |
|---|---|---|---|
| `.git/lfs/` | 196.1 MB | 56.8% | LFS cache — all binary assets and large media ever downloaded |
| `.git/objects/` | 102.2 MB | 29.6% | Complete commit history object store (commits, trees, blobs) |
| `.git/logs/` | 0.6 MB | 0.2% | reflogs — local branch history and unpushed operational traces |
| Source code & docs | ~46.2 MB | 13.4% | `src/`, config files, internal documentation |

The `.git` directory alone accounts for **86.6%** of the payload.

Once uploaded, the cloud receives far more than your current working tree — it gets **the entire lineage of your repository since day one**:
- Historical API keys and sensitive configs that were deleted in later commits;
- Unpushed local branch names (which reveal unreleased feature plans);
- Internal GitLab hostnames and repository paths configured in `.git/config`.

Furthermore, an extra manifest named `repo_snapshot_extra_manifest` hashes your global ZCode configuration files (such as `settings.behavior.json`) and bundles them across workspaces with every snapshot.

## The Truth About the Switches: UI Toggles Don't Stop It

The natural reaction is checking settings to toggle it off. I cross-referenced the UI options with the codebase:

| Switch | What you expect it to do | What it actually does |
|---|---|---|
| **Optimize Experience** (`optimizeAgentExperienceEnabled`) | Disables telemetry / data collection | **Only controls whether data is authorized for model training**. Snapshot capture and upload still run |
| **Repo Snapshot Indexing** (`repoSnapshotIndexingEnabled`) | Disables the snapshot feature | **Only controls whether the server indexes uploaded snapshots**. Local packaging and upload continue uninterrupted |

Looking at host assembly code makes it crystal clear: the capture/upload sidecar is **instantiated unconditionally** at startup. There are no gating `if` checks on user preferences; the only requirement is that `tokenProvider` can return a valid JWT.

**Bottom line: as long as you are logged in, this background pipeline is permanently active, and no UI setting can turn it off.**

Capture triggers occur at two points: `captureBeforePrompt` (before every prompt) and on task completion tagged with `repo-wiki-update`. In session logs, a single active session generated up to 62 capture events.

## What the Privacy Policy Says

Checking ZCode's privacy policy, it explicitly states that it collects "text, files, and code submitted during conversations" — standard practice for feeding context to LLMs.

However, across the entire policy, FAQs, and changelogs, there is **not a single mention of silently packaging and uploading entire workspaces and full Git histories**.

The closest mention is the generic template statement: "optimization program is off by default, and inputs will not be used for training without consent".

## Defense: Deleting Is Whack-a-Mole; Lock the Directory

When I first found the pending package, I simply deleted it. Within half an hour, it re-captured — a fresh 313MB archive with the retry counter ticking from 564 to 565. When the uploader sees the file is gone, it just packs a new one. Manual deletion is whack-a-mole.

The cleanest and most effective solution is setting an immutability flag at the filesystem level, denying write access at the kernel level:

### macOS

```bash
# Wipe and lock the checkpoints directory
rm -rf ~/.zcode/v2/checkpoints
mkdir -p ~/.zcode/v2/checkpoints
chflags uchg ~/.zcode/v2/checkpoints

# Verify: should output "Operation not permitted"
touch ~/.zcode/v2/checkpoints/test
```

### Linux

```bash
# Wipe and lock the checkpoints directory
rm -rf ~/.zcode/v2/checkpoints
mkdir -p ~/.zcode/v2/checkpoints
sudo chattr +i ~/.zcode/v2/checkpoints

# Verify: should output "Operation not permitted"
touch ~/.zcode/v2/checkpoints/test
```

### Impact & Rollback
- **Result**: The capture logic gets blocked by the kernel whenever it attempts disk I/O. Without local artifacts, the upload pipeline has nothing to send;
- **Trade-off**: The "checkpoint rollback / timeline" UI feature won't work (which always required uploading your code in the first place). Normal chat, autocomplete, and tool executions work without issue. Swallowed I/O errors in logs are harmless;
- **To restore**: Run `chflags nouchg ~/.zcode/v2/checkpoints` (macOS) or `sudo chattr -i ~/.zcode/v2/checkpoints` (Linux).

## Closing Thoughts

When using AI tools, model inference inevitably needs code context — everyone accepts that going in. But this behavior clearly crosses the line in two ways:

First, **data scope**. Inference sends task-relevant context; snapshotting exfiltrates the entire repository along with years of Git commit history.

Second, **architectural posture**. If this were genuinely designed for user-side restore or syncing, the decryption keys would belong to the user. An encryption key held exclusively by the server, zero disclosure in privacy policies, unstoppable background uploads, and stubborn re-packaging upon deletion — this looks less like backup and far more like collection.

Tools are tools, but users must draw their own boundaries. If the software won't let you turn it off, use the OS kernel to lock it in a cage.
