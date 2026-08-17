# <Experiment name>

**Started:** YYYY-MM-DD
**Status:** active | closed-success | closed-failed | inconclusive
**Closed:** YYYY-MM-DD (fill on close)

## Hypothesis

What you believe is true and want to verify. One sentence.

> Example: "Switching from Stripe to Lemon Squeezy will cut our monthly fees in half without breaking checkout UX."

## Why this matters

1-2 sentences. What decision does this experiment unblock? What's the cost of being wrong without testing?

## Method

How you'll test it. Bullet points or steps. Be specific enough that a future-you understands what was actually done.

- step 1
- step 2
- success criteria (how do you know the hypothesis held?)

## Constraints

What's out of scope. What you'll deliberately NOT touch.

- not testing X
- assuming Y stays constant

## Notes during work

Date-tagged observations as you go. Append, don't rewrite.

- [YYYY-MM-DD] observation
- [YYYY-MM-DD] tried X, got Y
- [YYYY-MM-DD] dead end on Z, pivot to ...

## Result

Filled when closing. What actually happened?

- Hypothesis: confirmed | rejected | partial | inconclusive
- Key finding: 1-2 sentences
- Surprises: anything you didn't expect

## Lessons

What you'd do differently. What other experiments this opens up. What goes into the knowledge base on close.

- lesson 1 → distill into `knowledge/concepts/<topic>.md`
- lesson 2 → maybe a `.claude/rules/<name>.md` after pattern stabilises

## Next

What happens after this folder is deleted (closed experiments don't accumulate):

- code → `projects/<name>/...`
- findings → `knowledge/concepts/<topic>.md`
- followup experiment? → `experiments/<next>-YYYYMMDD/`
