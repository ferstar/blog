---
title: "Notes on a Batch of Demo Logs: Why 'Wrapping Everything in an Agent to Make a SaaS' Is an Absurd Illusion"
slug: "the-illusion-of-agent-saas"
date: "2026-09-03T15:10:00+08:00"
tags: ["AI", "Agent", "SaaS", "Architecture", "Engineering"]
description: "Many believe wrapping business workflows inside an Agent makes building SaaS easy; inspecting live demo logs reveals why using probabilistic models as deterministic enterprise backbones is a fragile illusion."
---

> I am not a native English speaker; this article was translated by AI.

Yesterday, I spent time reviewing a batch of demo session logs from an internal development build of a desktop Agent. From PowerPoint deck generation to cross-department action checklists, down to complex cash flow forecasts and sales contract compliance audits, the demo lineup looked impeccably structured.

At a surface glance, every demo delivered striking end results: pinpointing contractual risks, calculating liquidity turning points, and autonomously running Python scripts to render sleek, tech-blue inline SVGs and standalone HTML files that open cleanly in any offline browser.

Yet peeling back the underlying interaction traces, token throughput, and execution timelines left me with an overwhelming sense of cognitive dissonance.

Across the industry today—whether among clients, business executives, or product managers—a dangerous and lazy assumption is spreading: **"In the past, building a CRM, ERP, or approval workflow required dozens of database tables and six months of development. Now, just wrap an LLM in an Agent shell, attach a few tools and scripts, and 'solve any business problem with a single prompt'—presto, you have a modern AI-native SaaS!"**

Believing that cramming every conceivable task into an Agent shell makes building enterprise SaaS effortless is not just unrealistic; inspecting the real operational logs and the engineering mess uncovered afterward makes it plain that this is an absurd illusion running counter to basic software engineering reality.

---

## 1. The Engineering Clutter Behind Flawless Demos

Looking into yesterday's nine demo sessions, every scenario that produced an "impressive result" was skating right along brittle engineering boundaries:

### 1. Extremely Fragile Determinism: Sustained Only by Babysitting Prompts
In hardcore business demos like "Corporate Cash Flow Tracking" or "Cross-Department Action Checklist", the user's initial prompt was never a concise natural instruction. Instead, it was a 300-to-500-word defensive micro-contract packed with strict boundary guardrails:

> "Distinguish confirmed collections from estimated collections... Do not fabricate receipt dates or approval decisions... Do not overwrite original files... Only assign owners and due dates when explicitly committed in the source files, otherwise mark as 'Pending Confirmation'..."

This is not intuitive natural language interaction; this is a software engineer manually hand-coding missing defensive assertions into a prompt.
When faced with an ordinary user prompt (such as a casual line from the logs: *"I need to optimize your work logic first"*), the Agent was instantly paralyzed, firing off multiple clarification popups begging for context.

Without that round-the-clock babysitting through handcrafted prompts, an Agent's business reliability plummets immediately.

### 2. The Clash Between Local Privileges and Environmental Isolation
Why did those demos appear so capable? Because they ran inside a privileged local desktop environment:
- Reading and writing user `.xlsx`, `.docx`, and `.pptx` files on the local filesystem;
- Spawning a local Python runtime to process numbers and generate self-contained dashboards on the fly;
- Previewing artifacts directly on the host machine.

Yet in engineering reality, this setup is exceedingly fragile: environmental pollution on the host (such as user-defined Python variables) can instantly cripple built-in Skill execution; the moment an ad-hoc test attempts to write outside the workspace, the sandbox blocks the operation with errors; not to mention the frontend cheerfully marking a scheduled job as "Created Successfully" without verifying whether the external messaging channel actually connects.

Real-world business data lives on local disks and internal networks. Trying to lift this into a multi-tenant cloud SaaS immediately runs into hard brick walls around network isolation, environment compatibility, file permissions, privacy compliance, and cross-system authentication.

### 3. "Vanity Engineering" vs. Core Business Value
Commands like *"Switch to a tech-blue color scheme"*, *"Self-contained inline SVG without external dependencies"*, and *"Change to a tech-blue background view"* appeared repeatedly throughout the logs.

Simply to make the visual presentation pop during demos, the Agent had to re-read original files, generate Python code for style replacement, re-verify string integrity, and write out new files.
A single re-theming run pushed context to **138,000 tokens** (137k+ input tokens for a few hundred output tokens). Thanks to our harness engineering and robust prompt caching, cache hit rates reliably reach 99%+, which keeps actual inference latency and token costs well under control. But the fundamental contradiction remains: the underlying business logic didn't change at all, yet system bandwidth and runtime machinery were heavily consumed just making things look polished.

---

## 2. Why "Stuffing Everything into an Agent Makes a SaaS" Is a Castle in the Air

