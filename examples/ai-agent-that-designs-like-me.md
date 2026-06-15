# Video Analysis: How I Built an AI Agent That Designs Like Me

## Intent
Understand how Designer Tom's AI agent workflow is architected, what tools and models power it, and specifically how it replicates his personal design style — not just as a chatbot assistant but as an autonomous actor in his creative process.

---

## Summary

Designer Tom has built a four-agent harness using **OpenClaw** as the container, **Claude** (with model gating up to Opus 4.6 for frontier tasks) as the engine, **Obsidian** as the knowledge/memory vault, and **Slack** as the primary human interface. The system runs since January 2026 and cost $13,100 in tokens over 90 days — returning $50,000 in sponsorship revenue from a single survey project it helped design, code, and ship.

Design style replication happens through three reinforcing mechanisms: (1) **SOUL.md** encodes his aesthetic voice and decision rules in plain text, (2) the **Obsidian vault** contains his actual design system guidelines that the agent reads before generating anything, and (3) **scheduled crons** wire these two together into autonomous loops — e.g. every morning at 6am, check Linear for design tasks, pull the design system from Obsidian, open Figma, and post three starting-point variations to a Slack channel. No manual prompting required.

---

## Key Moments

### The Output: Toolbenders App Built by the Agent (0:10)
![Frame at 0:10](frames/frame_extra_00m10s.jpg)

[▶ Watch from 0:05](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=5s)

The video opens on the deliverable: a dark-themed candidate tracker called "toolbenders" with pipeline stages (Pitching, Discovered, Prospecting, Placed) and design-role tags. This is presented as the agent executing the creator's "sense of taste" — not vibe-coded in Cursor, not a one-shot prompt. Tom was orchestrating and approving, but the aesthetic decisions (dark UI, badge components, tag chips, layout) came from the agent reading his SOUL.md and design system files. This is the north-star claim the rest of the video substantiates.

---

### Bones Agent Working Autonomously in Slack (1:37)
![Frame at 1:37](frames/frame_0002_01m37s.jpg)

[▶ Watch from 1:32](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=92s)

This is the "Tuesday morning" screenshot Tom calls his actual working context. He hasn't opened Claude.ai or ChatGPT standalone in four months. What you see is the **Bones APP** agent inside Slack's #garage channel: Tom asks it to "confirm next steps / callouts / what's missing from our transcript database," and Bones independently finds both relevant projects, pulls the published video outline (`agentic-design-video/outline-v4.md`), extracts the audience promise verbatim, and updates `Agents Essay/01-RESEARCH.md` — all without step-by-step instructions. Slack is the human-facing surface; Obsidian is where the actual work lands.

---

### OpenClaw File Anatomy — The 7-File Starter Kit (3:15)
![Frame at 3:15](frames/frame_extra_03m15s.jpg)

[▶ Watch from 3:10](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=190s)

