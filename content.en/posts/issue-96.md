---
title: "AI-First Blog Cleanup Log: SEO, Redirects, and a Bilingual Setup"
slug: "blog-seo-multilingual-ai-optimization"
date: "2026-01-06T03:00:00+08:00"
tags: ['Idea', 'Linux']
series: ["Network & Security"]
description: "A cleanup log: fixing 300+ legacy redirects, tweaking titles/descriptions with GSC data, and shipping a high-fidelity zh/en structure."
---

> I am not a native English speaker; this article was translated by Gemini.

This post is basically my cleanup log. A few hours ago this blog was still Chinese-only: a messy `static/_redirects` from multiple migrations, and missing meta descriptions on some high-traffic posts.

I used Google Search Console (GSC) to locate the pain first, then fixed redirects, and finally made the bilingual structure and writing rules explicit. In this round, Gemini mainly did the repetitive work and cross-checking; the decisions were still mine.

---

### 1. What GSC told me: lots of US impressions, very few clicks

- **US market**: 13,000+ impressions, only **1.46%** CTR
- **Chinese market**: CTR stayed above 6%

I used to assume "hardcore content spreads by itself", but the reality is simpler: a Chinese-only page is a wall for many overseas readers. Going bilingual isn't about looking international — it's about making the content readable once people find it.

---

### 2. Redirects: boring, but one mistake can kill your indexed URLs

After a few migrations (Farbox -> Bitcron -> Hugo), `static/_redirects` turned into a long, messy list. My first instinct was the lazy one: replace spaces with `-`, then collapse repeated dashes.

That broke immediately because of a Hugo quirk: when filenames contain `&`, Hugo can generate slugs like `google-search-tips--tricks` with `--`. If you collapse `--` into `-`, old Google results become 404s.

What I ended up doing:

- Keep both the "single-dash normalized" path and the "original multi-dash" variants (`--`, `---`, etc.), all pointing to the new slug
- Replace fuzzy wildcards (like `/post/*`) with explicit mappings, so the file is maintainable

This pass cleaned up 300+ rules into something I'm comfortable keeping long-term.

---

### 3. Bilingual: I didn't want the "English summary only" version

I set three non-negotiables:

1. **Code parity**: shell commands, Java hooks, kernel configs must match character-for-character
2. **Visual parity**: Mermaid diagrams must render on the English pages
3. **Nuance retention**: keep the traps, trade-offs, and perf data — don't translate them into bland prose

Workflow-wise, Gemini drafted and cross-checked, and I edited paragraph by paragraph until it read naturally. The first batch covered 10+ high-traffic posts.

---

### 4. Write the rules down: AGENTS.md

My biggest worry after cleanup is "I'll forget what I changed in a few months". So I added `AGENTS.md` to the repo and wrote down the rules:

- **Bilingual symmetry**: Chinese updates must be followed by high-fidelity English updates
- **SEO formula**: meta descriptions follow `[Pain Point] + [Solution] + [Result]`
- **Directory conventions**: how we keep `content.en/` structured and linked

Next time — whether it's me or an agent — we can follow the same playbook.

---

### Conclusion

I write to preserve how I solved problems; SEO and i18n just make those solutions easier to find and easier to read. For me, AI is an accelerator: it speeds up the grunt work, but the final calls (and responsibility) are still mine.

---
*Compiled by ferstar; Gemini helped with cross-checking and translation.*
