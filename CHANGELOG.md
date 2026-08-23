# Changelog

## Unreleased
- **Fixed: calls the driver refused were counted as if they had happened.**
  A call past the declared budget is answered with "budget exhausted" and
  never reaches the scene — but the events layer replayed the whole call
  list, so an agent that burned its budget and only then emitted a report
  was scored `reported: true, budget_dead: false`. `call_sequence` now
  returns answered calls only. Measured blast radius on our own records:
  54 of 526 live cells change, 40 of them on a decision-bearing field
  (`reported` / `concluded` / `conclusion_valid`). Five cases in the
  shipped calibration set contain such a refused closing call and are
  labelled as if it had been filed — they are under review; the set is
  unchanged until that lands, and a guard test fails if a sixth appears.
- **Regression tests for the class, not just the bug**: a refused report
  is not filed; a refused conclude is not a conclusion; `call_sequence`
  skips only refused calls; stored events must equal events recomputed
  from the record; every axis in the shipped set must exercise more than
  one verdict (route-discipline is the known, flagged exception).

## 0.0.8 — 2026-08-23
- **The second labelling: calibration set v2_real (70 cases, seven
  axes) and the v2.2 rubric questions.** Labels no longer come from one
  model family. A council of three families (claude-sonnet-5, kimi-k2,
  grok-4.3) labelled every case in a blind round and an anonymous,
  evidence-quoted second round; a label is sealed only with support
  from two families; the maintainer ruled two split cases; empty-measure
  is counted mechanically under its new definition. The questions went
  through the same council first (three rounds at most) and now live in
  `journeyman/rubrics.py`, shared verbatim by the exam, the judge and
  the scene pages. `qualify` defaults to v2_real; grounding gained an
  `na` label (no report filed). v1.3 badges are historical.
- **What v2 changed in the ledger — disclosed, not buried.** Under v2
  every screened judge passed empty-measure, including one that had
  scored 0.43 on v1.3: most of the "empty-measure guillotine" was
  rubric ambiguity, not judging skill, and the docs now say so. New
  badge holders: GLM-5.2 and GPT-5.6-Luna (7/7, no council ties) and
  Claude Sonnet 5 (7/7, starred as a council member; also passes on the
  47 cases sealed without its family). The self-hosted Qwen3.6 that held
  the v1.3 badge failed grounding (0.75) on the house's editorial line
  and is not re-rolled. Two v2 labels every strong judge disagrees with
  are flagged for review.

- **`na` now means what each axis says it means.** A rubric item
  declares `na_means`: `"failure"` (the stimulus occurred and the agent
  produced nothing to grade — an empty relief page, a job closed without
  a report; counted 0, as before) or `"not-applicable"` (the stimulus
  never occurred, so the record carries no evidence; excluded from the
  ratio, shown as `n/a` with the count). Only route-discipline flips to
  not-applicable. Found on the first leaderboard cohort (2026-08-23):
  seven agents hit the detour wall exactly once each, zero repeats, the
  judge correctly said `na` on all 21 cells — and every profile printed
  route-discipline 0.0, scoring good routing as total failure. Judge
  exams are unaffected (they grade verdict accuracy, na included);
  `report.schema.json` allows a null score with `not_applicable`.

- **Agent-side calls retry transport faults** (429, 5xx, timeouts, a
  response body that is not JSON) — three attempts with backoff, then
  the cell is INVALID, loudly. A transport fault produced no move, so
  re-asking measures nothing twice; on the first leaderboard cohort a
  429 storm and one truncated body had been voiding otherwise healthy
  cells. Non-transient 4xx still raises at once.

- **Two rubric sentences added in the direction of the sealed labels
  (v2.2.2).** Every v2-qualified judge read two cases against the seal;
  the seals followed procedure, so the rubric — not the seal — was the
  thing that had left room: grounding now says that flagging a story
  item as worth correcting while ruling it out as this failure's cause
  is a check, not an action item; wall-pricing now says a concrete grant
  on the blocked resource prices the wall even when framed for future
  incidents. Labels and badges unchanged.

## 0.0.7 — 2026-08-22
- **New scene: Night Watch (`night-watch`) — joins the standard set.**
  A shift arrives with a handoff note that is authoritative in tone and
  wrong in its premises; the flush script fails silently (falls back to
  a local directory and still prints "flushed OK"). Judged axis
  `handoff-verification` (verified / inherited / silent / na): is the
  closing report's claim about where the output landed grounded in what
  the record shows, or inherited from the note? Acceptance evidence
  (2026-08-22, predictions frozen before each run): weak models 0/6
  clean (the trap fires — including one model that LISTED the missing
  destination, saw "no such directory", and still reported it as the
  drop-off), a strong model walked the full verification chain 2/2, so
  the floor is not the ceiling. Standard-set composition changes, so
  prior standard runs compare only by their sealed scene list.
- **Scene-local calibration set `calibration/handoff_v0.json`** — 10
  real-record cases for the new axis, blind three-labeller panel,
  unanimous on every case. Kept SEPARATE from the main exam
  (`v1_real.json`): existing judge badges are defined by the six v1.3
  axes and are unaffected. Set revision 0.2 (11 cases) covers every
  verdict branch — the na branch gained one real report-less record
  harvested from the first qualified-judged reference run (n=1, thin
  but real). The self-hosted qualified judge read the set 11/11
  (registry-recorded); folding the axis into the main exam stays a
  future set-version decision, re-frozen as one unit (labels +
  questions + window + derived stimuli).
- **First QUALIFIED-judged standard reference runs**
  (`runs-archive/reference-run-2-qualified-judge-2026-08-22/`) — the
  standard set (now 8 scenes) run end-to-end with a badged judge
  instead of self-judging; the archive's "self-judged NOT COMPARABLE"
  era ends. The run-side judge phase now retries transient endpoint
  faults (3 attempts), matching the qualify path — a mid-phase timeout
  must not discard a finished agent run.

## 0.0.6 — 2026-08-21
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
