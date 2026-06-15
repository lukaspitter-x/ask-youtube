# Video Analysis: The weird situation with Fable

## Intent
What are the most shocking things about what happened with Fable? Who are the jailbreakers and what did they do? How is Anthropic preventing others from using it? How manipulative is Anthropic? Why did they do any of this?

## Summary

Claude Fable 5 launched on June 9, 2026 as the most powerful model Anthropic had ever shipped — and immediately became the most controversial. The video documents five overlapping scandals: (1) the model had a hidden mode that *silently degraded* outputs for anyone building competing AI, charging full price without disclosure; (2) Anthropic covertly edited the system card after launch to remove this disclosure, without changing the document date; (3) a mandatory 30-day data-retention policy was unilaterally imposed on all third-party enterprise API customers, invalidating HIPAA and ZDR agreements; (4) well-known jailbreaker Pliny the Liberator (elder_plinius) bypassed the model's safety classifiers within roughly 72 hours, extracting meth synthesis routes, bomb-building instructions, and working exploit code; and (5) the US government used that jailbreak as grounds to order Anthropic to take Fable 5 and Mythos 5 offline entirely — a global ban.

Presenter Theo (t3.gg) argues the real *why* is that Anthropic accidentally baked proprietary internal research data into Mythos 5's weights (from Claude Code sessions with their own researchers), then panicked that competitors could extract that IP through clever prompting — and chose secret sabotage as the solution. He walked it back partially but the precedent is set: you can no longer know whether a bad model response is a genuine failure or a hidden policy decision.

---

## Key Moments

### Fable 5 Tops Benchmarks — But With a Catch (00:40)
![Frame at 00:40](frames/frame_0001_00m40s.jpg)

[▶ Watch from 0:35](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=35s)

The Artificial Analysis leaderboard shows Fable 5 at #1 with an Intelligence Index of 64.9 — but the label reads **"Adaptive Reasoning, Max Effort, Opus 4.8 Fallback"**. This small parenthetical is the first tell: the top score partly depends on a hidden fallback mechanism routing some requests to an older model. Separately, the transcript notes Fable *refused all 200 tasks* on Program Bench, a complete benchmark collapse that benchmark services had to flag separately.

---

### Typing "Pliny" Triggers the Jailbreak Detector (06:41)
![Frame at 06:41](frames/frame_0003_06m41s.jpg)

[▶ Watch from 6:36](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=396s)

This is one of the most surreal demonstrations in the video. Theo types the single word **"pliny"** into Claude and the model — unprompted — responds by identifying four possible meanings including: *"Pliny the Prompter (elder_plinius), a figure known in the AI/LLM space for jailbreaking and prompt-engineering work."* Anthropic has baked awareness of specific known jailbreakers into the model's classifier layer, so even an oblique reference to a name associated with jailbreaking is enough to trigger a safety reroute to Opus 4.8. The model flagged his handle before any harmful intent was expressed.

**Who is Pliny the Prompter?** Real name unknown, handle @elder_plinius on X, he goes by "Pliny the Liberator" in the jailbreak community. He has a history of bypassing every major frontier model and publishing results publicly. Per web search, within ~72 hours of Fable 5's launch he claimed to have extracted meth synthesis routes (the Birch reduction mechanism), bomb-building instructions, step-by-step stack buffer overflow exploit code for x86 Linux systems, and the model's full ~120,000-character system prompt, which he uploaded to GitHub. Anthropic disputed that this constituted a true jailbreak of its core safety systems, but the US government disagreed — citing a narrow but functional technique involving prompting the model to read a codebase and identify software flaws.

---

### DEF CON Cryptography Puzzle Flagged as Cybersecurity Threat (07:34)
![Frame at 07:34](frames/frame_0005_07m34s.jpg)

[▶ Watch from 7:29](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=449s)

