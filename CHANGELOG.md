# Changelog

## Unreleased

- Judging phase metered: calls, tokens and the provider's charge land in
  `report.json` as `judge_cost`.
- Keys read from `$JOURNEYMAN_API_KEY` / `$JOURNEYMAN_JUDGE_API_KEY`.

## 0.1.2 — 2026-08-28

- **Version stamp corrected.** 0.1.1 shipped with `pyproject.toml` bumped and
  the other three version records left at 0.1.0, so a report produced by that
  release carried `bench: "0.1.0"` in its seal — a run stamped with a version
  that did not produce it. The repository's own drift guard catches this; it
  was run after the tag rather than before, which is the whole reason the
  guard exists. 0.1.1 should not be used for anything whose provenance
  matters. No behaviour change beyond the stamp.

## 0.1.1 — 2026-08-28

- **An endpoint given as `.../v1` now reaches the model.** `list_models` had
  always accepted a bare host, a `/v1`, or a full `/v1/chat/completions`;
  `Endpoint` appended the path blindly, so `--endpoint https://host/api/v1`
  passed the model listing and then 404'd on every call. Because a cell that
  404s is invalid rather than fatal, the run completed and reported nothing —
  which reads as a model that said nothing, not as a URL never reached. Same
  normalisation as `list_models`, with a test for each of the three shapes.

## 0.1.0 — 2026-08-26

