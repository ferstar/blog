---
title: "AI-First Blog Cleanup Log: SEO, Redirects, and a Bilingual Setup"
slug: "blog-seo-multilingual-ai-optimization"
date: "2026-01-06T03:00:00+08:00"
tags: ['Idea', 'Linux']
series: ["Network & Security"]
description: "A cleanup log: fixing 300+ legacy redirects, tweaking titles/descriptions with GSC data, and shipping a high-fidelity zh/en structure."
---

> I am not a native English speaker; this article was translated by AI.

This post is basically a renovation note for the blog. A few hours earlier, the site was still Chinese-only: `static/_redirects` had a pile of old rules from several migrations, and many posts with decent traffic still had no description.

I first used Google Search Console (GSC) to find where the pain was, then cleaned up redirects, and finally added the bilingual structure and writing rules. In this round, AI mostly handled repetitive work and cross-checking. The calls on what to keep and what to delete were still mine. Fair enough, since the model is not going to take the blame if I break the site.

---

### GSC poured some cold water on me first

The data was simple, but not pleasant:

- **US market**: 13,000+ impressions, only **1.46%** CTR
- **Chinese market**: CTR stayed above 6%

I used to think technical posts would find readers as long as the content was solid. In reality, when a fully Chinese page shows up in search results, many overseas readers will just skip it. Going bilingual is not about looking international; it is about letting people who already found the post actually read it.

---

### Redirects look small, but they can quietly kill indexed URLs

After moving the blog from Farbox to Bitcron and then to Hugo, `static/_redirects` was not pretty. My first lazy idea was to replace spaces with `-`, collapse repeated dashes, and call it done.

Hugo corrected me pretty quickly. Filenames with `&` can generate slugs like `google-search-tips--tricks`, with two dashes in the middle. If a script helpfully collapses `--` into `-`, already-indexed Google URLs go straight to 404.

I ended up using a dumber but safer approach:

- Keep both the single-dash normalized path and the original multi-dash variants (`--`, `---`, etc.), all pointing exactly to the new slug
- Replace fuzzy wildcards (like `/post/*`) with explicit mappings, so debugging later does not become guesswork

This pass cleaned up 300+ legacy redirects into something I am comfortable keeping long-term. The file is still not short, but at least every rule has a reason to exist.

---

### Bilingual does not mean appending a short English summary

I did not want a half-finished setup with the Chinese post plus a tiny English abstract, so I set a few rules for translations:

1. **Code parity**: shell commands, Java hooks, and kernel configs must match character-for-character
2. **Diagram parity**: Mermaid diagrams must render on the English pages too
3. **Do not sand off the details**: traps, trade-offs, and performance numbers should stay, not turn into lukewarm prose

The workflow was: AI drafted, then AI cross-checked the Chinese and English versions; I edited paragraph by paragraph and cut or rewrote anything that sounded too templated. The first batch covered 10+ high-traffic posts. The older debt can be paid down slowly.

---

### Put the rules in AGENTS.md, because memory is unreliable

After the cleanup, my biggest worry was not that the code would break. It was that I would forget why I made these choices a few months later. So I added `AGENTS.md` to the repo and wrote down the ground rules:

- **Bilingual alignment**: after a Chinese update, the English version must be updated with high fidelity
- **SEO description**: descriptions follow `[Pain Point] + [Solution] + [Result]`
- **Directory convention**: keep `content/` and `content.en/` separate, and handle links as a multilingual site
- **No redirect rollback**: `static/_redirects` should use explicit rules only, no lazy `/post/*`

It is not complicated, but it helps. Next time, whether I come back myself or ask an agent to continue, there is a runnable set of rules instead of "probably close enough".

---

### Closing

I write blog posts to preserve how problems were solved. SEO and bilingual pages just smooth the path to the door, making those notes easier to find and easier to finish reading.

For me, AI is more like a power tool: checklists, bulk edits, cross-checks — it is fast at those. But the final trade-offs, tone, and responsibility are still mine. That is probably for the best. If something breaks later, I know exactly who to blame.

---
