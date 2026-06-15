# Video Analysis: Anthropic Just Revealed The Best Claude Code Setup

## Intent
Produce a detailed guide on all parts mentioned in the video — cover every topic, tool, concept, and technique discussed, with enough depth to act as a standalone reference.

## Summary

This video is an AI Labs walkthrough of [Anthropic's official large-codebase best-practices blog post](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start). It goes well beyond a basic install guide: the core thesis is that **the harness you build around Claude Code matters more than the model itself** — and that harness has seven distinct components. The video covers each in sequence: how Claude navigates files (file-system traversal, not RAG), why you need a custom harness, how to structure `CLAUDE.md` at scale, hooks for enforced behavior and self-improvement, skills for on-demand context, plugins for team distribution, LSP for unconventional languages, custom MCPs for internal tooling, and sub-agents for parallelized work. It closes with five large-codebase hygiene practices.

Every section below maps directly to a chapter of the video with timestamps, supporting frames, and supplementary depth from Anthropic's own documentation.

---

## Key Moments

### Pre-flight checklist before a large task (00:19)
![Frame at 00:19](frames/frame_0001_00m19s.jpg)

[▶ Watch from 0:14](https://www.youtube.com/watch?v=lGalJmyI78w&t=14s)

Before Claude Code touches a large refactor (shown: auth refactor across 240k LOC / 1,847 files), the agent should complete a structured checklist: read `CLAUDE.md` for conventions, map module boundaries, locate existing patterns to mirror, and define the exact scope (14 files in this example). The UI shows **Plan Mode** active via `Shift+Tab`. This sets the tone for the whole video: never let the agent start blind.

---

### RAG vs file-system navigation (01:09)
![Frame at 01:09](frames/frame_0003_01m09s.jpg)

[▶ Watch from 1:04](https://www.youtube.com/watch?v=lGalJmyI78w&t=64s)

This animated diagram is the clearest visual explanation in the video. The old RAG-based approach embeds 18,742 files into a central database, runs embedding-based semantic search ("find rate limit handler"), and returns the nearest-neighbor files with similarity scores (0.74, 0.71, 0.69, 0.68). The central database is bordered in red to signal the failure mode: at scale, the embedding pipeline can't keep up with active teams — so it returns stale or hallucinated module references.

---

### Anthropic's official explanation of file-system traversal (01:23)
![Frame at 01:23](frames/frame_0004_01m23s.jpg)

[▶ Watch from 1:18](https://www.youtube.com/watch?v=lGalJmyI78w&t=78s)

The Anthropic blog post displayed here is the primary source for the whole video. Key quote: Claude Code *"traverses the file system, reads files, uses grep to find exactly what it needs, and follows references across the codebase"* — locally, with no index required. This is why bash tools don't pollute the context window with irrelevant snippets.

---

### CLAUDE.md — the first harness component (03:00)
![Frame at 03:00](frames/frame_extra_03m00s.jpg)

[▶ Watch from 2:55](https://www.youtube.com/watch?v=lGalJmyI78w&t=175s)

The Anthropic blog describes `CLAUDE.md` files as context files auto-loaded every session: root file for the big picture, subdirectory files for local conventions. The highlighted sentence — *"They give Claude the codebase knowledge it needs to do anything well"* — is the entire argument for investing time in this file. The blog also introduces hooks here as a self-improvement mechanism (not just guardrails).

---

### Stop hook — the self-improving reflect script (06:00)
![Frame at 06:00](frames/frame_extra_06m00s.jpg)

[▶ Watch from 5:55](https://www.youtube.com/watch?v=lGalJmyI78w&t=355s)

This is the most technically specific frame in the video. The file `.claude/hooks/reflect-on-session.sh` uses `jq` to build a JSON payload with `decision: "block"`, which forces Claude to pause before ending the session. The embedded prompt instructs Claude to scan for four categories of learnings and propose `CLAUDE.md` updates: (1) gotchas/surprises, (2) correct build/test/lint commands, (3) conventions from code review, (4) new top-level directories or modules.

---

### Skills — progressive disclosure concept (06:30)
![Frame at 06:30](frames/frame_extra_06m30s.jpg)

[▶ Watch from 6:25](https://www.youtube.com/watch?v=lGalJmyI78w&t=385s)

The Anthropic blog section on skills is quoted directly: skills use *"progressive disclosure"* — only the name and description (~100 tokens) load initially; the full skill content loads only when the task matches. A security-review skill loads for vulnerability assessments; a documentation skill loads when code changes need doc updates. Skills can be path-scoped to activate only in relevant directories.

---

### Plugin distribution — manual upload vs GitHub sync (08:00)
![Frame at 08:00](frames/frame_extra_08m00s.jpg)

[▶ Watch from 7:55](https://www.youtube.com/watch?v=lGalJmyI78w&t=475s)

The docs page shown explains the two distribution methods for plugins (Team/Enterprise plans only): **Manual upload** — ZIP files via admin UI, best for quick iteration; **GitHub syncing** — connect a private repo so Cowork auto-syncs, best for multi-developer collaboration with version control. Both can run in parallel. Prerequisite: Cowork and Skills must be enabled org-wide.

---

### LSP with unconventional frameworks — Shopify/Remix example (09:12)
![Frame at 09:12](frames/frame_0006_09m12s.jpg)

[▶ Watch from 9:07](https://www.youtube.com/watch?v=lGalJmyI78w&t=547s)

The VS Code view shows a Shopify + Remix app with Prisma ORM — the video's running example of an "unconventional" stack. File conventions like `.server.ts`, `.server.tsx`, Shopify extensions, and Prisma singletons are non-obvious to an agent navigating purely by text pattern. Without LSP, Claude guesses at symbols. With LSP, it navigates via go-to-definition exactly as a human developer would.

---

### MCP servers and sub-agents — official blog (10:20)
![Frame at 10:20](frames/frame_extra_10m20s.jpg)

[▶ Watch from 10:15](https://www.youtube.com/watch?v=lGalJmyI78w&t=615s)

The blog page clearly states: *"MCP servers are how Claude connects to internal tools, data sources, and APIs that it can't otherwise reach."* The most sophisticated teams expose structured search as a callable tool. Then the subagents section begins immediately below: *"A subagent is an isolated Claude instance with its own context window that takes a task, does the work, and returns only the final result to the parent."*

---

### Sub-agents — official definition and exploration pattern (11:16)
![Frame at 11:16](frames/frame_0007_11m16s.jpg)

[▶ Watch from 11:11](https://www.youtube.com/watch?v=lGalJmyI78w&t=671s)

The blog highlights the canonical read-only exploration pattern: spin up a read-only subagent to map a subsystem and write findings to a file, then have the main agent edit with the full picture. This "split exploration from editing" pattern is the core reason subagents improve large-codebase quality — it prevents the main agent's context from getting polluted with exploratory noise.

---

## Detailed Analysis

### 1. How Agents Navigate Code: RAG vs File-System Traversal (00:32–01:45)

![Frame at 01:01](frames/frame_0002_01m01s.jpg)

The VS Code view of the "Helix" monorepo (pnpm + Turborepo, auth-service selected) is the backdrop for explaining how file-system navigation works in practice. Claude Code looks at the file tree the same way a developer would: start from `CLAUDE.md`, read the project structure, then drill into the relevant service folder.

![Frame at 01:09](frames/frame_0003_01m09s.jpg)

**RAG-based approach (deprecated):** Embeds the entire codebase into a central vector database. At query time, semantic search returns nearest-neighbor chunks by similarity score. Problem: embedding pipelines can't keep up with active teams — the database becomes stale. The agent then confidently references modules that no longer exist (hallucination).

![Frame at 01:23](frames/frame_0004_01m23s.jpg)

**File-system traversal (current standard):** Claude Code uses `ls`, `grep`, and bash tools to navigate exactly as a developer would. It reads only what it needs, follows import references, and never pre-loads a central index. Bash tools are efficient because they load only the exact snippet into context — no noise. As Anthropic confirms: *"It operates locally on the developer's machine and doesn't require a codebase index to be built, maintained, or uploaded to a server."*

> **Implication:** Nearly all modern coding agents (Claude Code, Codex, Gemini CLI) now use file-system traversal. The RAG debate is settled.

---

### 2. Why the Harness Matters More Than the Model (01:46–02:47)

![Frame at 01:48](frames/frame_extra_01m48s.jpg)

The video makes a strong architectural claim: the model's intelligence is a floor, not a ceiling. The harness — everything around the model that configures how it perceives, acts, and self-corrects — determines the ceiling. The GPT-5.2 comparison on screen underlines that this is model-agnostic: whether you use Claude, Codex, or Gemini CLI, a weak harness wastes model capability.

**The harness has five components (all configured environmentally):**
1. `CLAUDE.md` files
2. Hooks
3. Skills
4. Plugins
5. MCPs + Sub-agents

Open-source harnesses like **Superpowers** exist but won't scale for large bespoke codebases — you'll need to build your own.

---

### 3. CLAUDE.md — The Knowledge Base (02:48–04:18)

![Frame at 03:00](frames/frame_extra_03m00s.jpg)

`CLAUDE.md` is loaded at session start and persists in memory for the entire session. It is the agent's knowledge base for the codebase: conventions, architectural rules, dos and don'ts.

**Key rules for CLAUDE.md at scale:**

| Rule | Detail |
|---|---|
| **Length cap** | ~300 lines (root file). Longer = distraction. |
| **Scope** | Cross-cutting concerns only — nothing task-specific |
| **Monorepo** | Each subdirectory gets its own `CLAUDE.md`; agent loads progressively when entering that directory |
| **Maintenance cadence** | Update as the project evolves AND as models evolve |
| **Model-specific tuning** | Instructions for Claude 3.5 Sonnet may be redundant for Opus — newer models overcome old failure patterns natively |

**Progressive loading in monorepos:** The root `CLAUDE.md` loads at session start. Subdirectory `CLAUDE.md` files load only when Claude enters that directory. This means the agent isn't burdened with auth-service conventions when it's working in the billing-service.

**What belongs in CLAUDE.md:**
- Project conventions and style
- Module boundaries (what touches what)
- Non-negotiable hard rules
- Architecture overview
- Tech stack specifics

**What does NOT belong in CLAUDE.md:**
- Task-specific workflows (→ Skills)
- Tool-specific configurations (→ Hooks)
- Integration details for external systems (→ MCPs)

> ⚠️ `CLAUDE.md` is a living document. Anthropic's blog: *"Because they load in every session regardless of the task, keeping them focused on what applies broadly will prevent them from becoming a drag on performance."*

---

### 4. Hooks — Enforced Behavior and Self-Improvement (05:09–06:22)

![Frame at 06:00](frames/frame_extra_06m00s.jpg)

Hooks are shell scripts that execute at specific lifecycle events. They differ from `CLAUDE.md` instructions in a critical way: **instructions can be ignored or drift in Claude's attention span; hooks cannot be skipped.** They force behavior.

**Hook event types (from Anthropic docs):**

| Event | When it fires | Use case |
|---|---|---|
| `SessionStart` | Session opens | Load git state, inject context, initialize env |
| `PreToolUse` | Before any tool call | Block writes to protected files; validate inputs |
| `PostToolUse` | After any tool call | Run linter, run tests, log tool usage |
| `Stop` | After agent completes | Force reflection; update `CLAUDE.md` |
| `StopFailure` | After agent fails | Log error details; notify team |

**The Stop Hook / Self-Improvement Pattern:**

The most powerful hook shown in the video is `reflect-on-session.sh`. Using `jq`, it builds a JSON block with `decision: "block"` — this prevents Claude from ending the session until it has:

1. Scanned for **gotchas** (failures, surprises, non-obvious behavior)
2. Documented **correct build/test/lint commands** found during the session
3. Captured **conventions** that emerged from code review or corrections
4. Noted **new top-level directories or modules** that appeared

Claude then proposes `CLAUDE.md` updates while the context is fresh. This turns every session into a feedback loop — the harness improves itself.

**Exit code semantics:**
- Exit code `0` → continue normally
- Exit code `2` → block / force Claude to keep working (used in the stop hook)

**Pre-tool-use example:** Configure a hook on the `Edit` tool that checks if the target file path is in a protected list (e.g., `.env`, `secrets/`). If it is, exit `2` to block the edit.

---

### 5. Skills — On-Demand Context via Progressive Disclosure (06:23–07:24)

![Frame at 06:30](frames/frame_extra_06m30s.jpg)

Skills are `.md` files (and supporting files) that load into the agent's context only when the task calls for them. They use **progressive disclosure**: at session start, Claude sees only the skill's name and description (~100 tokens each). When a task matches a skill's description, Claude loads the full skill content (under 5,000 tokens). Supporting scripts load only if explicitly invoked.

**Why not just put everything in CLAUDE.md?**
A 1,000-line `CLAUDE.md` that includes security review workflows, deployment procedures, migration scripts, and documentation templates wastes tokens on every session — even sessions that never touch any of those areas. Skills solve this by keeping the right expertise *available* without making it *present* in every session.

**Path scoping:** Skills can be scoped to specific directory paths. A deployment skill scoped to `deploy/` will never activate when Claude is working in `src/components/`. This is implemented via glob matching against the files Claude has touched or is about to touch.

**How to create a skill:**
1. Invoke the built-in skill creator: `/skill create` (now native to Claude Code; previously required a GitHub download)
2. Answer the conversational prompts about what the skill should do
3. Restart the session — the skill is available

**Skill examples from the video:**
- Security review skill (loads during vulnerability assessment)
- Documentation update skill (loads when code changes need doc updates)
- Deployment skill (path-scoped to `deploy/`)

**Skill file structure:** Each skill is a folder containing a `SKILL.md` with YAML frontmatter (name, description, path globs) and markdown instructions. Supporting scripts and reference files live alongside it.

---

### 6. Plugins — Distributable Bundles for Teams (07:25–08:41)

![Frame at 08:00](frames/frame_extra_08m00s.jpg)

A **plugin** is a bundle of skills + hooks + MCPs packaged as a single installable unit. Where skills are per-developer configurations, plugins are the mechanism for distributing a fully configured harness across an entire team or organization.

**Why plugins matter for large codebases:**
Without plugins, every new team member must manually download and configure skills, hooks, and MCPs separately. With plugins, they run one command and get the identical context and configuration.

**Plugin distribution methods (Team/Enterprise plans):**

| Method | Best for |
|---|---|
| **Manual upload** | ZIP files via admin UI; quick iteration, one-off tools |
| **GitHub syncing** | Connect a private repo; Cowork auto-syncs; ideal for multi-developer collaboration |

Both can run in parallel (e.g., GitHub-synced core plugins + manual ad-hoc tools).

**Plugin commands:**
- Install: `/plugin install <name>`
- Browse marketplace: `/plugin marketplace`
- Add a custom marketplace: `/plugin marketplace add <url>`

**Built-in plugins from the official marketplace:**
- Front-end design
- Code review
- Code simplifier
- Playwright (testing)

**Prerequisite:** Cowork and Skills must both be enabled at the organization level before plugin marketplaces are accessible.

---

### 7. LSP — Language Server Protocol Integration (08:42–09:56)

![Frame at 09:12](frames/frame_0006_09m12s.jpg)

LSP gives Claude Code the same navigation intelligence a developer has in an IDE: go-to-definition, find-all-references, real-time diagnostics, type checking. Without LSP, Claude navigates by text pattern matching — fast but imprecise, especially for unconventional stacks.

**Why LSP matters for unconventional frameworks:**
The Shopify + Remix + Prisma example shown is a perfect case: `.server.ts` files, Shopify extension structure, and the Prisma singleton pattern are all non-standard. A text pattern search for a function name may return 5 files — LSP identifies the exact definition in 50ms instead of 45 seconds of bash traversal.

**Supported languages (as of 2026):** Python, TypeScript, Go, Rust, Java, C/C++, C#, PHP, Kotlin, Ruby, HTML/CSS — plus community LSPs for GDScript (Godot), BSL (1C:Enterprise), and others via the plugin marketplace.

**Setup:**
1. Set `ENABLE_LSP_TOOL=1` (environment variable)
2. Add the LSP plugin marketplace
3. Install the language plugin for your stack
4. Ensure the language server binary is available on `PATH`

**Key principle from the video:** Don't wait for errors before adding LSP. Configure it for every language in your stack *before* writing any code. Once installed, Claude automatically receives diagnostics (type errors, missing imports, syntax issues) as it edits.

> *"Instead of letting the agent guess patterns, installing LSP lets it read and edit code the way a developer thinks about it, not just as text."* — 09:54

---

### 8. Custom MCPs — Internal Tools, APIs, and Data Sources (09:57–11:03)

![Frame at 10:20](frames/frame_extra_10m20s.jpg)

MCP (Model Context Protocol) servers extend Claude's reach beyond what file-system access provides. Public MCPs connect to external services; **custom MCPs** connect to your project's internal systems that no external tool knows about.

**What custom MCPs can expose:**

| MCP type | Example |
|---|---|
| Documentation guide | Internal architecture docs, API reference |
| Analytics retrieval | Fetch metrics from internal dashboards |
| Ticketing integration | Create/update Jira, Linear, or GitHub issues |
| Code mutation | Make changes through the MCP rather than direct file edits |
| Structured search | Expose internal vector search as a callable tool |

**How MCPs work operationally:** An MCP server runs as a process (TypeScript via `createSdkMcpServer` or Python via `create_sdk_mcp_server`) and exposes tools Claude can call. Those tools appear in Claude's tool list alongside built-in tools.

**Critical sequencing rule from the video:**
> Set up your app first. Get the basic application working. Then build the MCP. Configuring MCP before the app is stable causes the MCP implementation itself to fail.

**Team distribution:** Custom MCPs can be bundled inside plugins so the entire team automatically gets access to internal tooling when they install the project plugin.

---

### 9. Sub-Agents — Isolated Context and Parallel Delegation (11:04–12:25)

![Frame at 11:16](frames/frame_0007_11m16s.jpg)

A sub-agent is an isolated Claude instance with its own context window, system prompt, and tool list. It receives a delegated task, does the work, and returns only the final result to the parent agent. The parent's context is never polluted with the sub-agent's exploratory noise.

**Why sub-agents matter at scale:**
- A 200k-token exploration of the auth subsystem doesn't need to live in the main agent's window
- Multiple sub-agents can run in parallel (as of April 2026, MCP connections also initialize in parallel)
- The main agent stays focused on orchestration; sub-agents handle execution

**The canonical exploration pattern (from Anthropic blog):**
1. Spin up a **read-only sub-agent** to map a subsystem
2. Sub-agent writes findings to a file
3. Main agent reads the file and edits with full context

**Configuration options:**
- Claude spins up sub-agents automatically when needed
- You can configure custom sub-agents with specific tools, models, and instructions
- You can **override built-in agents** (e.g., `explore`) with your own version that knows your project's directory structure

![Frame at 12:00](frames/frame_extra_12m00s.jpg)

**Overriding the built-in `explore` agent:** Claude's default `explore` agent is generalized for all codebases. A custom `explore` agent can describe how to navigate your specific directory tree (e.g., the Shopify app structure visible in the frame) — saving tokens and preventing wrong-path traversal.

**Parallelization:** Agent delegation enables parallel workstreams. Example: three sub-agents simultaneously investigating authentication, database, and API modules, then reporting back to the orchestrating parent.

**Key limitations:**
- Sub-agents cannot spawn their own sub-agents (no recursive delegation)
- Sub-agents don't see each other's work in real time — if Agent A's output changes what Agent B should do, you must wait for A and route manually

---

### 10. Large Codebase Best Practices (12:26–13:55)

![Frame at 00:19](frames/frame_0001_00m19s.jpg)

The closing section covers five hygiene rules that apply once the full harness is in place.

**1. Separate tests per subdirectory**
Don't centralize all tests in a root `tests/` folder. Per-subdirectory test folders:
- Keep tests co-located with the code they test
- Avoid timeout issues when running all tests at once
- Enable path-scoped execution (run only billing tests when working in billing)

**2. Build a codebase map for unconventional languages**
For conventional stacks (React, Next.js, standard Node), skip this — agents are trained extensively on them. For C++, Rust, GDScript, proprietary frameworks, or unusual monorepo layouts, create a dedicated codebase map file that acts as a table of contents: what file lives where, what module contains what. This replaces hundreds of bash `ls`/`grep` commands with a direct lookup.

**3. Use ignore files**
Two files control what the agent and version control can touch:
- `.gitignore` — standard; already in use
- `.agentignore` (or permissions in `.claude/settings.json`) — blocks Claude from reading/writing specific files. Put `.env`, secrets, and sensitive configs here. **Note:** `.claudeignore` is a hallucination that spread online — it does not exist. Use `.claude/settings.json` `denylist` for file access restrictions.

**4. Review the harness every few months**
Model improvements make old instructions redundant. What Sonnet 4.5 needed explicit instructions for, Opus handles natively. Bloated `CLAUDE.md` files with stale rules waste tokens and degrade performance. Remove hooks, instructions, and skills that newer models no longer need.

**5. Plan Mode before large tasks**
As shown in the opening frame (00:19), activate Plan Mode (`Shift+Tab`) before starting any large task. Complete the preflight: read `CLAUDE.md`, map module boundaries, locate the existing pattern, define the exact file scope. Never let the agent start blind.

---

## Insights

- **The harness is the product.** The model is the engine; the harness is the vehicle. A weak harness on a strong model still produces bad code at scale.
- **CLAUDE.md is not a one-time artifact.** It should evolve with the project AND with each new model release. Stale instructions waste tokens and can actively mislead newer, more capable models.
- **The stop hook is the highest-ROI investment.** Making Claude reflect at session end and propose CLAUDE.md updates turns every coding session into a self-improvement loop — the harness gets smarter automatically.
- **Skills > CLAUDE.md bloat.** If you're tempted to add something to `CLAUDE.md`, ask: "Does every session need this?" If not, it's a skill. Path-scoped skills are especially powerful in monorepos.
- **LSP is not optional for unconventional stacks.** If you're using Remix, Shopify Liquid, GDScript, C++, or any non-mainstream framework, set up LSP before writing the first line of code — not after the agent starts making symbol errors.
- **Sub-agents solve the context pollution problem.** The classic mistake is running a 200k-token codebase exploration in the main agent's window. Use a read-only sub-agent to explore → write findings to file → main agent edits.
- **Plugins are team infrastructure.** For any team larger than one person, a plugin bundling skills + hooks + MCPs is the difference between consistent AI-assisted development and each developer having a different, incompatible setup.
- **MCP sequencing matters.** Build the app first. Wire the MCP second. Configuring MCP for a half-built app creates circular debugging hell.
- **Test co-location prevents scale failure.** A single root `tests/` directory creates timeout and scoping problems as the codebase grows. Separate test directories per subdirectory are a prerequisite for reliable CI at scale.
- **Review and prune quarterly.** Set a calendar reminder to audit the harness every few months. Remove what the latest model no longer needs. Smaller, sharper context always beats larger, stale context.