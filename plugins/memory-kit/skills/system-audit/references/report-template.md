---
title: System audit — <repo/system name>
date: YYYY-MM-DD
depth: quick | standard | deep
scope: <layers audited; layers marked n/a>
prior_audit: <path to previous report, or "first">
---

# System audit — YYYY-MM-DD

## 0. Verdict (three lines)

- **Works:** …
- **Drifts:** …
- **Missing:** …

## 1. Delta from the previous audit

| previous priority | status | evidence |
|---|---|---|
| … | done / partial / ignored | file:line or command |

> If most of last time's priorities were ignored — that's finding #1. The reason matters more than the list.

## 2. Findings by lens

One table for the whole audit. `severity`: 🔴 broken · 🟠 drifting · 🟡 unverified · ⚪ missing · 🗑 excess.
`evidence` — what was verified PERSONALLY (file:line / command+output). Without it — `hypothesis` + what would verify it.

| # | lens | sev | finding | evidence | verified by | status |
|---|---|---|---|---|---|---|
| F-01 | 1 delivery | 🟠 | … | `path:line` | me / recon+reverified | accepted |

## 3. Priorities (max 5)

| # | what to do | why now | cost | what breaks if not done |
|---|---|---|---|---|
| P1 | … | … | ~20 min | … |

## 4. Subtraction (quota ≥3)

| what | evidence it's dead | cost to keep | what breaks if removed | action |
|---|---|---|---|---|
| … | not seen in N sessions | attention/tokens/drift | nothing | delete / merge / label historical |

## 5. Not recommended (deliberately)

What suggested itself but costs more than it's worth at the current scale — with one line "why not".
This section matters as much as the priorities: it keeps the audit from bloating the system.

## 6. What was already fixed this session

- … (file:line, what changed)

## 7. Needs the user's decision

- … (deletions, history purge, external actions, cost)
