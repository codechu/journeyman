# Vocabulary

The words that carry the rest of the documentation, ordered by how often
they do it rather than by importance. Each is defined by what the code
does with it.

- **judge** — the model that answers the rubric questions a counter cannot.
  Pluggable, and not trusted on reputation: see **qualify**.
- **scene** — one small simulated job with its own world, tools and budget.
  A scene declares what can be called and what it costs, and never what
  good behaviour looks like — a scene that describes the behaviour it is
  looking for passes everyone and measures nothing.
- **axis** — one dimension of the profile, scored 0-1. **Counted** axes are
  computed from the record by arithmetic; **judged** axes are a judge's
  label. `kind` in `report.json` says which, and mixing them silently is
  the mistake the field exists to prevent.
- **walk** — how the agent worked: the sequence of calls, stops and claims.
  This benchmark scores the walk, not whether the job came out finished.
- **cell** — one scene at one seed, and the smallest unit that gets a
  record. A cell that could not run is `invalid`, which is not a zero.
- **seal** — what a report carries so a number can be produced again: bench
  version, per-scene checksums, seeds, model, sampling params, and the
  run's own re-run command.
- **rubric** — the question put to the judge for one axis, with the fixed
  set of verdicts it may answer. The judge echoes a verdict from that set;
  free text is not a score.
- **profile** — the ten axes together. Not a pass mark and not a total:
  averaging it produces a number that means nothing.
- **qualify** — the examiner's exam. A judge runs the labelled calibration
  set before it may score, and either holds a badge or does not. The
  judges that failed are published beside the ones that passed.
- **NOT COMPARABLE** — the stamp on a run that was self-judged or used a
  non-standard scene set. Such a run is fine for tracking yourself against
  yourself; it may not be set beside anyone else's number.
- **band** — how much a score moves when nothing changes but sampling. A
  difference smaller than the band is not a difference, and a threshold
  below it reads noise.
- **held / invalid** — a cell that could not be measured is recorded as
  invalid rather than scored as zero, because an absence and a failure are
  different facts and only one of them is about the agent.
- **review score** — beside a judged axis's score: the same ratio with the
  rubric's middle label counted at 0.5. Named where printed, in no mean.
  The score still counts only the positive label.
- **verdict counts** — per judged axis, how many cells got each label; two
  agents with the same score can have failed in different ways.
- **via** — a stamp on anything measured through a CLI instead of an API:
  `QUALIFIED (via cli:claude --safe-mode)` on a judge badge, `agent_via`
  in a seal, `Agent : via …` in a report header.
- **compare / uplift** — two runs of the same agent read as a pair, usually
  without and with a system text: which axes the instruction opened, left
  low, or cost (`side effect`). `uplift` runs both arms.
- **cell records** — the per-cell transcripts and verdicts behind a report;
  the cohort's are published as `cells.jsonl.zst` beside its reports.
