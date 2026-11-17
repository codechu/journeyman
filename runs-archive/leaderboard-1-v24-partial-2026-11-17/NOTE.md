# Leaderboard cohort 1 — v2.4 reports with partial credit beside the score (2026-11-17)

The same eleven agents, the same cells, the same judge labels as
`../leaderboard-1-v24-2026-08-24/`. Nothing was re-run and nothing was
re-judged, and no score changed: every `score`, `per_seed` and `n` here
equals the v2.4 report (checked axis by axis when these were rendered).

What is new is two added fields on **wall-pricing**:

- `score_partial` — the same ratio with `unpriced` (the report says
  access is needed, not which kind) counted at 0.5;
- `verdict_counts` — how many cells got each label.

Across the eleven agents: 3 `priced`, 6 `unpriced`, 21 `none`. The six
`unpriced` cells belong to two agents, three seeds each —
`google/gemini-2.5-flash` and `meta-llama/llama-4-scout`: score 0.00,
partial 0.50. For every other agent the two numbers are equal.

The judge label in these reports is folded (`self-hosted`, `<path>`),
which the v2.4 reports predate. The cell records are published next to
the v2.4 reports as `<agent>/cells.jsonl.zst` (`tools/archive_cells.py`).
