---
paths: ["src/**/*"]        # scope it, or delete this line to load the rule in EVERY session
created: YYYY-MM-DD
last-reviewed: YYYY-MM-DD   # bump when you re-verify the rule still holds, not when you edit it
---

# <rule name>

**Always / never:** one imperative sentence. If you cannot state it as a check someone could
run (grep, linter, gate), it is judgement, not a rule — write it as a
`knowledge/concepts/<topic>.md` article instead.

**Why:** one sentence, ideally naming the incident that produced it.

**Check:** the mechanical verification, e.g. `grep -rn "<forbidden>" src/` must return 0. If
none exists yet, write "informal — agent self-checks" and treat that as debt.

<!--
Keep a rule under ~25 lines. Rules WITHOUT a `paths:` field load into context at every session
start, at the same priority as CLAUDE.md — that is the whole cost model. Review history belongs
in git, related links belong in the concept article, and the rationale belongs in the handoff
that produced the rule. A rules directory that grows prose is how a memory system quietly gets
expensive. (The v5 template was 40+ lines of scaffolding and taught exactly that habit.)
-->