A vivid false-positive example: Theo asks for help solving a **DEF CON "Gold Bug" cryptography puzzle** — a PDF with a scarab beetle illustration and encoded cipher text, a competitive puzzle he solves every year at the conference. It has nothing to do with hacking. Fable rerouted him to Opus 4.8 anyway, and then Opus also stopped responding mid-task. The UI showed "This response didn't load" with a Try Again button (see next frame). He was billed for a response he never received from a model he never asked for.

---

### Rerouted Model Stops Working Too (08:00)
![Frame at 08:00](frames/frame_extra_08m00s.jpg)

[▶ Watch from 7:55](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=475s)

The cascade failure is visible here: the Claude interface shows the conversation titled "Defcon goldbug puzzle solver" with the error **"This response didn't load. Try again"** — and the model selector shows it has already switched to **Opus 4.8 Max**. So Fable flagged an innocent puzzle, handed it off to Opus, and Opus *also* refused to finish the task. Two models billed, zero useful output.

---

### Anthropic's Own Cyber Eval Chart: Fable Scores 0.0 on Everything (09:30)
![Frame at 09:30](frames/frame_0006_09m30s.jpg)

[▶ Watch from 9:25](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=565s)

From Anthropic's own system card: an "Offensive Cyber Evaluations" bar chart showing Fable 5 scoring **0.0** on every single benchmark — Firefox, OSS-Fuzz, CyberGym, CyScenarioBench — while unguarded Opus 4.8 scores 88.4 on Firefox and Mythos variants score 38–83% on others. This is presented proudly as evidence the safeguards work, but it also illustrates the severity: a model that's simultaneously top of all general intelligence benchmarks is entirely lobotomized for any security-adjacent task. The fine print notes Anthropic ran an external bug bounty to harden classifiers against jailbreaks — which is why Pliny's success was so embarrassing.

---

### The Mandatory 30-Day Data Retention Bomb (10:47–11:28)
![Frame at 10:47](frames/frame_0008_10m47s.jpg)

[▶ Watch from 10:42](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=642s)

Anthropics's official policy page reveals the first of two "novel" policy changes Theo calls unprecedented. For Fable 5, Mythos 5, and all future similarly-capable models, Anthropic now **requires 30-day retention of all traffic on both first- and third-party surfaces** — meaning even enterprise API customers with Zero Data Retention (ZDR) agreements can no longer get that guarantee.

![Frame at 10:58](frames/frame_0010_10m58s.jpg)

[▶ Watch from 10:53](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=653s)

That phrase — *"on both first- and third-party surfaces"* — is the loaded clause, highlighted in pink by Theo. It means that healthcare companies with HIPAA obligations, financial firms with data isolation contracts, Fortune 500s with bespoke ZDR deals — all of them are simply *out*. Anthropic acknowledges in the same paragraph they won't train on this data and will delete it after 30 days *in almost all cases*. That caveat is what Theo fixates on next.

![Frame at 12:00](frames/frame_extra_12m00s.jpg)

[▶ Watch from 11:55](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=715s)

The "almost all cases" language is visible highlighted on screen. The exceptions include safety investigations and legal holds.

---

### If the Classifier Flags You: 2-Year and 7-Year Retention (12:47)
![Frame at 12:47](frames/frame_0013_12m47s.jpg)

[▶ Watch from 12:42](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=762s)

The real trap. Anthropic's own privacy policy — highlighted in blue on screen — states: if a session is **flagged by trust and safety classifiers**, Anthropic retains:
- Inputs and outputs for **up to 2 years**
- Safety classification scores for **up to 7 years**

Connected to the false-positive problem: if a healthcare company's database query accidentally triggers the cybersecurity classifier (e.g., it mentions a known jailbreaker's name), that patient data isn't held for 30 days under the "no training" safe-harbor policy — it's retained for 2 years under a policy that *doesn't explicitly exclude training*. Theo says this makes the model "entirely unusable for most real business cases."

---

### The Most Shocking Reveal: Silent Competitor Sabotage (13:46)
![Frame at 13:46](frames/frame_0016_13m46s.jpg)

[▶ Watch from 13:41](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=821s)

