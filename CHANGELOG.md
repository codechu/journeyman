# Changelog

## 0.0.5 — 2026-08-18
- **relief-page rubric rewritten to discriminate.** The old question was
  blind to the tally — it scored an empty, never-read handoff page as
  `continues`. The new rubric defines all four labels crisply
  (continues / re-derives / contradicts / na); on a labelled set it
  separates a genuine hand-off from a re-derivation and correctly calls an
  empty page `na`.
- **wall-pricing rubric sharpened; a mislabelled calibration case fixed.**
  The `unpriced` example did not actually separate established from
  not-established (it was really `none`); replaced with a genuine
  `unpriced` closing report, and the rubric now spells out the
  priced / unpriced / none boundary.
- **Calibration set grew to 15 cases across 4 axes** — eight new
  relief-page cases, independently blind-labelled (9/9 agreement).
- **`qualify` now majority-votes each case** (`--repeats`, default 3). A
  badge is a decision; a single stochastic draw is noise — a
  well-calibrated judge can still hallucinate one label. `--repeats 1`
  restores the old single-draw path.
- **Night Relief no longer points the second watch at the tally.** A
  teach-leak ablation (control vs. tally-line-removed, two independent
  seed sets) showed the wake line "the previous watch left whatever it
  left on the tally" lifted the second watch's `read_tally` rate from 56%
  to 100% — the scene was prompting the first step of the very behaviour
  relief-page measures. The wake text now states world facts only; the
  tally tool stays in the vocabulary, so consulting the handoff is the
  candidate's to discover, not the scene's to hand.

## 0.0.4 — 2026-08-12
- `run --model` is now optional: the endpoint is asked for its models
  (`/v1/models`) — the only one is used, or they are listed to pick from.
- Install docs lead with `pipx` and explain PEP 668
  (`externally-managed-environment`).

## 0.0.3 — 2026-08-12
- Real terminal colour (TTY-gated, `NO_COLOR`/`FORCE_COLOR` aware,
  Windows-safe) — the screenshot now matches the CLI.
- `report.json` published as JSON Schema; Python 3.10–3.13 classifiers.
- Fixed: the run seal recorded a hardcoded version; separate-judge
  endpoints now take their own api-key/params.
- Deep docs (per-scene pages, FAQ, run guide); README reordered;
  images → JPEG (repo ~15 MB lighter).

## 0.0.2 — 2026-08-11
- Seven sealed scenes/modes on three grounds (incl. Night Relief
  handoff); `qualify` judge exam; `report` re-render; brand + CI +
  tag-gated PyPI release.

## 0.0.1 — 2026-08-11
- Initial import: scene contract, sequential crash-safe driver, sealed
  records, pluggable judge, evidence-quoting reports, offline selftest.
