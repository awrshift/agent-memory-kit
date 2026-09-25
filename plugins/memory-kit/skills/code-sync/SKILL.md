---
name: code-sync
description: >
  Reconcile the project's documents with what the code now shows, after a merge or at the end of
  a build: spec statuses (building → done only with a named gate, or → stale with the reason),
  assumed specs owed ratification, the project README map and its Last verified date. Surgical
  edits only. Use when the user says "/memory-kit:code-sync", "sync the docs", "sync specs with
  code", "синхронизируй доки с кодом", "что устарело в спеках", or right after merging an
  executor branch.
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# /code-sync — documents reconciled against the repository

`close-session` reconciles the SESSION with memory. This reconciles a PROJECT's documents with
the CODE: every claim a spec still makes is checked against what is in the tree right now.

Two rails hold the whole skill up. **Evidence, never a claim** — a spec becomes `done` only from
a gate YOU ran in this session or a `Verified` cell someone already filled. **Surgical edits
only** — the only things you write are a status value, a `Verified` cell, one `Stale since:`
line, a map row, `Last verified:`, and a BACKLOG Done line. Everything else keeps its bytes.

## Step 0 — locate the projects

- `Glob projects/*/README.md`. If the repo keeps its documents elsewhere, read the root
  `CLAUDE.md` / `README.md` for the docs home and use the map it names. Nothing found → say so
  and stop. This skill never scaffolds.
- From each project README read two things: the map table ("Where this project's documents
  live") — the SSOT for where plans, QA records and the backlog actually are — and the
  `**Workflow tier:**` line, which sets how much evidence a `done` needs:

| Tier | Evidence a `done` needs |
|---|---|
| `prototype` | the gate output, run by you |
| `alpha` | + an integrator acceptance walk named in the `Verified` cell |
| `beta` | + a `qa/qa-run-*.md` record and tests naming each `AC-n` |
| `ga` | + a review pass and a `document` entry for the change |

- The user named one project → sweep only that one. Otherwise sweep all of them.

## Step 1 — inventory the specs

Read the header of every `plans/*.md` (`**Created:** YYYY-MM-DD · **Status:** …`; one grep over
the folder is enough). A plain `Status: …` line counts too, and a spec with no `Created:` takes its
date from a `YYYY-MM-DD-<slug>.md` file name — the SessionStart spec flags read them the same way.
A spec with no status line at all is counted as `no status` in the table, never guessed. Statuses are `draft · decided · building · done · superseded · assumed ·
stale`. Build the working table: spec · status · created · age in days.

`building` goes to step 2, `assumed` to step 3. `draft`, `decided`, `done`, `superseded` and
`stale` are counted and left untouched.

## Step 2 — every `building` spec against the code

Read its Acceptance table and its `## Gates` block in full. For each `AC-n` row hunt evidence in
this order and stop at the first that holds:

1. the row's `Verified` cell is already filled (date + pointer) → taken as is;
2. a QA run record naming the id — `grep -l "AC-3" projects/<name>/qa/qa-run-*.md` — and it
   records a pass;
3. a test that names the id (grep the test tree for the id), in a suite the gate below runs;
4. **the gate**: run the commands from the spec's `## Gates` block yourself, from the repo root,
   and read the output. A gate you did not run is not evidence.

Report per AC: evidence found (what · where) or missing. Then exactly one of:

- **All ACs have evidence** → set the status line to `done` and fill each `Verified` cell you
  earned with `YYYY-MM-DD · <the command you ran, or the record>`. Cells already filled stay as
  they are.
- **The code contradicts the spec** → check the spec's Slices "Files it owns" and the interfaces
  it names: `Glob`/`Grep` each one. A named file gone, a symbol renamed, a signature the spec
  depends on changed → set the status to `stale` and append, directly under the status line, one
  line: `**Stale since:** YYYY-MM-DD — <reason, file:line>`. A `stale` spec is never also `done`.
- **Anything else** → leave `building` exactly as it is and name what is missing: which `AC-n`,
  and what evidence would settle it. Half-evidence is not a flip.

## Step 3 — `assumed` specs owed ratification

An `assumed` spec is an executor's recorded override, not a decision. List every one of them:

| Assumed spec | Parent spec | Owed decision | Authorized by | Age |
|---|---|---|---|---|

Take Owed decision from the file's `## Owed decision` section, one line, and the authorizer from
its header. Print the table under the heading **Owed ratification** and recommend which to take
first (the oldest, or the one whose Code area the current work touches).

**Never flip or edit an `assumed` spec yourself.** The kit has no architect skill: the main
session deliberates, then either writes the real spec and marks the assumed one `superseded`, or
confirms the assumption and flips it to `decided`. Your output is that agenda, nothing more.

## Step 4 — BACKLOG.md, only what you can prove

A task moves to `## Done` only when BOTH hold: its `**Spec:**` points at a spec you flipped to
`done` in step 2, AND every box in its Acceptance list is already ticked. Then move it as one
line, newest first, in the file's own format:

```
- [YYYY-MM-DD] T-NNN — <its one line> · verified by `<the gate you ran>`
```

Everything else in that file — priorities, ordering, wording, `TODO` / `IN PROGRESS` / `BLOCKED`
statuses — is untouched. Never tick an acceptance box yourself: an unticked box is the
integrator's open question, not your paperwork.

## Step 5 — the README map and `Last verified`

For every document class that now has files on disk but no row in the map table, add the row
(Class · Path · Written by), using the classes the project template already names: Tasks ·
Plans / specs · Research + evidence · Decisions ledger · Review-finding classes · QA protocol +
runs · Client materials. An empty folder is not a row. A row that points at the wrong place is
the integrator's call — report the mismatch, don't repoint it. Then set `**Last verified:**` to
today. Nothing else in the README changes.

## Step 6 — report

Four lines, the kit's shape:

- **Headline:** `N specs reconciled: a done · b stale · c still building · d assumed owed`.
- **Next:** the ONE command or decision that moves this forward — the gate that would close the
  nearest `building` spec, or the assumed spec to ratify first.
- **Heads up:** only if a spec went `stale` — one line each, spec + reason.
- **Pointer:** the files you edited, as paths.

## Dry run

With the argument `--dry-run` — or when the user says "just show me" / "покажи, не трогай" — do
the whole walk and run the gates (reading is not writing), but print the plan of edits as a
table (file · line · from → to) instead of applying it. Nothing is written, not even
`Last verified:`. Close with the same four-line report plus the command to run it for real.

## What NOT to do

- **Never rewrite prose or a whole section.** The six writable things are listed at the top; if
  a fix needs anything else, report it instead of doing it.
- **Never mark `done` from a claim** — not an executor's report, not a subagent's summary, not
  "the tests should pass". Run the gate yourself (`reference/orchestrator-fact-check.md`).
- **Never flip or edit an `assumed` spec.** You list it; the integrator decides.
- **Never touch** `.claude/memory/MEMORY.md`, `context/handoffs/`, `knowledge/` or
  `.claude/rules/` — promotion lives in `/memory-kit:close-session`, on the user's yes.
- **Never create a file.** This skill creates none: no spec, no run record, no report file.
- **Never delete a document.** `superseded` and `stale` are labels, not removals
  (`reference/doc-governance.md`, R3).
- **Don't touch** a `draft`, `decided`, `done` or `superseded` spec at all — they are not yours
  to reconcile.