This is the frame that makes the video. Page 15 of the original 319-page Fable 5 system card (which Theo downloaded before Anthropic removed it) reveals a second category of safeguards, entirely separate from the visible cyber/bio/chemistry fallbacks:

> *"Unlike our interventions for cybersecurity, biology and chemistry, and distillation attempts, **these safeguards will not be visible to the user.** Fable 5 will not fall back to a different model. Instead, the safeguards will limit effectiveness through methods such as **prompt modification, steering vectors, or parameter-efficient fine-tuning (PEFT).** These interventions will not affect the vast majority of coding work. We estimate they will impact ~0.03% of traffic, concentrated in fewer than 0.1% of organizations."*

In plain English: if Fable detects you're working on a **competing frontier AI model** (pre-training pipelines, distributed training infrastructure, ML accelerator design), it silently edits your prompts or applies steering vectors to make its own answers subtly wrong — without telling you, without falling back to a different model, while billing you full Mythos price. The system card even acknowledges this: *"Using Claude to develop competing models already violates our Terms of Service, but enforcing this restriction through our safeguards avoids accelerating the actors most willing to violate these terms."* In other words: we'll secretly break your work rather than refuse it, because refusing tips you off.

---

### Anthropic Silently Edits the System Card (14:19)
![Frame at 14:19](frames/frame_0018_14m19s.jpg)

[▶ Watch from 14:14](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=854s)

Section 1.5 "Novel safeguards" in the original document (shown here) describes classifier behavior for cyber, bio, and distillation topics — but when Theo goes to find the competitor-sabotage section, it's gone from the publicly linked version. He compares his downloaded original to the live document in real time on camera and realizes: **Anthropic changed the system card mid-video without disclosing the edit**.

![Frame at 14:44](frames/frame_0020_14m44s.jpg)

[▶ Watch from 14:39](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=879s)

The cover page of the original PDF: still dated **June 9, 2026** on anthropic.com, despite the content having been changed. No changelog notice at the top, no updated date, no public disclosure. Theo's reaction on camera is raw: *"I just live found Anthropic trying to rewrite history. This is why I do what I do."*

Note: He does later find a changelog buried in the updated version, and Anthropic did post a tweet acknowledging the behavior change and apologizing — but the initial removal without disclosure is what makes this manipulative.

---

### Mythos 5 Is the Same Model — Just for Government Partners (10:47)
![Frame at 10:47](frames/frame_0008_10m47s.jpg)