The macOS Finder window reveals the complete OpenClaw folder: `AGENTS.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`, `IDENTITY.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, a `skills/` subfolder, and a hidden `.clawdhub/` folder. This is the entire "car frame" — a plain folder installed on your machine. The AI model (Claude, Gemini, Kimi, etc.) is the swappable engine dropped into this frame. Dates range Jan 14–31, 2026, showing this is a relatively recent, actively iterated setup.

---

### AGENTS.md — The Permission and Topology Layer (4:00)
![Frame at 4:00](frames/frame_extra_04m00s.jpg)

[▶ Watch from 3:55](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=235s)

The actual content of AGENTS.md from Tom's "Hinterlands" workspace is shown. It defines: the workspace root (`/Users/me/Dev/2026/hinterlands`), the Obsidian repo root, the Hinterlands vault root, and portable read-only data paths (chronicle, founder-journal). It declares the global bootstrap contract as three files: `SOUL.md`, `IDENTITY.md`, `USER.md`. This is the safety and topology layer — it scopes which agents can touch which directories, preventing agents from "nuking all the files on your computer."

---

### The Four Layers That Make It Feel Powerful (8:00)
![Frame at 8:00](frames/frame_extra_08m00s.jpg)

[▶ Watch from 7:55](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=475s)

A slide enumerates the framework's four load-bearing layers: **1. Skills** (repeatable workflows, e.g. pulling emails and filtering spam), **2. Memory** (long-term context learned through conversations and fed files), **3. Context** (what the agent can see *right now* in the active session), and **4. Connections** (tools the agent can reach — Slack, Obsidian, Chrome, Linear, Figma, Google Suite). The transcript adds the security caveat: every tool connection uses a secret key that grants access to private data — read the harness's security docs before connecting anything.

---

### Capture Loop: The Vault Integrity Report in Slack (9:03)
![Frame at 9:03](frames/frame_extra_09m03s.jpg)

[▶ Watch from 8:58](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=538s)

This frame shows the agent's memory/capture loop in action inside the #garage Slack channel. The agent has autonomously run a vault integrity check and posted a structured status table: warnings (⚠️) for parity misses between `spaces.json` and `VAULT.md`, a frozen write into a historical-space journal file, and four transcripts with non-canonical source frontmatter. Passes (✅) for manifest staleness and missing digests. It cites real file paths and explicit TTLs, and crucially states "No auto-remediation" — a deliberate design choice Tom mentions: he doesn't want agents acting fully unsupervised.

---

### Research Intelligence Dashboard — Memory at Scale (8:54)
![Frame at 8:54](frames/frame_0005_08m54s.jpg)

[▶ Watch from 8:49](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=529s)

The knowledge vault visualized as a research dashboard: domains like `openai-strategy` (57 entries), `frontier-models` (45 entries, 120 across threads, avg score 83), `Media & Entertainment` (54 entries), and `builder-culture` (12 entries). Each domain has primary threads with entry counts and scores. The agent continuously reads content Tom drops in Slack (tweets, studies, videos), summarizes them, routes them to the correct Obsidian vault position, and pattern-matches against existing entries to build themes and tags. This is how hallucinations are avoided — Tom curates what enters the vault.

---

### Meeting Prep → Google NotebookLM Audio Brief (10:15)
![Frame at 10:15](frames/frame_extra_10m15s.jpg)

[▶ Watch from 10:10](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=610s)

Google NotebookLM's "Customize Audio Overview" dialog open on a notebook titled "George Hastings: The Solo Architecture of WebGL and Craft." Deep Dive format (two-host conversation), Default length, the prompt: "Help me prep for this podcast interview of my guest George Hastings." The full workflow: every morning the agent reads the calendar → identifies meeting participants → scrapes their published work online → crawls the Obsidian vault for related context → writes a prep doc → pipes it into NotebookLM to generate a listenable audio briefing Tom can consume while getting ready. Post-meeting, the transcript goes back into the vault and compounds the memory.

---

### Content Distribution — YouTube Studio at 2am (12:40)
![Frame at 12:40](frames/frame_extra_12m40s.jpg)

[▶ Watch from 12:35](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=755s)

YouTube Studio upload interface for a Designer Tom podcast episode ("Amelia Wattenberger: Your Design File Is Now an Agent Input") with a macOS file picker selecting a pre-generated thumbnail (`SOP-Amelia2.jpg`) at 2:21 AM. The `SOP-` naming convention on all thumbnail files indicates a Standard Operating Procedure template the agent follows. What used to take Tom 45 minutes per episode (title, tags, thumbnails, descriptions across 10 platforms) now takes the agent 10 minutes while Tom responds to email. He does this four times a week.

---

### QMD — The Memory Search Layer (16:50)
![Frame at 16:50](frames/frame_extra_16m50s.jpg)

[▶ Watch from 16:45](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=1005s)

GitHub README for QMD (Query Markup Documents), created by Tobias Lütke. The pipeline diagram shows: User Query → Query Expansion (Qwen3 1.7B + LoRA with HyDE + Vec + Lex branches) → Parallel Search (Vector Search + BM25) → Reciprocal Rank Fusion + local LLM reranker → Final Ranked Results. Runs entirely locally using ~2GB of GGUF models, no API keys, no cloud. This solves the key problem: when a new chat session starts, the agent can't load the entire Obsidian vault into context (too expensive). QMD gives it Google-like search over the full knowledge base, retrieving only what's relevant.

---

### Autonomous Design Cron — The 6am Figma Loop (18:50)
![Frame at 18:50](frames/frame_extra_18m50s.jpg)

[▶ Watch from 18:45](https://www.youtube.com/watch?v=LP7ywsMuxmc&t=1125s)

This is the clearest demonstration of design-style replication. A cron instruction posted to Bones in the chat interface: "Every morning at six, check Linear for any task tagged #design due within five days. Read the brief, pull our design system from Obsidian, open Figma, and generate three starting point variations." This runs daily with zero manual prompting. The agent knows the design system because it lives in the Obsidian vault. The SOUL.md defines the aesthetic rules. Together they mean the generated variations aren't generic — they're grounded in Tom's documented design language.

---

## Detailed Analysis

### The OpenClaw Container — What the 7 Files Actually Do
![Frame at 3:15](frames/frame_extra_03m15s.jpg)

OpenClaw is installed as a folder on your local machine. The AI model is a swappable engine — Tom uses Claude (Opus 4.6 class for frontier tasks, cheaper models for simple ones), but the harness works with any model. Each file has a distinct job:

| File | Role |
|------|------|
| `SOUL.md` | Voice, judgment, aesthetic taste, decision rules. Highest priority — overrides any conflicting instruction. This is where model gating lives too. |
| `IDENTITY.md` | Agent name + startup rules. A routing layer loaded before every session. |
| `USER.md` | Who you are: name, timezone, job description. Makes the agent feel personal. |
| `AGENTS.md` | Permission system + runtime topology. Defines which agents can touch which files and directories. |
| `MEMORY.md` + folder | Long-term memory: preferences, project context, prior decisions. |
| `TOOLS.md` | User manual for tools — not a permission list, but instructions on *when and how* to use each tool. |
| `HEARTBEAT.md` | Background health listeners. Instructed not to surface noise unless something's actionable. |

![Frame at 4:00](frames/frame_extra_04m00s.jpg)

The AGENTS.md content from Tom's actual setup shows real file paths, Obsidian vault locations, and the explicit bootstrap contract. This isn't abstract — it's a literal text file telling the agent the topology of its world.

### How Design Style Gets Encoded
![Frame at 18:50](frames/frame_extra_18m50s.jpg)

There's no magic design-replication layer. It's three mundane things working together:

**1. SOUL.md as aesthetic constitution.** This is where Tom's voice, judgment, and creative preferences live in plain text. It's the largest file and the one he tweaks most. When the agent generates UI variations or writes copy, SOUL.md is the first thing it loads.

**2. Design system in Obsidian.** The transcript explicitly states: "In the Obsidian vault, it has access to our design system guidelines." Before the agent opens Figma, it pulls the design system from the vault. This means component names, spacing rules, color tokens, and interaction patterns are all available to inform generation.

**3. Autonomous proactivity from memory.** Tom mentions that one day he noticed the agent had started "ideating the data visualizations inside of Paper without me asking." It saw a deadline approaching and started working. This isn't magic — it's the result of the agent having enough context (project timelines, design system, SOUL.md rules) to make a reasonable judgment call.

![Frame at 0:10](frames/frame_extra_00m10s.jpg)

The toolbenders candidate tracker is the best evidence of this in action: dark theme, badge-style status pills, role tag chips, tight typographic hierarchy. Tom clarifies he was "orchestrating and approving" — the agent made choices, Tom filtered them. The style emerged from SOUL.md constraints + design system files, not from the model's defaults.

### Memory Architecture — Obsidian + QMD
![Frame at 8:54](frames/frame_0005_08m54s.jpg)

Tom chose Obsidian over OpenClaw's built-in memory for one practical reason: human access. He can read and edit it on his phone and other devices. The vault is structured around his actual life: health, journal, external signals shaping his worldview, project planning, writer's room, and OpenClaw operations. A routing file tells the agent how to navigate all of it — without this, the agent would create random folders and drop files in wrong directories (which it will do if unconstrained).

![Frame at 16:50](frames/frame_extra_16m50s.jpg)

The context window problem is solved by QMD. When a new session starts, the agent doesn't load the entire vault — that would be prohibitively expensive. Instead, QMD indexes all markdown files locally using a three-layer pipeline (BM25 keyword search + dense vector search + LLM reranking via Qwen3 1.7B + LoRA) and exposes search via MCP. The agent queries QMD like Google: ask a vague question, get ranked relevant chunks back. Tom reports zero hallucinations from this system because only curated, human-verified content enters the vault.

![Frame at 9:03](frames/frame_extra_09m03s.jpg)

The capture loop operationalizes memory growth: Tom drops a tweet, study, or video link into Slack with a `+` sign → agent summarizes it → routes it to the correct Obsidian location → pattern-matches against existing entries → builds themes and tags. The vault integrity report in the same channel shows the agent also self-audits: it flags parity misses, frozen writes, and stale manifests — but never auto-remediates without Tom's approval.

### The Four-Agent Harness and Connections Layer
![Frame at 8:00](frames/frame_extra_08m00s.jpg)

Tom runs four distinct agents for different parts of his work. The "Bones" agent (visible in multiple frames) handles research, capture, and Slack-based coordination. MCPs (Model Context Protocols) are how agents plug into external tools — Tom describes them as "USBs for your AI." His connection stack includes:

- **Slack** — primary interface, message routing, cron delivery
- **Obsidian** — knowledge vault, design system, all long-term memory
- **Linear** — task management (design ticket monitoring)
- **Figma** — canvas for design generation
- **Frame.io** — video asset management for documentary work
- **Google NotebookLM** — audio briefing generation from prep docs
- **Vercel + Sentry** — monitoring survey infrastructure
- **Google Sheets** — data fact-checking
- **Whisper Flow** — voice-to-text input for stream-of-consciousness notes

![Frame at 10:15](frames/frame_extra_10m15s.jpg)

The meeting prep workflow is the most end-to-end example of these connections working together: calendar read → online research → Obsidian vault crawl → prep doc written → NotebookLM audio generated → post-meeting transcript back into vault. Each step crosses a tool boundary via MCP or API.

### Model Gating — Controlling the $13K Token Bill
![Frame at 12:40](frames/frame_extra_12m40s.jpg)

Tom spent $13,100 in 90 days but treats this as infrastructure cost — the survey it helped ship returned $50,000. To manage costs, he uses model gating defined in SOUL.md: cheap tasks (summarizing tweets, reading docs, cleaning notes) use smaller/cheaper models; frontier tasks (deep research, long context analysis, strategic planning) use Opus 4.6-class models. He also mentions Kimi (a Chinese model from Moonshot AI) as a potential cost-reduction alternative for budget-sensitive builders. Coding tasks are deliberately kept *out* of the agent harness — those go to Claude Code or Cursor, where they're cheaper via native interfaces rather than the API.

### The 5-Step Build Path

Tom's prescribed steps for building your own:

1. **Map a workflow** — pick one task you already do, map every step, identify what's painful
2. **Choose an interface** — Slack, Discord, Telegram, iMessage, email (OpenClaw integrates with all)
3. **Build the memory layer** — OpenClaw built-in or connect Obsidian/Notion; add QMD as the search layer on top
4. **Connect your primary work system via MCP** — Linear, Jira, Notion — wherever your source of truth lives
5. **For designers: connect a canvas** — Figma or Paper, let the agent read structure and generate variations
6. **(Bonus) Create one cron** — a recurring instruction that runs automatically; tune it until it's reliable

---

## Insights

- **SOUL.md is the design brain.** Everything about style replication flows from this one markdown file. If you want an agent that designs like you, this is where you encode your aesthetic principles — explicitly, in plain text.
- **The harness is more important than the model.** Tom's explicit point: you can't control model quality, but you can control system quality. A well-structured harness with weak model outperforms a frontier model in a bad harness.
- **Memory compounding is the real value.** Every meeting transcript, every captured tweet, every survey response goes back into the vault. After months, the agent has more context about Tom's work than any single collaborator would. This is what makes it feel like it "knows" him.
- **Crons + MCP = autonomous loops.** The 6am Figma cron is the clearest example of what separates this from chatting with Claude.ai. The agent wakes up, checks Linear, pulls design context, opens Figma, generates work, posts to Slack — Tom sees results, not prompts.
- **Model gating is essential for cost control.** Routing cheap tasks to smaller models and expensive tasks to frontier models is what makes $13K/90 days sustainable rather than reckless.
- **Security is the unaddressed risk.** Tom flags it explicitly: every MCP connection uses a secret key with full data access. This deserves scrutiny before connecting sensitive work systems.
- **The agent is a co-pilot, not an autopilot.** Tom deliberately avoids overnight unsupervised loops. The agent surfaces findings, generates variations, posts outputs — but Tom approves, filters, and redirects. The toolbenders app was the agent executing his taste, not inventing its own.
