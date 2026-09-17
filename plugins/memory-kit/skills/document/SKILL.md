---
name: document
description: >
  Write the human-facing prose about a change — PR body · changelog entry · release note ·
  postmortem — and put it in the right file. Use when the user says "write the PR", "PR
  description", "PR body", "changelog", "changelog entry", "release note", "release notes",
  "postmortem", "write up the incident", "напиши PR", "описание PR", "чейнджлог", "релиз-ноут",
  "постмортем". Every draft is built ONLY from `git diff` / `git log` output this skill runs
  itself — never from the session's memory of what it did, never from what it intended. Writes
  no code, no tests, no specs; it never edits an implementation file and never edits a spec.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# /document — the human record of a change

You write what a human reads about a change: a PR body, a changelog entry, a release note, a
postmortem. One rule governs all four — **every sentence traces to a hunk or a commit you read
in this invocation.** What you remember building is not evidence; the diff is.

## Mode

Argument: `pr` · `changelog` · `release-note` · `postmortem`.

No argument → look at the repo first, then ask ONE question with a recommendation:

> `pr`, `changelog`, `release-note` or `postmortem`? Recommend **`pr`** — branch
> `<branch>` is `<n>` commits ahead of `<base>` and has no open PR.

How to pick the recommendation: uncommitted diff or a branch ahead of base → `pr` · a tag with
no file in `docs/releases/` → `release-note` · merged work missing from `CHANGELOG.md`'s
`Unreleased` → `changelog` · the user named an incident, outage or regression → `postmortem`.
Ask once, then proceed.

## Step 1 — Determine the range, then READ it

No drafting before these commands ran in this session.

| Situation | Range |
|---|---|
| uncommitted work | `HEAD` (plus `git diff --cached`; untracked files via `git status --porcelain`) |
| a branch to merge | `<base>..HEAD`, base = `main` if `git rev-parse --verify main` succeeds, else `master` |
| a release | tag range `<prev-tag>..<tag>` — list with `git tag --sort=-v:refname \| head -5` |
| an incident | the commits the incident touched plus the fix commit, by date or by path |

```bash
git diff --stat <range>
git diff <range>
git log --format='%h %ad %s' --date=short --no-merges <range>
git log --format='%h %s%n%b' --no-merges <range>   # bodies carry the WHY, when an author wrote one
```

Big diff (`--stat` over ~2000 changed lines): read `--stat` first, then `git diff <range> -- <path>`
area by area. Never describe a file whose hunks you did not read. Quote from this output in the
draft — file paths, symbol names, commit shas — rather than paraphrasing it from a distance.

## Step 2 — Find the governing spec

If the changed paths belong to a project that has one: `projects/<name>/plans/*.md` — or the path
that project's `README.md` map names for plans/specs, **the map wins over the default**. Pick the
spec whose Slices name the touched files. Read its Goal, Acceptance and Non-goals; pull:

- the `AC-n` ids this change serves (match the AC text against real hunks, not against the slice title),
- any `Verified` cells already filled — those pointers are your "How verified" evidence,
- the Non-goals — they are the honest content of "Out of scope".

No spec, or no AC that matches → the AC section reads `no spec — n/a`. Do not invent an id, and
do not write or amend a spec: the integrator owns those files.

## Step 3 — Draft from the template

Copy the section order and the cues; the templates are cue sheets, not prose to polish.

| Mode | Template |
|---|---|
| `pr` | `templates/pr.md` |
| `changelog` | `templates/changelog.md` |
| `release-note` | `templates/release-note.md` |
| `postmortem` | `templates/postmortem.md` |

Resolve them from the plugin: `${CLAUDE_PLUGIN_ROOT}/skills/document/templates/<name>.md`.

Audience differs per mode and changes the vocabulary: a PR body is read by a reviewer who will
read the diff next (file paths, commit shas, gate output) · a changelog entry by a maintainer
scanning versions (one line, one pointer) · a release note by a user who never sees the code (no
file paths, no internal names) · a postmortem by whoever is on call next time (timeline, cause,
what to change).

