# AI Agent Operational Guide & History

This document serves as the source of truth for AI Agents interacting with this blog repository. It outlines critical workflows and historical optimizations to ensure consistency and performance.

## 1. Multilingual Content Mandate

To maintain the global reach established in January 2026, the following protocol is **mandatory** for all new content:

- **Bilingual Symmetry**: Every new post created in `content/` (Chinese) MUST have a corresponding high-fidelity translation in `content.en/` (English).
- **High-Fidelity Standard**:
    - **Code Parity**: All shell commands, Java/Python snippets, and configurations must be identical between versions.
    - **Visual Assets**: Mermaid diagrams and data tables must be fully preserved and rendered correctly in both languages.
    - **Nuance Retention**: Philosophical insights, "expert's blind spots," and technical troubleshooting logic must be translated with depth, avoiding over-simplification.
- **Disclaimer**: Every English post must include the standard disclaimer:
  `> I am not a native English speaker; this article was translated by Gemini.`

## 2. SEO Optimization History (Jan 6, 2026 Session)

The following measures were implemented based on Google Search Console (GSC) data analysis:

### A. Redirect Architecture
- **Standardization**: Cleaned and slugified 300+ legacy redirects in `static/_redirects`.
- **Compatibility**: Added specific rules for "multi-dash" slugs (e.g., `google-search-tips--tricks`) to ensure historical Google search results do not break.
- **Precision**: Removed fuzzy wildcard redirects (`/post/*`) in favor of explicit mapping.

### B. Metadata & Content Discovery
- **Top-10 Optimization**: Applied custom `description` fields to the top 10 high-traffic posts using the `[Pain Point] + [Solution] + [Result]` formula.
- **CTR Recovery**: Retitled and re-described "high impression, low CTR" pages (e.g., Windows Resource Protection fix, ShellClash upgrade) to boost organic clicks.
- **Internal Linking (Series)**: Grouped related posts into Hugo `series` (e.g., "Network & Security", "Kernel Development") to improve link equity distribution and user retention.

### C. Multilingual Architecture
- **Structure**: Implemented `contentDir` partitioning (`content/` for zh-cn, `content.en/` for en).
- **Navigation**: Fixed multi-language Archive and Tag links using Hugo `pageRef`.
- **UX**: Configured language-specific homepage settings (e.g., disabling `showMoreLink` for the English version until content volume exceeds 20 posts).

---
*Maintained by ferstar and Gemini.*