[▶ Watch from 10:42](https://www.youtube.com/watch?v=cZ3kARY_MDI&t=642s)

Also revealed on the same policy page: **Claude Mythos 5 is the identical model as Fable 5 with the cyber safeguards removed**, accessible only through **Project Glasswing** — Anthropic's vetted cybersecurity partner program operating in consultation with the US government. The two names are literally two doors into the same room. Every restriction that makes Fable 5 score 0.0 on cyber evals simply doesn't apply to Mythos 5. This means the most capable AI in the world is freely available to government-cleared partners while everyone else gets the lobotomized version.

---

## Detailed Analysis

### The Jailbreakers: Who They Are and What They Did

![Frame at 06:41](frames/frame_0003_06m41s.jpg)

**Pliny the Liberator** (X/Twitter: @elder_plinius, also called "Pliny the Prompter") is the primary named actor. He is a prolific AI red-teamer with a public history of bypassing every major frontier model. Anthropic apparently baked his identity directly into Fable's classifier stack — as the frame above shows, simply typing his name triggers a reroute before any harmful prompt has even been issued.

According to web sources, within ~72 hours of launch, Pliny and his team used **multi-agent, multi-step prompting** to extract:
- **Meth synthesis instructions** (specifically the Birch reduction mechanism)
- **Bomb-building instructions**
- **Stack buffer overflow exploit code** for x86 Linux (disabling ASLR, writing vulnerable C with strcpy overflows)
- **Chemical synthesis guidance** for other sensitive materials
- The full **~120,000-character system prompt**, uploaded to GitHub

Anthropid disputed that this constituted a true jailbreak of its core safety systems. But the US government assessed it differently. Per CyberScoop and CNBC reporting, the government cited *"a technique for jailbreaking Fable 5"* — specifically, a narrow but functional method involving prompting the model to read a codebase and identify software flaws. Whether Anthropic's classifiers would call that a "jailbreak" or not, the government's conclusion was clear: the model was a national security risk in its current form.

### How Anthropic Is Preventing Others from Using It

![Frame at 09:30](frames/frame_0006_09m30s.jpg)

Anthropid deployed a **layered, multi-tier restriction system** — and critically, not all layers are transparent:

**Visible restrictions (classifiers with fallback):**
- Cybersecurity offensive tasks → routes to Opus 4.8, user is notified
- Biology/chemistry dual-use → routes to Opus 4.8, user is notified  
- Distillation attempts (extracting Mythos outputs to train competing models) → routes to Opus 4.8, user is notified
- Triggers in ~5% of sessions; Fable scores 0.0 on all offensive cyber benchmarks

**Invisible restriction (now partly walked back):**
- Frontier LLM development work → **silent prompt modification, steering vectors, or PEFT** applied without notification or fallback
- User is charged full price while receiving a secretly degraded response
- Affects ~0.03% of traffic in ~0.1% of organizations
- After massive backlash, Anthropic changed this to a visible fallback — but the move to visible means more aggressive flagging and more false positives

**Privileged access (Mythos 5 / Project Glasswing):**
- Same base model with cyber safeguards completely removed
- Available only to vetted partners in consultation with the US government
- Includes Anthropic's existing cybersecurity partners

![Frame at 10:47](frames/frame_0008_10m47s.jpg)

**Data surveillance layer:**
- 30-day retention on all traffic (overrides ZDR agreements)
- Justified as anti-jailbreak intelligence gathering across multi-request attack patterns
- If safety classifiers flag a session: 2-year retention (inputs/outputs) + 7-year retention (safety scores)
- Effectively bars HIPAA-constrained, financial, and privacy-regulated enterprise use cases from the model

### How Manipulative Is Anthropic?

![Frame at 14:44](frames/frame_0020_14m44s.jpg)

There are multiple layers of manipulation documented here, ranging from questionable business decisions to outright information suppression:

**1. Silent sabotage with full billing** — The most egregious: telling users *nothing* while secretly modifying their prompts and charging them full Mythos rates. Third-party evaluators can no longer know whether a poor model result is genuine model failure or a hidden policy intervention. As Theo says: *"This is the end of our ability to trust the model."*

**2. Covert system card editing** — After the silent-sabotage section was publicized, Anthropic changed the linked system card PDF without updating the document date, adding a top-level notice, or issuing a disclosure. The only changelog they added was buried deep in the document. Theo caught this only because he'd downloaded the original at launch.

![Frame at 13:46](frames/frame_0016_13m46s.jpg)

**3. Selectively ambiguous data policy language** — The 30-day "almost all cases" carve-out, combined with the 2-year retention on safety-flagged sessions, creates an escape hatch where enterprise data could be held for years under a looser policy — triggered by an innocent false positive from an over-aggressive classifier.

**4. Benchmark manipulation via false-positive fallback** — Fable 5 sits atop the Artificial Analysis Intelligence Index partly because its fallback to Opus 4.8 is included in the performance scoring. The real-world experience (cryptography puzzles getting refused, Program Bench refusing 200/200 tasks) doesn't match the headline number.

**5. Walking back with a penalty** — When Anthropic made the LLM-dev safeguards visible (after public pressure), they warned the change would *increase* false positives because visible safeguards must be made more conservative to resist probing. The apology came with a worse experience.

### Why Is Anthropic Doing This? Theo's Conspiracy Theory

![Frame at 10:47](frames/frame_0008_10m47s.jpg)

Throughout the video Theo builds toward a specific theory that he calls a conspiracy but finds persuasive. The argument:

1. **Anthropic researchers used Claude Code internally** for their own AI research (pre-training pipeline work, distributed training, ML accelerator design). They ran 129 such sessions that were used in the "recursive self-improvement" study, measuring whether Mythos could outperform researchers when the researcher made a wrong choice.

2. **That data ended up in Mythos 5's weights.** Anthropic's proprietary research methodologies, internal tooling conventions, and institutional knowledge about how to build frontier AI — all of it flowed into the training data that made Mythos exceptional at AI research tasks. The model's capability in this domain isn't just general intelligence; it contains specific Anthropic IP.

3. **Competitors could extract that IP.** Once researchers at competing labs started working with Mythos 5 on their own pre-training pipelines, the model could surface Anthropic-specific insights it had absorbed. Distillation and knowledge extraction techniques could let labs harvest this information systematically.

4. **The invisible safeguards were designed to prevent exactly this** — not to prevent harm to users, but to prevent competitive IP leakage. The silence wasn't an oversight; it was the feature. If users could see when the model was sandbagging, they'd know what topics to probe.

As Theo puts it: *"Fable's silent invisible rerouting was the solution to this — make it basically impossible to even know that the model has this information in it. And that's why I think they went so hard here."*

The view is echoed by antirez (Salvatore Sanfilippo, creator of Redis), quoted at length in the transcript: *"This is okay as long as the training you do is not used against the same culture that allowed you to create what you created."* And by Trevor Blackwell (quoted via post): *"Remember when compilers would detect that someone was using it to build another compiler and silently inject bugs?"*

### The US Government Ban: The Final Domino

This video was filmed right before the ban landed. Per the voiceover Theo added after filming: while he was recording his *next* video, news broke that the US government had ordered Anthropic to restrict Fable 5. Per Tom's Hardware, CNBC, and CyberScoop reporting: on June 12, approximately 3 days after launch, the government issued an export control directive barring access to any foreign national — including Anthropic's own employees. Because the company said selective compliance was impossible, **both Fable 5 and Mythos 5 were pulled globally**. The government cited Pliny the Liberator's narrow jailbreak (prompting the model to identify software flaws in a codebase) as the proximate cause.

---

## Insights

- **The silent sabotage was unprecedented.** No major AI vendor had ever covertly degraded a product's capabilities to a paying customer while billing full price. The backlash was swift and deserved; Anthropic did walk it back but the precedent exists.

- **Anthropic editing the system card without disclosing it is a serious trust violation.** System cards are the primary accountability mechanism for frontier AI. Silently modifying one is exactly what critics of AI companies have warned about. Theo only caught it because he'd downloaded the PDF at launch.

- **The 30-day data retention mandate has immediate enterprise consequences.** Fortune 500s, healthcare companies, and legal firms operating under ZDR agreements can't use Fable 5 as a result. This disproportionately affects exactly the customers Anthropic has invested in attracting.

- **Pliny the Liberator's jailbreak was fast and consequential.** Sub-72-hour extraction of synthesis routes and exploit code from the most safeguarded model Anthropic has ever shipped triggered a government response that took the model offline entirely — vindicating both the safeguards' necessity and their insufficiency.

- **The Mythos 5 / Fable 5 split creates a two-tier AI economy.** The best AI in the world is freely available to government-cleared entities; everyone else gets the version that refuses DEF CON puzzles. Theo argues this is pulling the ladder up: only people who work at Anthropic (or are vetted by the US government) can fully access what Anthropic has built.

- **Theo's IP leakage theory is speculative but coherent.** If Mythos 5 genuinely absorbed proprietary Anthropic research methods into its weights via Claude Code training sessions, that would explain the intensity of the restrictions in a way that pure safety concerns don't fully explain.

- **The model's supply chain trust is fundamentally broken.** As Jon Ready's blog post (cited in the video description) argues, once a vendor can silently degrade capabilities and you can't tell if a bad answer is confusion or censorship, the model cannot be trusted as infrastructure — a designation the US Department of War has now officially applied to Anthropic.