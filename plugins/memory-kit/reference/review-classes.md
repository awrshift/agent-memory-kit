---
created: 2026-11-11
last-reviewed: 2026-11-11
---

# Review classes — twelve defect classes one backend project kept meeting, each with its check

> Read on demand, when you review a diff or write a review checklist. Each entry: the class in one sentence · the
> check that catches it · the month of the incident that taught it. Copy the lines your system needs into your own
> checklist, each with your own incident and family (`review-loop.md` §2) — a line copied without a case of yours is
> a hypothesis there.

**Applies when:** you review code that takes outside input, runs queued or retried work, or acts on model output.

Every entry below: (one project's working practice; no count) — the date is the incident, not a measurement.

## Functional correctness

1. **The same class, next door.** A fixed defect usually has siblings. Check: name the MECHANISM of the fix and grep
   for it one layer up, in sibling call sites and fields, in the other place that applies the same rule, and under
   other vocabulary; list what was checked in the PR text. Two functions deciding one rule become one shared
   predicate. Incident 2026-09: the downstream reviewer's most repeated flag on that project's PRs.
2. **A check is named by what it proves.** A test, scorer or gate that re-runs an existing gate proves only that gate.
   Check: label it «re-verified»; its name and report state what it cannot see. Incident 2026-09: a harness reported
   «0 facts changed» by re-running the system's own checking functions.
3. **A text heuristic ships with its false-positive count on your own corpus** — including a heuristic the
   integrator decides in a spec. Check: the count on stored real inputs, both sides, before merge. Incident 2026-09:
   an unmeasured «an all-caps word is a name» rule made titles worse and fixed none.
4. **A heuristic that deletes defaults to keep.** It deletes only on a positive signal of what may go, never on the
   absence of a signal of what must stay; its count reports both sides — content lost and junk kept. A classifier
   that marks input unusable (`blocked`, `invalid`, `skip`) is a deleting heuristic. Check: test it on an item ABOUT
   its trigger phrase. Incidents 2026-09, 2026-10: a generic phrase in a page body marked a page about that very
   subject unusable, and its evidence was dropped silently.
5. **Refuse and accept are two predicates.** One function serving both drifts: every loosening for one side breaks
   the other. Check: two predicates, each named by its decision; the refusing side strict (positive signal only), the
   accepting side lenient; a false-positive count for each. Incident 2026-10: one name normaliser decided both «these
   two entities are the same» and «this heading names the entity».
6. **A filter that removes items makes every summary of the unfiltered set stale.** Check: a summary derived before
   the filter (counts, focus lists, recommendations) is not forwarded past it — or is recomputed from the kept set;
   never filtered by another model judgment. Incident 2026-10: a gate dropped items, while a summary written over the
   full list carried both dropped topics onward; two rounds of a second model judgment over the summary each opened
   new defects.

## Data and state

7. **A value the server cannot keep is refused, never accepted and dropped.** Check: a request field the write path
   would discard, clamp or null answers a 4xx naming the field — checked on the RESULTING row where an update merges
   with stored data; a fallback that swaps the caller's input for a default says so in the response or refuses.
   Incident 2026-10: a field sent in a shape the write path could not store answered 200/201 and stored null —
   first on one resource, then the same class on another.
8. **A write or a decision about an invocation is keyed to that invocation's own identity** — its hold id, its job
   id, the id its own request asked for — never to an id the next claim reuses, a state read, or a clock. Check: for
   each such write, name the key and who else can hold it. Incident 2026-10: four cases in one feature — a swallowed
   add, an old run's tail releasing the new run's hold, a stale key judged by a clock, a claim's own job taken for a
   stale holder by a state read.
9. **An ownership decision («is this invocation still mine?») is a total function.** Check: it never throws (a read
   failure answers `error`, which refuses), never leaves a live queue artefact behind (a delayed nudge, a stamp), and
   answers exactly one of `owned` · `not_mine` · `ended_by_other` · `error`; one table test feeds every call site every
   outcome. Incident 2026-11: written after the third fix round of a double-run defect.

## Untrusted input

10. **A predicate over a URL decides on the parsed fields** (`protocol`, `host`, `username`, `password`,
    `pathname`), never on the string. Check: grep the diff for string tests on URLs. Incident 2026-10: a hand-cut check
    let `https:///user:pass@host.example` through, because the URL parser reads it as an address with a login; a
    background security review caught it, the gates and the review checklist did not.
11. **A regex, recursion or backtracking walk over text you do not author ships with its worst case measured — without
    a stopwatch.** Check: feed a long repetitive input (a two-letter alphabet, an unclosed opener repeated) into every
    string argument; work sized by the input has a stated cap; the test asserts an operation count or the input cap,
    never milliseconds. Incidents 2026-10: a link pattern was quadratic on an unclosed `[`, 200,000 characters took
    18.6 s, synchronously; 2026-11: wall-clock bounds failed under the commit hook's load, and a GC pause read as
    superlinear growth.

## Tests

12. **One test per outcome, with a reachable Given.** Check: before a unit test is written, name the OUTCOME it
    proves and the real writer that produces its Given (`file:line`). A state no writer produces gets no test — the
    boundary that rejects it is tested once instead; variations of one input that reach the same outcome are one test.
    Incident 2026-11: the upstream repository's maintainer ported that project's tests and cut 29 cases to 11, removing
    tests whose Given no writer produces — each removal checked correct.

Related: `review-loop.md` (triage, the diff gate, the family registry these lines feed) · `spec-depth.md` §5 (a
heuristic's count is a screen until the outcome is measured) · `measurement-lessons.md` (counting a classifier).
