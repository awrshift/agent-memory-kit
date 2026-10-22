# v7.3 build evidence (2026-10-22)

What the 7.3 hook changes were proven with, copied from the build session's scratchpad (doc-governance R5). Local paths
are shortened to `~`, the maintainer's project names replaced by `project-NN`; nothing else was changed. Scripts expect
the paths they name and are kept as a record, not as a runnable suite — the runnable proof is `plugins/memory-kit/hooks/tests/`.

| File | Proves |
|---|---|
| `hooks/red-*.txt` | each new test FAILED on the code before its fix (AC-1/2, AC-3, AC-6, AC-7, AC-17 rounds, symlinks) |
| `hooks/final-pytest.txt` | the branch suite green after the fixes |
| `hooks/ac4-*.txt` | Claude Code 2.1.290 validates a hooks.json carrying `onFailure`, still runs SessionStart (canary quoted by the model) and the secrets guard (canary .env not leaked) |
| `hooks/measure_legacy_hooks.py`, `measure-legacy-hooks-output.txt` | the double-wired-hook detector over 25 adopter repos: 8 flagged, 0 missed, 0 clean repos flagged |
| `hooks/size_loop.py` | every SessionStart source × part stays ≤ 10,000 characters |
| `hooks/time_session_end.py` | session-end.sh 0.56–0.61 s with stdin left open (was 1.04–1.08 s) against the 1.5 s budget |
| `hooks/check_real_handoff.py` | a real 6.2k-char handoff: the opening section arrives whole with 7.3, not with 7.2.3 |
| `zsh/measure.py`, `zsh/diff_selftest.py` | guard-zsh-split: worst case 100k-char inputs 0.03–0.08 s; 0 false positives on the source's 37 self-tests and a 60-command hand corpus (self-made — an estimate) |

| `r2/` | the code-review fix round: `red-run.txt` 30 new tests failing on the pre-fix code, `green-run.txt` 144 passed; worst-case timings before/after; part sizes ≤ 10,000 |
