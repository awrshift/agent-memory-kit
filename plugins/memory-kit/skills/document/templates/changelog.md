# Changelog entry — cue sheet

Audience: a maintainer scanning versions. One line per change, each with a pointer. Keep a
Changelog sections, in this order, and only the sections that have content.

New `CHANGELOG.md` starts with this header, once:

```markdown
# Changelog

All notable changes to this project are documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]
```

Then insert into the right subsection under `## [Unreleased]` — never above the header, never in
a released version's block.

```markdown
### Added
- <new capability, from the user's side> (`path/to/file.py`)

### Changed
- <behaviour that used to be X and is now Y> (`path/to/file.ts`, commit `abc1234`)

### Fixed
- <the symptom that stopped happening> (`path/to/file.py`; reported in <issue/incident>)

### Removed
- <what is gone, and what replaces it> (`path/that/is/gone.md`)
```

Rules for the line itself:

- Written from the effect, not the implementation: "session start now shows owed decisions", not
  "added `_collect_specs()`".
- Exactly one pointer per bullet — file path, commit sha, or issue id. No pointer → the bullet is
  not ready.
- No marketing adjectives, no "improved performance" without a number that exists in the diff.
- `Security` and `Deprecated` sections are allowed when the change is one; do not add empty ones.
- Cutting a release: rename `[Unreleased]` to `[<version>] - YYYY-MM-DD` and open a fresh empty
  `[Unreleased]` above it.
