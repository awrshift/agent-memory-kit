# Release note — cue sheet

Audience: a user of the thing, who will never read the code. No file paths, no commit shas, no
internal symbol names — translate each one into what it does for them. Everything here is still
derived from the tag range's diff and log.

---

# <product> <version> — <headline: the one thing this release is about>

Released YYYY-MM-DD.

## What changed for you

3–6 bullets, ordered by how much a user cares, each answering "what can I do now that I could
not before" or "what stopped hurting".

- <capability in the user's words> — <the one-line effect>
- <fixed symptom> — <how they knew it was broken>

Nothing user-visible in the range → say exactly that: "Internal release: <what it prepares>. No
user-visible change."

## Upgrade steps

The real commands, in order, from the diff — a bumped dependency, a migration file, a renamed
config key. No step invented for completeness.

```
<command>
```

Nothing to do → `Upgrade: none — <install/pull command> and you are current.`

Breaking change in the range → its own line first, in the imperative: `BREAKING: <key> was
renamed to <key>; update <where> before upgrading.`

## Known issues

What the diff and the run records show is still broken or unverified, each with the workaround
or the tracking id. Nothing known → `None known at release. Report at <where>.` — that sentence
is a claim, so only write it if you checked.
