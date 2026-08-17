# The seven lenses — briefs

Each brief is written to be pasted verbatim into a subagent prompt (lenses 2-6) or followed
inline (1, 4, 7). Every lens obeys three shared rules:

- **Evidence or nothing.** A finding carries `path:line` or a command + its output. No evidence → label it `гипотеза` and name the check that would settle it.
- **н/п is a valid answer.** If the layer doesn't exist in this repo, say so in one line and stop. Do not invent a layer that should exist — that belongs to lens 6.
- **Raw facts, not architecture.** Lenses 2-6 report what IS. Recommendations are the integrator's job (lens 7 and step 4 of the skill are where "should" lives).

---

## Lens 1 — Delivery reality (integrator runs this)

**Question:** does the system's claimed state match reality?

- Take the project's own state documents (backlog, roadmap, handoff, README, "current state" header) and verify a sample of their claims **against disk, git and, where it exists, the running thing**. Prefer the load-bearing claims: "done", "deployed", "live", "tested".
- Count `✅ done · ⏳ in progress · 🚧 blocked`, and for every ⏳ older than ~2 weeks ask: still real, or quietly abandoned?
- **The blocker inventory:** every item blocked on someone else (client, key rotation, an approval) with the date it was last touched. Anything older than ~7 days about the outside world is a hypothesis — re-check before acting.
- Red flags: a "done" whose artifact isn't on disk · a handoff pointing to a file that moved · a task marked in progress with no commits touching it.

**Output:** a table `claim · where claimed · verified how · verdict`.

---

## Lens 2 — Knowledge layer (docs / SSOTs / concepts)

**Question:** is the knowledge layer telling one coherent, current story?