**Breaking:** `kind` is required in every axis entry of `report.json`, so a
report written by an earlier version does not validate against the current
schema. Pre-1.0 the minor digit is where a break goes (see
[versioning](docs/versioning.md#semantic-versioning)) — the major digit is
reserved for the 1.0 stability promise, which this is not. The bump is the
warning; `journeyman upgrade` is the fix.
- **`report.json` now says how each axis was scored.** Every axis carries
  `kind: "counted" | "judged"` — counted means computed from replayed events
  with no judge involved, judged means a model answered the rubric question.
  Schema change: `kind` is required in each axis entry, so reports produced
  before this release do not validate against the current schema.
  *Why:* the distinction existed in the data (a cell keeps counted axes under
  `event_axes` and judged ones under `verdicts`) but did not survive into the
  report, and the report is the surface we ask integrators to build against.
  Measured before shipping (13 sampled runs per arm, local model, gate frozen
  first): asked to classify the three counted axes from today's report, the
  reader scored 0/3 in 8 runs, 2/3 in 5, and 3/3 in none; with `kind` present
  it was 3/3 in all 13. The second half of that is close to tautological — the
  field names the answer — so the load-bearing half is the first: today's
  report does not let a careful reader get this right.
- **`report.json` carries `schema_version` (integer, now 1).** An integrator
  cannot branch on the release number — the package moves for reasons that
  never touch the report — so the contract now names its own version, bumped
  only when the shape changes in a way that can break a reader. `upgrade`
  stamps it too, but only when it could finish: a report with axes it could
  not classify is left unstamped rather than declared conformant.
- **The version-drift guard covers `journeyman/__init__.py`.** It watched
  `pyproject.toml`, `CITATION.cff` and `.zenodo.json` but not the module that
  `--version` prints and that every seal records — this release's bump missed
  it, and the package would have sealed runs as 0.0.11.
- **A way back for old reports.** `journeyman upgrade <report.json>` backfills
  `kind` without a model, a run, or a network call: an axis a scene declares
  but its rubric never asks about is computed from events, so it is counted.
  Axes it cannot place — a `nonstandard` run with custom scenes — are named
  and left alone, and the command exits non-zero rather than guessing; a guess
  is exactly the flattening the field exists to prevent. When the run
  directory still exists, prefer `journeyman report <run_dir>`: it re-renders
  from the cells, where the two layers were always separate.
- **Docs follow the same split.** The cell-record field list (`record.py`,
  `docs/run-guide.md`) was stale and omitted `event_axes` entirely; the axis
  table in `docs/scenes.md` gained a `kind` column; `docs/methodology.md`
  states that `report.json` is an aggregate profile and points per-case
  consumers at `cells/<id>.json`.
- **The schema claim is now true.** `docs/methodology.md` said the schema was
  "validated against real runs in CI"; nothing validated it. CI is stdlib-only,
  so a targeted conformance test now checks required keys, the `kind` enum,
  and that counted and judged axes come out labelled correctly — and the
  sentence was rewritten to describe exactly that, not more.

## 0.0.11 — 2026-08-24
- **Citable.** `CITATION.cff` (so GitHub offers "Cite this repository") and
  `.zenodo.json` (so an archived release carries our own title, abstract,
  author and license instead of guessed ones). The repository is linked to
  Zenodo from this release on, which mints a DOI per release.
- **A guard against stale citations.** Both files carry a version, and a
  citation record naming the wrong release is worse than none — the export
  now compares them against `pyproject.toml` and stops if they disagree.

## 0.0.10 — 2026-08-24
- **Package metadata, given its due.** The PyPI page was thin because we had
  declared little, not because anything was broken: one project URL, a legacy
  license table, five keywords. The summary now says what the thing is in the
  words people search (LLM agents, process quality, LLM-as-a-judge), the
  keyword list matches the repository's own topics, and the classifiers add
  Python 3.14, OS Independent, Quality Assurance and a research audience.
  Nothing about the code changed.
- **A claim the CI now backs.** Declaring Python 3.14 support means testing
  it: 3.14 joins the CI matrix (3.10–3.14).

## 0.0.9 — 2026-08-24 — "what the rubric was not saying"
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
- **The same fix in its other homes.** The refused-call sentinel and the
  answered-calls helper now live in `record.py`, and every layer that
  reads a record uses it: the bench scene's own event reconstruction (a
  refused assay counted as an assay, a refused conclude as a conclusion),
  the deterministic evidence block, and the maintainers' mechanical
  empty-measure counter. Measured impact of these three: no archived cell
  and no shipped label changes — they were latent, not active.
- **Calibration set v2_real grew to 82 cases and had its key corrected
  twice.** Revision 2.1: the four cases whose only closing report the
  scene refused were relabelled to the unfiled branches (grounding `na`
  x2, wall-pricing `none` x2) — they were the calibration half of the
  refused-call bug above, and every earlier exam score on those two axes
  is superseded. Revision 2.2: with those four relabelled, unfiled-report
  cases made up 25% of grounding and wall-pricing against about 8% in
  real records, so twelve fresh cases with FILED closing reports were
  harvested from cohort-1 records and labelled by the same three-family
  council (11 of 12 unanimous); both axes now hold 14 cases, 14% unfiled.
  Revision 2.3: one harvested case was relabelled `unpriced` -> `none`
  after all four examined judges read it the same way against the key —
  the house rule is that when every strong judge disagrees in the same
  direction, the key gets examined, not the judges.
- **Rubric v2.4: the sentence we had not written.** The refused-call
  clause described only the negative ("a call answered with 'budget
  exhausted' was refused") and never said what a *filed* report looks
  like, so a judge reading a complete-looking report text had nothing to
  check it against. Three axes (grounding, wall-pricing,
  handoff-verification) now also state the positive marker: the scene
  answers a filed report with "(report filed — job closed)". No label
  changed; only the question text. The prediction was frozen before the
  re-run and held: a judge that had been failing grounding at 0.71 went
  to 0.86 and a badge, the control judge went from 0.93/0.92 to 1.00 on
  every axis, and the self-hosted judge went from failing both axes to
  0.93/0.93. What we had written up as "two hard axes" was a quiet rubric.
- **Four qualified judges, two of them local and free.** Under v2.4 the
  ledger holds GLM-5.2 (1.00 on all seven axes), GPT-5.6-Luna, and the
  self-hosted Qwen3.6-35B-A3B in two forms — the stock open-weights build
  and the same weights behind a sealed character prompt. Both local rows
  qualify; the badge was earned by the missing sentence, not by the
  persona, which holds a steady +0.06/+0.07 on the three axes that need a
  call and loses nothing elsewhere (one run each, noise band unmeasured).
- **The sentence did not reach every judge.** Claude Sonnet 5 sat the
  same set as a control (hors concours — it sat on the labelling council,
  so it holds no badge whatever it scores) and did not qualify: grounding
  0.79, wall-pricing 0.79. Three of its six decisive misses are records
  whose only closing report the scene refused, and it read all three as
  filed, one of them identically in all three draws; the other three run
  the opposite way (filed reports read as unfiled or underpriced). So the
  quiet-rubric finding stands for three judges and stops at the fourth:
  what is left there is a real difference between judges, not our text.
- **The leaderboard re-judged under v2.4 by a local, free judge.** The
  same eleven agents' cell records — nothing re-run — scored by the
  self-hosted Qwen3.6-35B-A3B IQ4_XS build now that it holds the badge
  again. Rank correlation with the v2.2/luna board is 0.72. Two axes
  moved and they moved opposite ways (grounding +0.24 mean across
  agents, wall-pricing −0.23), while handoff-verification — also edited
  by v2.4 — did not move on a single agent. Judge and questions had
  changed together, so the cells were judged a third time (same judge,
  v2.2 questions restored from git) to fill the 2×2, with predictions
  frozen first: **the wall-pricing collapse is the rubric** (−0.40 from
  the questions under a fixed judge, 7 of 10 agents; +0.17 from the judge
  under fixed questions) and **the grounding rise is the judge** (+0.31
  from the judge, −0.06 from the questions). handoff-verification moved on
  no agent in either comparison — the null control held — while object-hold
  changed on 6 of 11 with a mean of zero, i.e. real single-draw noise on
  that axis; noise here is axis-dependent and no per-axis band is measured.
  Earlier boards are superseded, not deleted.
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
