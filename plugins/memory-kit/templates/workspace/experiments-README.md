# experiments/

Sandbox layer. Hypothesis testing, prototypes, throwaway research, R&D — anything that isn't real client work.

## How `experiments/` differs from `projects/`

| | `projects/<name>/` | `experiments/<name>-YYYYMMDD/` |
|---|---|---|
| **Purpose** | Real client / product work | Hypothesis, prototype, research |
| **Quality bar** | Polish, ship-ready | Rough is fine |
| **Lifetime** | Indefinite (active client) | Days to weeks; closed when answered |
| **Promotion to rules/concepts** | YES — patterns become canonical | NO — first distill into projects/ or knowledge/concepts/, THEN close |
| **Survives `/memory-kit:close-session` audit** | YES — agent proposes promotions | Limited — `/memory-kit:close-session` does NOT promote experiment patterns directly |

## Naming convention

`<descriptive-name>-YYYYMMDD` — date-tagged. The date is the **start** date.

```
experiments/
├── payment-provider-selection-20260427/
├── landing-page-redesign-20260415/
└── claude-tts-prototype-20260322/
```

Why date-tagged (not numbered): aligns with the kit-wide date-tagging convention. Lets you sort chronologically, see at a glance how old something is, and `/memory-kit:close-session` can check freshness ("3 experiments older than 30 days — still active or close them?").

## Inside an experiment

Every experiment folder has at least:

- `EXPERIMENT.md` — hypothesis, method, goal, result, lessons (use `EXPERIMENT-TEMPLATE.md` as the starting point)

Optionally:

- `BACKLOG.md` — if the experiment is multi-step
- Code, notes, screenshots, research files — anything goes, this is a sandbox
- Sub-experiments allowed: `experiments/parent-20260415/sub-test-20260420/`

## Lifecycle

1. **Open** — agent creates `experiments/<name>-YYYYMMDD/EXPERIMENT.md` when user says "let's try X" / "prototype Y" / "test the hypothesis that Z"
2. **Work** — write code, notes, results inside the folder
3. **Close** — when user says "the experiment is done" / "we have an answer", agent runs the **distill ritual**:
   - Successful: lessons → `knowledge/concepts/<topic>.md`, code → `projects/<name>/`, then `rm -rf experiments/<name>-YYYYMMDD/` (git history remembers)
   - Failed with lessons: `knowledge/concepts/<topic>-failed.md` capturing why, then delete folder
   - Inconclusive: leave as-is, revisit on next `/memory-kit:close-session`
4. **Forgotten experiments** — `/memory-kit:close-session` flags experiments older than 30 days that haven't been closed; agent asks user

## Agent triggers

When the user says any of these, agent creates an experiment, NOT a project:

- "let's experiment with..."
- "prototype X"
- "I want to test the hypothesis that..."
- "throwaway test for..."
- "quick R&D on..."

If unsure: ask. "Is this real work for an existing project, or an experiment to figure something out?"
