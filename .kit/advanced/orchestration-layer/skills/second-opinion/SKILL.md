---
name: second-opinion
description: "Cross-check the agent's own answer with independent reviewers before bringing it to the user. Use when the user says 'second opinion', 'sanity check', 'cross-check', 'am I missing something', 'stress-test', 'devil's advocate', 'run a full review', 'this is important', 'high-stakes', 'help me choose between', 'critique this', or similar. Three review styles: Devil's Advocate (single critique), Boardroom Debate (parallel multi-reviewer validation), Round-Table (multi-round brainstorm for choosing between paths). Not for factual lookups — use WebSearch for those."
---

# Second Opinion — cross-check before you commit

Stress-test your own answer with reviewers who don't share your framing. The reviewer set
depends on what you have available:

- **Always available:** the isolated `idea-validator` agent (same model family, but NO parent
  context — it can't anchor on your framing, and it READS the actual files).
- **If you have access to a second model family** (Gemini, GPT, …, via a CLI wrapper or API):
  add it as an external reviewer. A different training distribution catches different blind
  spots. It reviews from the brief only (no repo access) — lean on it for concept and
  tech-currency, not file-level facts.

## When to invoke

1. Two or more viable paths to choose between → Round-Table.
2. High-stakes decision (architecture, launch copy, anything with real rollback cost) →
   Boardroom Debate.
3. Stuck on the same problem after 2+ attempts, or a non-trivial proposal awaiting approval →
   Devil's Advocate.

If none fires, don't invoke — a single-model answer is enough for routine work.
Out of scope: factual lookups ("what's the latest X") — that's WebSearch, not review.

## Own thinking first (load-bearing)

Before ANY review style: do your own research, form your own proposal with rationale and
trade-offs, show it to the user. Only then invoke reviewers to critique it. Asking a reviewer
before forming your own position turns it into a seed for the decision instead of a validator —
and a reviewer without your codebase context can confidently seed something wrong.

## The three styles

### 1. Devil's Advocate (single critique)
Spawn `idea-validator` with a self-contained artifact (the design/decision/plan pasted inline,
plus the file paths it should actually read). Or send the same artifact to your external model
if the claim is about tech or the outside world.

### 2. Boardroom Debate (parallel validation — the headline pattern)
1. Write ONE self-contained artifact. Paste content inline — never rely on file references a
   brief-only reviewer might silently fail to load.
2. Launch ALL reviewers in the SAME message (parallel calls). Sequential calls destroy
   independence — a later reviewer sees the earlier one's framing.
3. Build an acceptance ledger: | Concern | Reviewer A | Reviewer B | My evaluation | Action |
4. **Adjudicate, never count votes.** All agreeing can share a blind spot; one dissenter with a
   file:line beats abstract agreement. A code-reading reviewer outranks a brief-only one on
   facts about the code.
5. Present the ledger critically: where you accept, where you push back, and why. You make the
   final call — reviewer output is INPUT, not the decision.

### 3. Round-Table (choosing between paths)
Diverge → deepen → converge, with a mandatory user check-in before convergence:
ground the facts (web-check) → generate/challenge options broadly → kill weak ones down to 2-3
with concrete arguments → **present survivors to the user, ask for preference** → converge on
one primary + a kill list → fact-check the final claims → synthesize.

## Critical evaluation rule

After every reviewer call: challenge each recommendation (fact or speculation?), check for
missing context the reviewer couldn't see, verify numbers (predictions are not measurements),
and present a table — reviewer said / my evaluation / action.

Anti-patterns: forwarding reviewer output as-is · accepting everything · treating reviewer
confidence as correctness · running reviews for trivial/stylistic choices · sequential
"parallel" calls.
