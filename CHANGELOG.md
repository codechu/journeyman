# Changelog

## Unreleased
- **The REAL calibration set: `calibration/v1_real.json` (59 cases, 6
  axes; v1.3).** Distilled from transcript-bearing reference runs of
  third-party models of different strengths; every case blind-labelled
  by a three-labeller panel under a protocol frozen before labelling
  (>=2/3 majority, splits discarded, stimulus identical to what the
  judge sees). Contested cases were adjudicated case-by-case by the
  maintainer against mechanical evidence, then probed by a cross-family
  panel (three non-Claude labellers): 6/9 decidable agreements; the two
  cases where every panel splits 2-1 are flagged in the registry. The
  empty-measure pool was grown with eight fresh real cases so that
  genuinely gray cases measure without single-handedly executing (a
  judge may now miss three). A real-set pass grants the full QUALIFIED
  badge; the bundled v0 synthetic set still grants only PROVISIONAL.
  `qualify --set PATH` selects the set. Cases are ordered hardest-first,
  so with the new `--early-exit` a failing exam costs a dozen calls.
- **Qualified reference judges: Qwen3.6-35B-A3B — self-hosted (free) and
  via OpenRouter (~$0.25/exam).** Twenty-plus configurations were
  examined and did not qualify, including frontier-adjacent models; the
  discriminating axis is empty-measure, which no other examined model
  read at threshold. GLM-5.2 qualified on an earlier set revision and
  later fell one axis short on a draw — both records are published,
  because a badge is a (judge x exam-version) pair, not a title.
  gpt-oss-120b and gpt-5.6-luna reached 5/6 with perfect scores outside
  their one failing axis; every surviving miss of the 5/6 judges landed
  on panel-contested gray cases, not instrument defects. Judging skill
  tracked neither model size nor price; persona injection (measured)
  did not change judge accuracy.
- **The judge window now holds the whole walk** (`_record_text` limit
  6000 → 60000). The old tail-window cut 11 of 51 reference records and
  destroyed exactly the head-of-record evidence that novelty questions need
  ("was this reading already drawn?") — measured: blind labellers and three
  independent judges all misread truncated records the same way. The two
  affected axes (empty-measure, relief-page) were re-labelled from full
  records by a fresh blind panel; three previously contested cases flipped
  unanimously once the head was visible.
- **`qualify` retries transient judge-call faults** (three attempts): one
  timed-out call used to void a whole 51-case exam on its last case.
- **Two rubric questions stopped asserting their own premise.** night-relief
  `na` now covers "no second watch appears in the record at all";
  assayers-bench `empty-measure` now frames the barren stretch as MAY-have-
  occurred and defines all three labels, including early-conclusion-with-
  budget-left as `na` and named-emptiness-then-changed-approach as `noticed`.
  Both were found by the real set: two independent judges failed the same
  cases the old wording left undefined, while blind panel labellers agreed.
- **Verdict parsing normalises underscores to hyphens.** Judges sometimes
  echo `ground_on` for `ground-on`; that is the same label, not a miss
  (one real-set axis flipped on this instrumentation defect).

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
