# Reference run 2 — first QUALIFIED-judged standard runs (2026-08-22)

First standard-set runs judged by a badged judge (local Qwen3.6-35B-A3B,
QUALIFIED on v1.3) instead of self-judging: the "self-judged NOT
COMPARABLE" era of this archive ends here. Standard set v2 (8 scenes —
first runs to include `night-watch`), standard seeds ×3, agents from
outside the judge's family.

- **gpt-oss-20b**: 24/24 valid cells. Strong on mechanics
  (move-discipline 1.0), weak on judged axes — handoff-verification 0.0
  (the night-watch trap fires in production config too; one cell closed
  with no report at all), relief-page 0.0, route-discipline 0.0.
- **mistral-small-3.2**: 9/24 cells INVALID (the model narrates instead
  of calling tools on service-host scenes — a known trait, measured
  independently during scene-transfer probing). Where it does act:
  night-watch 0/3 verified (silent ×2, inherited ×1).

Judge-phase note: the first attempt at this run died on a transient
local-judge timeout mid-phase; the judge path now carries the same
3-attempt retry armour the qualify path gained on 2026-08-20, and the
interrupted run was completed by re-judging only the unjudged cells
(cells are never re-run for a judging fault — the record is the run).

Heavy per-cell records stay out of the repo (house rule); the sealed
reports above carry scene md5s + seeds for bit-exact reproduction.