- **Frontmatter/lifecycle coverage:** which non-trivial docs lack status / authority / last_verified (or the project's equivalent)? Report the ratio and the worst offenders, not a full list.
- **Drift:** pick the load-bearing facts (a price, a schema, a model id, a deadline, a decision, a path, a count) and grep each across all docs. Report **every fact restated in >1 place** with which copies disagree, and which copy is the SSOT.
- **Contradictions between SSOTs:** two docs both claiming authority over the same fact with different values.
- **Derivable numbers stated as live values** (test counts, LOC, file counts) — these rot by construction.
- **Staleness:** docs whose `last_verified` (or last commit) is old relative to the code they describe; docs describing a thing that no longer exists.
- **Reachability:** a doc nothing links to and no rule points at is functionally invisible — flag it (it feeds lens 7).

**Output:** `fact · homes (paths:lines) · values found · which is authoritative · verdict`.

---

## Lens 3 — Operational layer (rules / agents / memory / loops)

**Question:** is the machinery internally coherent — and does it describe a loop that can actually close?

- **Rules:** each one — is it a mechanical always/never (good) or vague advice (weak)? Does it contradict another rule or the main instruction file? Is its scope (`paths:`) accurate? Does it have the required metadata?
- **Agents/subagent definitions:** is each one's trigger description distinct enough to route correctly? Do two agents overlap so much that the orchestrator can't choose? Is the model tier per agent consistent with the project's model policy?
- **Memory:** caps respected? entries date-tagged? header = current state, not a stacked chronicle? any fact in memory that belongs in a deeper home (and vice versa)?
- **The self-improvement loops** (findings registry → promotion → drop; decisions ledger; session handoffs): trace ONE example end to end. Does a finding logged N sessions ago actually reach a rule or a check? If the loop has never completed a full cycle, that's the finding — mark it 🟡 не проверено, not 🔴.
- **Hooks / automation:** defined vs actually firing (the collector's telemetry section gives the raw data).

**Output:** per artefact — `path · purpose in one line · coherent? · contradiction/gap found`.

---

## Lens 4 — Layer telemetry: did it ever fire? (integrator runs this)

**Question:** which parts of the system are load-bearing and which are decoration?

This is the lens that prevents an agent system from becoming an unread constitution.

- Read the collector's telemetry table: per rule / skill / agent / hook / script — last mention in session transcripts, last git touch, number of distinct dates it appears.
- Classify each: **hot** (fired in the last few sessions) · **warm** (fired, but a while ago — is its trigger seasonal?) · **cold** (defined, never observed firing).
- For anything cold, distinguish honestly:
  - *never triggered because the situation never arose* → keep, note the trigger to watch for;
  - *never triggered because the trigger is unreachable / misworded* → 🔴 broken, fix the trigger;
  - *never triggered because nobody needs it* → 🗑 delete candidate (lens 7).
- Same test for **process**: a ritual step, a template section, a required field that is always empty — that's a cold layer too.
- Caveat to state in the report: transcript grep undercounts (a rule can shape behaviour without being named). Treat cold as a *question*, not a conviction — that's why the classification above exists.

**Output:** the hot/warm/cold table + the honest classification for each cold entry.

---

## Lens 5 — Tools & infra

**Question:** can this be reproduced, restored and safely handed over?

- **Reproducibility:** are dependencies pinned? is there ONE documented command to run each tool? does a fresh clone work, or is there undocumented local state (a path, an env var, an installed binary, a logged-in browser profile)?
- **Secrets:** anything committed (gitleaks / grep for key shapes) · `.env` tracked or ignored · keys pasted into docs, transcripts or fixtures · key rotation debt (a key known to be exposed and not yet rotated).
- **Backup AND restore:** a backup that has never been restored is 🟡 не проверено, not a backup. Check: what's covered, where it lands, encryption, retention, and whether a restore has ever been exercised.
- **External state ownership:** what lives outside the repo (cron jobs, cloud scripts, deployed automations, third-party dashboards) — who owns it, how would we know it broke, and is that monitoring itself alive?
- **PII / sensitive material:** is it in git? should it be? if it was purged, is it purged from history too?
- **Tests / gates:** do they run green right now — you run them, not the docs' claim.

**Output:** per tool/infra item — `what · how to run it · reproducible? · secret exposure · monitored?`.

---

## Lens 6 — Domain gaps (what a system of this class should have)

**Question:** what's structurally missing, compared to a professional system doing this kind of work?

Name the domain first (from the user, or infer it from the repo). Use the matching gap-map;
if none fits, derive one: *what does this system produce → what does a professional producer of
that need at each stage: intake, production, quality, distribution, measurement, risk?*

- **Client/consulting delivery:** intake & scoping records · estimate-vs-actual tracking · a reusable proposal/offer pipeline · decision + change-request log · acceptance criteria per deliverable · invoicing/handover artifacts · post-mortems that feed the next estimate · liability/legal position stated · client-data handling (PII, DPA, key ownership).
- **Publishing / content site:** SEO & structured data · AIEO (how machines cite you) · content calendar & refresh cadence · distribution channels · analytics with an owner and a review cadence · accessibility · legal (licences, imprint, privacy) · security (deps, forms, headers) · performance budget.
- **Software product:** CI gates · test strategy across levels · release/rollback path · observability & alerting with an owner · dependency & vulnerability policy · onboarding docs · ADRs for one-way doors.
- **Automation / ops:** failure alerting (incl. dead-man switch) · idempotency & retry semantics · rate-limit and quota handling · a documented manual fallback · credential ownership & rotation · runbook.
- **Research / knowledge work:** source provenance · reproducible notebooks/data · a distillation path from raw to reusable · a claim-verification standard.

For each gap: is it *actually* needed at this system's current scale? A missing thing that would
cost more than it saves is **not a gap** — say so explicitly. Rank by `pain avoided / cost`.

**Output:** `gap · why it matters here (concrete) · cheapest first step · needed now or later?`.

---

## Lens 7 — Anti-bloat / subtraction (integrator runs this; quota is mandatory)

**Question:** what would this system be better off without?

Sources: lens 4's cold list, lens 2's duplicate homes, lens 3's vague rules, plus your own read.
Candidate classes:

- **Never fired** — a rule, skill, agent, hook or script with no observed use and no plausible near-future trigger.
- **Duplicated** — the same fact/instruction in two layers; keep the enforceable one, point the other at it.
- **Ceremony without a consumer** — a template section, a field, a report nobody reads or acts on.
- **Premature generality** — abstraction, config, or a pipeline built for a scale that hasn't arrived. The tell: one caller, ever.
- **Zombie state** — closed experiments, dead branches/worktrees, superseded docs still in the reading path, archived-but-not-labelled files.
- **Instruction overload** — an instruction file so long that its own rules compete for attention. If everything is a rule, nothing is.

For each: `what · evidence it's dead · what it costs to keep (attention, tokens, drift surface) · what breaks if removed · removal = delete | merge | label as historical`.

**Quota:** at least 3 candidates, or an explicit, evidence-backed statement that the system is
lean. Deleting a shared rule/doc layer needs the user's yes; archiving with a label is the safe
middle path.
