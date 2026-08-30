# Leaderboard cohort 1 — 2026-08-23

Nine agents on the standard set v2 (8 scenes × seeds 4242/777/31337),
judged by the qualified self-hosted Qwen3.6-35B-A3B (IQ4_XS). The table
is rendered from these sealed reports by `tools/journeyman_leaderboard.py`
into `docs/leaderboard.md`; nothing there is hand-entered.

- `deepseek-r1-0528`: PARTIAL — 17/24 cells, stopped on cost; judged
  afterwards with the same judge; `nonstandard` stamps the report.
- `nemotron-3-super-120b-a12b`: 4 cells lost to provider 429s on the
  first pass, re-run on resume with the retry-armoured driver.
- Reports were rendered after the `na_means` change (route-discipline
  `na` = not-applicable); raw cell records are retained off-repo by the
  maintainers for re-judging.