Traditional software architecture and the so-called "pure Agent architecture" represent fundamentally conflicting paradigms:

{{< mermaid >}}
flowchart TD
    subgraph SaaS["Traditional SaaS (Deterministic Core)"]
        DB[(Relational DB / ACID)] --> Core[State Machine & Rule Engine]
        Core --> Auth[RBAC & Audit Trails]
        Auth --> UI[Standardized UI]
    end

    subgraph AgentTrap["Fancied Agent SaaS (Probabilistic Black Box)"]
        Prompt[Vague Prompt] --> LLM{LLM Inference}
        LLM -.->|Probabilistic Judgment| Script[Ad-hoc Python / Tool Scripts]
        Script -.->|Drifting Output| Out[Unpredictable Drafts]
    end
{{< /mermaid >}}

### 1. Dumping Deterministic Business Rules onto an LLM to Guess Is Pure Laziness
The hardest and most tedious part of building enterprise software has always been nailing down every business rule and state transition:
- Transferring money from account A to account B requires double-entry bookkeeping, transactional integrity checks, and audit logging;
- Approval matrices bind rigidly to organizational hierarchies; thresholds require explicit sign-off from designated roles.

Those trying to shortcut their way to an "Agent SaaS" are simply trying to skip the hard work, hoping the LLM will just guess what to do next based on conversation context.
However, LLMs are fundamentally **probabilistic engines**. A system that requires hundreds of words in a prompt just to prevent it from hallucinating whether money will arrive next Wednesday cannot provide basic ACID guarantees or data consistency. Building on quicksand guarantees structural failure regardless of how many layers are piled on top.

### 2. Confusing an "Operator" with the "System Core"
An Agent's true strength is acting as an **adaptable operator**:
- Extracting signal from messy emails and unstructured spreadsheets;
- Merging intermediate data across two mismatched schemas into a coherent draft;
- Adjusting a report's presentation theme upon request.

An operator is not the operating system. An executive assistant who types fast and files folders efficiently does not replace an enterprise ERP platform.
Claiming that a chat box driving a handful of CLI tools constitutes a full SaaS without underlying database schemas, permission engines, or immutable audit logs is mistaking the surface skin for the skeleton.

### 3. The Structural Contradiction in Unit Economics and Liability
Teams attempting to package Agents as SaaS face an unavoidable economic dilemma:

| Dimension | Traditional SaaS | Fancied Agent SaaS |
| :--- | :--- | :--- |
| **Marginal Cost** | Near zero (fixed infrastructure, milliseconds per request) | Extremely high (tens to hundreds of thousands of tokens per run) |
| **Billing & Predictability** | Predictable seat-based or annual subscription | Wildly fluctuating compute sink; users fear token billing, vendors bleed on flat fees |
| **Liability Boundary** | Deterministic execution; platform guarantees audit trails and state changes | "For reference only; does not assume legal liability; please verify manually" |
| **Final Deliverable** | Actual business state mutation (ledger updated, contract executed, order dispatched) | Analysis, recommendations, drafts, or preview files (Draft / Preview) |

A glance at real-world Agent constraint policies reveals an uncompromising disclaimer at the bottom:
> *"Unless explicit authorization and confirmation exist, all actions must halt at draft/preview: no executing payments, no formal write-offs, no signing contracts on behalf of the company..."*

When an application cannot close the loop on risk, cannot be granted autonomous decision-making power, and requires line-by-line human verification for every output, it cannot realistically function as an autonomous, unattended enterprise SaaS.

---

## 3. Conclusion: Drop the Omnipotence Fantasy and Return to Tooling Fundamentals

Adding to the irony was the reality of the demo itself: after countless hours spent staging scenarios, hand-tuning prompts, and obsessing over presentation styling, the planned 30-minute session was squeezed by various delays and hiccups into a rushed 10-minute sprint, ending in a frantic, unceremonious wrap-up.

No matter how elaborately you stage the theater or how thick you pad the prompts, the messiness of the real world will always deflate unwarranted expectations.

Believing that an Agent wrapper lets you bypass business complexity and effortlessly monetize a SaaS is merely a speculative hangover of the current AI hype cycle.

This does not mean Agents lack utility. On the contrary, stripping away the grandiose delusion of "replacing all legacy enterprise software" makes their true value evident:
- Instead of replacing databases and deterministic engines, Agents serve as an **efficient cognitive bridge between humans and complex systems**;
- They excel as **desktop copilot utilities**, sitting directly in the user's local workspace to clean dirty data, draft intermediate documents, and perform exploratory analysis;
- Let deterministic code and relational databases handle state, and let Agents handle flexible language understanding and ad-hoc orchestration.

Acknowledging model boundaries and tackling the unglamorous work of data modeling and infrastructure engineering is far more credible than pretending an Agent shell will magically reinvent enterprise software.
