---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Rules subtraction — make an instruction set shorter and consistent without losing an obligation

> Read on demand. Lens 7 of `/memory-kit:system-audit` finds what to cut; this is the procedure for cutting rule TEXT
> safely — the same obligations, fewer lines, one home per directive.

**Applies when:** your always-loaded instructions (`CLAUDE.md`, `.claude/rules/`, process docs a session must follow)
grew by one line per incident for months, or a newer model is about to read them.

## Why — a literal reader

A model that smooths contradictions forgives a messy rule set; one that applies lines as written stalls between two
rules, asks for approvals a rule already gives, or applies an absolute far past the case it was written for. Vendor
prompt guidance for a newer model (checked 2026-11-11 in one project): «rewrite absolute rules so that they state their
scope and reason»; cautious instructions «build up wherever context carries over: memory, notes, instruction files,
and messages between agents»; approval rules «name the exact actions they cover».

What one project's audit found in its own set (measured in one project, 2026-11: 51 written obligations per work
block, 6 of them enforced by a script; 17 contradictions; 20 directives restated in 2–5 files). Capitals were rare —
tone was not the problem; nesting and superseded absolutes («all of them», «whatever the context size») were.

## Bars first

Write the bars and the fail branches before any rule text changes (`spec-depth.md` §4). The ones that worked:

- **One answer** — for every contradiction, the losing statement's wording has 0 hits in the scope, the winner one home.
- **Nothing lost** — every unit of the before-text has a destination row; no dropped row carries a decision the user
  made, unless it names the later decision that retired it.
- **Pointers resolve** — every numbered citation of a rule from live files and scripts still lands.
- **Gates unchanged** — every check script gives the same verdicts on its stored cases before and after.
- **Smaller** — the set shrinks; a file that grows is reported by name with its bytes, never offset elsewhere.
- **Outcome, delayed** — counted later from transcripts (below); a screen until then.

(one project's working practice; no count)

## The method

1. **The contradictions table** — one row each: both statements with `file:line` · the date of each · the winner and
   why · the edit. Two statements by the user that conflict, neither superseding the other in its own words → one
   question to the user with options and a recommendation, not your pick.
2. **The destinations table** — every unit of the before-text (a bullet, a numbered item, a paragraph) goes to exactly
   one of `kept` · `merged into <id>` · `pointer to <home>` · `notes <file>` · `dropped — <why>`. When in doubt, `kept`.
3. **One home per directive** — the file that owns the topic keeps it; every other copy becomes a pointer, or is
   dropped where the home is always loaded for the same reader.
4. **Every absolute gets its scope and its reason, or loses the absolute** — and is changed only on evidence: another
   loaded statement that says the opposite, or practice that already departs from the letter. Rewording a working
   line is itself a risk; «walked, nothing to change» is a valid result.
5. **Rationale and incidents move to a notes file behind a tag.** The rule line keeps `[date; tag]`; a
   `<rules>-evidence.md` beside it holds the story and the before-text verbatim. Old item numbers are never reused — a
   «former numbers» table maps each. A line that practice cites three times or more keeps its concrete trigger.
6. **Edits applied as data** — a script holding each `(file, old text, new text)`, run after the user's yes on a
   «was → becomes → why» table, so the change is reviewable and repeatable; the bars run after it.
7. **A behaviour check on fixed cases** — replay every changed line against the incident it was written for: the new
   text must still catch it, else the line stays verbatim. Then, after the pass, count over the next sessions against
   the last ones, by script: approval questions a rule already answers · stalls where two rules are cited against
   each other · wrong refusals by a gate.

(measured in one project, 2026-11: of 17 contradictions 13 were resolved by an edit, 2 were not contradictions, 2 lay
in files the project does not own, 2 more rows went to the user; obligations went 51 → 31 against a target of ≤ 30,
always-loaded rules 55.2 → 53.2 KB, the main process file 26.3 → 20.8 KB, 293 numbered citations with 0 unresolved; a
second batch walked 88 absolutes of three files — 83 kept, 5 changed — and those files grew by 219 bytes.)
The effect on behaviour (in trial in one project since 2026-11-11; count due after the next three working sessions).

## Traps met on the way

- **A hook edit made during the pass cut a neighbouring helper function** — the committed hook exited 1 for minutes.
  Run an edited hook once before the commit, through its wiring (`harness-measurement.md` M4).
- **A markdown formatter renumbers an ordered list with gaps** — with stable item numbers, write the items as
  bold-led paragraphs, not a numbered list.
- **«No touched file grows» forgot the home that receives moved text** — report the failure as it is; do not restate
  the bar after the result (one project's working practice; no count).

Related: `project-extensions.md` (what shape a rule should have at all) · `review-loop.md` §2 (the drop rule for lines
that never fire) · `doc-governance.md` R1–R2 (one home per fact).
