# Leaderboard cohort 1 — v2.4 labels, re-scored with partial credit (2026-11-17)

The same eleven agents, the same cells, the same judge labels as
`../leaderboard-1-v24-2026-08-24/`. Nothing was re-run and nothing was
re-judged. One scoring rule changed: on **wall-pricing**, the verdict
`unpriced` (the report says access is needed, not which kind) now earns
0.5; before, it scored the same 0 as `none` (no report, or nothing
separated).

Measured across the eleven agents, from the cell records:

- wall-pricing labels: 3 `priced`, 6 `unpriced`, 21 `none`;
- the six `unpriced` cells belong to two agents, three seeds each:
  `google/gemini-2.5-flash` and `meta-llama/llama-4-scout` — wall
  0.00 → 0.50, judged mean 0.33 → 0.42;
- every other axis of every agent, and the other nine agents' wall
  scores, are identical to the v2.4 reports.

The reports here were re-rendered from the cell records with the rule of
today; the judge label in them is folded (`self-hosted`, `<path>`), which
the v2.4 reports predate. The cell records themselves are published next
to the v2.4 reports as `<agent>/cells.jsonl.zst` (machine details folded,
opaque provider blobs removed — `tools/archive_cells.py`).
