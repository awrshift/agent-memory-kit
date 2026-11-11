<!-- from one project's practice, in trial since 2026-11; count due at six acceptances; see reference/acceptance.md -->
<!-- Applies when: you accept a helper's build after a review round. -->

# <block> — acceptance

**Created:** YYYY-MM-DD · **Verdict:** ACCEPTED | NOT ACCEPTED — <one line why>

> Written by the integrator, the only writer here, when a block's build (and its fix rounds) is accepted. One file per
> accepted head, beside the block's review records. What «blocking» means, why a fix round may not redesign, and what
> the gates line owes: the plugin's `reference/acceptance.md`.

- Head: `<full commit hash of the accepted tree>`
- Spec: `<path>` (`v<N>` when a redesign made a new spec version)
- Rounds: <number of fix rounds; 0 = the build only>
- Build review: `<review record path>` · range `<base>..<head>` — with no fix round
- Fix-diff review: `<review record path>` · range `<build head>..<fix head>` — after a fix round, replaces Build review
- Gates: re-run by the integrator on this Head: `<each command>` → `<its last line>` | `<receipt for exactly this tree>`
- Gate ruling: `<gate>` — <why it passes although it failed or timed out> (only when one did)

## Findings decided

One ruling line per finding id of the review record — every id, none skipped; ids as the record writes them.

- F1 · <fixed in `<hash>` | ticket `<where>` | rejected — <why>>
- M1 · <kept as part of the fix | the round stops — the redesign is a new spec version, read before its build>
- Layer: <ruling> (only when the reviewer's layer verdict is «disagree»)

## Other tops

Optional: each other finished head held unsent that this Head does not contain — hash and one word, one line each.

- `<hash>` · parallel | to merge | merged | dropped | sent
