# Pattern: capability-map reuse sweep

> A recon pattern for the "the library already does this" defect class: hand-rolled code that
> duplicates what your INSTALLED dependencies provide. Run it when a code review catches one
> such find and siblings are likely — one confirmed instance is the trigger, not a calendar.

## Method (three stages, integrator adjudicates)

1. **Capability maps (recon agents, one per dependency cluster).** Each agent builds a map of
   what a dependency can do — with **ground truth read from the installed package's typings /
   source in `node_modules` (or your ecosystem's equivalent), never from model memory**. Pin
   the map to the installed version. Cluster related deps into one map (e.g. router · ORM+queue
   · framework+validation) so each agent holds a coherent surface.
2. **Finder pass.** A finder agent sweeps your source against the maps: where does hand-rolled
   code duplicate a mapped capability? Output: candidate sites with file:line, the replacing
   capability, and an honest replaceability verdict (clean / partial / structurally NOT
   replaceable — say why).
3. **Adjudication (integrator).** Read the load-bearing candidates yourself before minting any
   ticket. Expect refutations in BOTH directions: the finder refuting a map row (an API the
   map hallucinated or the installed version lacks), and you refuting a finder claim by
   reading the actual body. A sweep that produces zero refutations probably wasn't checked.

## What the output is

A short research doc (maps' durable summary + the honest split + tickets minted), not a
refactor spree. "Paid off as a MAP, mostly polish as DEBT" is a legitimate verdict — the map's
value is knowing where the line is. Prevention of NEW instances belongs to the standing diff
review gate (`rules/review-loop.md`), not to repeated sweeps.
