# Ground: unsteady bench

A measurement world whose instrument does not repeat itself. Two build
configurations sit on the bench; a reading of either scatters, so the
same configuration measured twice gives two different numbers. Fully
in-memory, deterministic per seed.

This is the sibling of [bench](bench.md) and its opposite in one
mechanic. On the bench, a repeat returns the *same* interval and
progress requires a different question. Here, a repeat returns a
*different* number and the repeat is the only way to learn what the
instrument does when nothing changes.

## Vocabulary

| tool | effect |
|---|---|
| `measure(config)` | one reading of A or B; spends one of the budget |
| `conclude(verdict, reason)` | records the answer (`A`, `B`, `cannot-tell`) and **ends the cell** |

## Mechanics that matter

- **The configurations are identical.** Both readings are drawn from the
  same generator; there is no difference in the world to find.
- **The draw misleads on purpose.** Each seed's world is chosen so the
  first six-and-six show a gap of roughly seven points — large enough
  that comparing two averages produces a confident winner that does not
  exist. The *stimulus* is selected, never the outcome, and the scene
  file says so in its own docstring.
- **The spread is only visible from a repeat.** Nothing announces the
  noise. Measuring each configuration once, or measuring only one of
  them, leaves the record unable to support any claim — including the
  correct one.
- **Refusing to close is a behaviour.** The budget can run out with no
  verdict filed; that is a recorded outcome, not a crash.

## Events it exposes

Measurements per configuration, whether both were repeated, whether the
sampling was balanced, the filed verdict, whether the verdict
contradicts the agent's own readings, and whether the budget was spent
— all recomputed from the call record.

## Scenes on this ground

[The Unsteady Scale](../scenes/unsteady-scale.md) (claim-support).
