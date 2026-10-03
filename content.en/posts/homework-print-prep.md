---
title: "Turning Phone Photos of Homework into Printable A4: Notes on Homework Print Prep"
slug: "homework-print-prep"
date: "2026-10-04T00:00:00+08:00"
tags: ["Python", "OpenCV", "Rust", "OCR"]
description: "Homework photos sent in class groups are skewed, covered in watermark ads, and mixed in orientation — unprintable. This open-source project uses an OpenCV perspective-flattening plus Rust OCR orientation pipeline to auto-process pages onto A4; upload in a browser and download a print-ready PDF, deployable on a single machine."
---

> I am not a native English speaker; this article was translated by AI.

Printing a kid's homework is a familiar chore for many parents: the teacher posts photos in the class group chat, the pages are skewed, the margins carry mini-app watermarks, landscape and portrait pages are mixed together, and the printout is a mess. I tried scanner apps, but their goal is "archival scans" — they output scan-style images with watermarks and know nothing about A4 layout.

So I built something narrower: **Homework Print Prep**. Upload a PDF or photos, and it flattens the paper, removes watermarks outside the content, rotates pages upright, and fills an A4 sheet; after previewing you download a print-ready PDF or print directly. The hosted version runs on my own VPS ([dazuoye.ferstar.org](https://dazuoye.ferstar.org)), and the code is open source at [github.com/ferstar/homework-print-prep](https://github.com/ferstar/homework-print-prep).

## The pipeline

Every page follows the same chain:

{{< mermaid >}}
flowchart LR
    A[Upload PDF / photos] --> B[Frontend composes<br>images into a PDF]
    B --> C[Perspective flatten]
    C --> D[Watermark removal]
    D --> E[OCR orientation]
    E --> F[Crop to content box]
    F --> G[Fill A4]
    G --> H[Document-wide orientation]
    H --> I[Preview tweaks / export]
{{< /mermaid >}}

A few stages in more detail:

**Perspective flattening.** For a photographed sheet, the paper edge is found first: closed border → content hull → paper-edge fallback; once the quad is found, `getPerspectiveTransform` + `warpPerspective` flattens it in one step. Camera shots (the browser reads EXIF and reports it) prefer the paper edge, cutting the paper out with GrabCut, so a cluttered desk background is no problem. The tricky case is photos forwarded through chat apps — EXIF is stripped, so the server decides once: if it finds a tilted sheet and the area outside the paper is not a flat digital background, treat it as a photo; otherwise treat it as a screenshot and skip cropping. When automatic flattening fails, the preview page has an Office Lens-style corner editor: drag the four corners manually, and the quad is final — no second crop afterwards.

**Watermark removal.** Homework page margins often carry mini-app logos, banner text, and teal copyright marks. The approach estimates a content box first, then clusters only the isolated small connected components outside it and wipes them with local paper color; QR codes and teal marks expand into whole plates and are wiped together. Educational QR codes, page numbers, and seal lines inside the content box are never touched — they are part of the homework itself.

**OCR orientation.** Each of 0/90/180/270 runs through the embedded Rust OCR (ocr-rs + MNN; the PP-OCRv6 tiny model is checksum-verified at build time and embedded, so nothing is downloaded at runtime), and the best direction wins on confidence plus text-line scores. After the whole document is processed, a document-wide pass unifies orientation: majority vote on reading direction decides landscape vs portrait, individual pages get rotated and re-laid out, and landscape homework is never blindly turned portrait.

**Paper-white enhancement is off by default.** For gray paper you can enable it: morphological illumination estimation followed by soft brightening — no binarization, trying hard to preserve pencil and light writing. But it risks washing out faint strokes and the illumination estimate is expensive, so it stays off by default, and when enabled the preview must be checked before printing.

## Engineering decisions worth calling out

**Soft-failure philosophy.** Whenever perspective, orientation, or paper-white enhancement is unreliable, it returns the original image plus a reason, and never throws an exception that kills the whole page. A too-extreme camera angle, degenerate detection geometry, or a crashed OCR worker all end as "this page stays as-is" rather than a failed job. For image algorithms like these, doing less beats doing wrong — warping the paper is far worse than not warping it.

**One lossless cache per page.** Margin tweaks and paper-white toggles reuse the lossless PNG after orientation, watermark removal, and cropping — no OCR re-run. The cache key includes page settings and `CACHE_VERSION`; changing a preprocessing algorithm or the embedded model bumps the version and invalidates everything.

**Rate-limit even on a single machine.** Reprocessing is CPU-heavy, so uploads, single-page reprocessing, batch reprocessing, manual wipes, and export share one FIFO bounded queue: by default 1 concurrent, 4 queued; full returns 429, wait timeout returns 503, and the web UI shows a retry countdown while keeping the operation and the already-uploaded file. Documents go through Cloudflare R2 direct upload plus CDN: the browser uploads via a 5-minute signed PUT URL, downloads hit the CDN, so user uploads and downloads never touch VPS bandwidth, and export URLs carry a content hash so they never hit a stale version.

**Feedback loop.** Every page can be up- or down-voted; each vote change stores the page parameters, processing metrics, and preview version alongside it in SQLite. Files are retained by feedback class: down-voted 30 days, up-voted 7, no feedback 1 — down-voted samples are kept longest, banked as regression cases.

**Tests lean on synthetic scenes.** Real homework data cannot live in the repo, so regression relies on generated Chinese exam papers with region annotations: 36 curated scenarios covering framed/unframed, single/double column, sparse and edge-hugging content, faint strokes, shadows, rotation, and perspective, exporting comparison images plus region-retention metrics (are pinyin, formulas, thin lines, page numbers, and QR codes still there). Real samples ship via GitHub Release, unpacked into a gitignored `fixtures/` for local end-to-end checks.

## Stack and deployment

Backend: FastAPI + OpenCV + PyMuPDF on Python 3.14, managed by uv (src layout; `uv sync` compiles the Rust OCR worker along the way). Frontend: React + TypeScript + shadcn/ui; the Vite build output is packed into the wheel, so production needs only Python. The OCR worker is a resident subprocess, reused serially, restarted automatically on timeout or crash. Deployment is one small VPS plus Docker, single-process uvicorn — the queue is in-process, and multiple workers would each run their own, which is deliberate: rather than going distributed, make the single machine solid.

## Known limits

Export is a raster PDF at roughly 160 DPI, not vector; curved-page flattening is unsupported; without a reliable paper edge or border, perspective correction falls back conservatively and may keep a slight trapezoid; extremely faint pencil can still wash out under paper-white enhancement. All of this is spelled out in the README — no pretending it handles everything.

From first commit to 1.0 going live took three days, and most of that time actually went into the corner editor and the queue — the "uncool" parts. But those are exactly what users feel best: when flattening fails you can drag the corners yourself, and during peak hours you queue without re-uploading.
