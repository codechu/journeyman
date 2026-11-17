# Leaderboard cohort 1 — v2.4 reports with the review score beside the score (2026-11-17)

The same eleven agents, the same cells, the same judge labels as
`../leaderboard-1-v24-2026-08-24/`. Nothing was re-run and nothing was
re-judged, and no score changed: every `score`, `per_seed` and `n` here
equals the v2.4 report (checked axis by axis when these were rendered).

What is new is two added fields:

- `verdict_counts` on every judged axis — how many cells got each label;
- `review_score` on the three axes whose rubric defines a middle label,
  counted at 0.5: `unpriced` (wall-pricing), `mixed` (grounding),
  `re-derives` (relief-page).

Where the review score differs from the score:

| agent | axis | score | review |
|---|---|---|---|
| gemini-2.5-flash | wall-pricing | 0.00 | 0.50 |
| llama-4-scout | wall-pricing | 0.00 | 0.50 |
| kimi-k2 | grounding | 0.33 | 0.50 |
| kimi-k2 | relief-page | 0.33 | 0.50 |
| glm-5.2 | relief-page | 0.33 | 0.67 |
| mistral-small | grounding | 0.67 | 0.83 |
| gpt-oss-120b | grounding | 0.00 | 0.33 |
| nemotron-3-super-120b-a12b | relief-page | 0.00 | 0.17 |
| gpt-5.6-luna | relief-page | 0.00 | 0.17 |
| qwen3.6-35b-a3b | relief-page | 0.00 | 0.17 |

The judge label in these reports is folded (`self-hosted`, `<path>`),
which the v2.4 reports predate. The cell records are published next to
the v2.4 reports as `<agent>/cells.jsonl.zst` (`tools/archive_cells.py`).