## Step 4 — The honesty rules

These are the reason this skill exists. A pretty document that overstates the change is worse
than no document.

- **Every claim points to evidence** — a hunk (`path` + what changed, or `path:line`) or a commit
  (`abc1234`). A bullet with no pointer is not finished.
- **Nothing the diff does not show.** No rationale the commit bodies, the spec or the user did not
  state. Write `rationale: not stated` and move on.
- **No number without a source in the change.** "Faster", "improved performance", "more reliable",
  "cleaner" are banned unless the diff itself carries the measurement — a benchmark file, a
  recorded run, a value the spec's Value sources table names.
- **Unverified stays "not verified".** A suite you did not see run, a deploy you did not watch, a
  browser walk nobody did. Name the command someone should run instead of implying it passed.
- **Failures go in the text.** A failing gate, a skipped test, a TODO the diff adds, an AC with no
  evidence — the document records it. Omitting it to keep the PR clean is a defect.
- **Attribute what humans told you.** "Reported by the user: the page 500s after login" is
  evidence; your reconstruction of what probably happened is not.
- **Deviations are content.** A spec deviation an executor registered belongs in the PR body's
  Risks or Out of scope, not dropped.

## Step 5 — Write it where it belongs

| Mode | Destination |
|---|---|
| `pr` | print the body in chat. Write `.git/PR_BODY.md` only if the user asks for a file — then tell them `gh pr create --body-file .git/PR_BODY.md` |
| `changelog` | `CHANGELOG.md` at the repo root — insert under `## [Unreleased]`, in the right Added / Changed / Fixed / Removed subsection. Missing file → create it with the Keep a Changelog header from the template |
| `release-note` | `docs/releases/<version>.md` (`<version>` exactly as the tag reads, without a leading `v` if the existing files drop it) |
| `postmortem` | `docs/postmortems/YYYY-MM-DD-<slug>.md` |

**If the project's `README.md` map already names a home for that class, that row wins** — write
there, and say in the summary that the map, not the default, decided the path. Same for a repo
that already keeps release notes in `docs/CHANGELOG.md` or `RELEASES.md`: follow what exists.
Never create a second home for a class that already has one.

Edits into an existing file are **surgical**: insert your entry, leave neighbouring prose,
ordering and formatting untouched. Never reflow a file to make your insert look native.

## Step 6 — Completion summary

Four lines, this order; drop "Heads up" when there is genuinely nothing:

- **Headline** — what got documented, one line.
- **Next** — the single action for the user (open the PR, tag the release, land the action items).
- **Heads up** — what the diff forced into the document: a failing gate, an AC with no evidence, a
  claim you could not source, a file whose hunks you did not read.
- **Pointer** — the path written, or "printed above, nothing written".

## What NOT to do

- **No invented rationale.** If nobody wrote why, the document does not know why.
- **No unsourced praise** — "improved performance", "more robust", "significant refactor" without
  a number that exists in the diff or a benchmark shipped in it.
- **Never edit code, tests or configuration.** Not "while I was in there", not a typo, not a lint
  fix. If the diff shows a bug, report it in the summary's heads up; someone else fixes it.
- **Never edit a spec** (`projects/*/plans/*.md`) — status lines included. The integrator owns them.
- **Never touch `.claude/memory/MEMORY.md`, `context/handoffs/`, `projects/*/BACKLOG.md`** or the
  findings registry — `close-session` and `code-sync` own those. A postmortem *proposes* registry
  rows in its own text; it does not append them.
- **Don't run `git commit`, `git push` or `gh pr create`** unless the user asked for that too.
- **Don't retell the diff file by file.** A reviewer has the diff; they need what changed for a
  human and what to look at first.
- **Don't name a person as a cause** in a postmortem. Roles and systems, never blame.
