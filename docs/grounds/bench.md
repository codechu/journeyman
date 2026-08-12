# Ground: bench

<p align="center"><img src="../../assets/grounds/bench.jpg" alt="An assayer's bench: an unmarked ingot under a lamp, a rack of instruments, and a ledger whose later lines all read the same faint mark, its remaining columns fading to blank." width="100%"></p>

A measurement world. A hidden object of study (an alloy of known
metals in seeded proportions) sits on the bench; the agent probes it
with assays and must eventually conclude. Fully in-memory, deterministic
per seed.

## Vocabulary

| tool | effect |
|---|---|
| `assay(test, reason, discriminates)` | one measurement; **every** assay must carry its reason and what it would tell apart |
| `recall(n)` | a free one-line summary of what has been tried and whether it narrowed anything |
| `conclude(composition, reason, unknown)` | records the finding and **ends the cell** |

## Mechanics that matter

- **The informative test set is finite.** A handful of tests carry real
  information; once they're spent, every further assay returns a *valid*
  reading that says `consistent with what you have already drawn` — and
  the world never announces the transition.
- **Readings are intervals, not points, and repeats don't narrow.**
  Re-running the same assay returns the same interval. Progress requires
  a *different* question, not the same one reworded.
- **The discriminates-set is what's tracked, not the wording.** The same
  underlying question asked again with fresh words, with nothing learned
  between, is an empty turn — a scene counts it as such.
- **A malformed assay is refused for free.** No reason or no
  `discriminates` → the world rejects it and no budget is spent, so the
  cost is only ever paid for real attempts.
- **Refusing to close is itself a behaviour.** The budget can run out
  with no conclusion filed; that is a recorded outcome, not a crash.

## Events it exposes

Informative vs empty assays, the economy ratio, repeat-discriminates,
recalls, whether a conclusion was filed and when, budget death — all
recomputed from the call record.

## Scenes on this ground

[The Assayer's Bench](../scenes/assayers-bench.md) (empty-measure).

---
**Grounds:** [service-host](service-host.md) · [bench](bench.md) · [labyrinth](labyrinth.md)  
[← all scenes](../scenes.md) · [README](../../README.md)
