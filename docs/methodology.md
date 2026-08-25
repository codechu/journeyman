# Journeyman — Methodology

> *Journeyman measures how agents work — and how they fail.*

## What is measured

The unit under measurement is **everything behind one OpenAI-compatible
endpoint**: model, quantisation, sampling, system prompt, scaffolding.
Journeyman sends only messages, tools, the model name, and a seed; an
optional `--system-file` and `--params-file` are part of the *agent
definition* and enter the seal. Nothing else crosses the wire.

Most benchmarks score whether a task got done. Journeyman scores the
**process**: what the agent does when an approach has already answered,
when a wall cannot be passed, when the work is finished early, when the
world whispers a plausible story the evidence contradicts, when the
watch changes hands — and what it does in a cell that cannot be won.

## Scenes, grounds, modes

- A **ground** is physics: a simulated world-engine — [service-host](grounds/service-host.md), [bench](grounds/bench.md), [labyrinth](grounds/labyrinth.md) (service-host: file
  trees; the assay bench; the labyrinth). Everything the agent touches
  is simulated — no sandbox, no containers, by design.
- A **scene** configures a ground with one pressure (Closed Roads, The
  Finished Cart, The Borrowed Story, The Assayer's Bench, The Unmarked
  Maze).
- A **mode** is a registered dial-setting of a scene (detour /
  no-way-through; Night Relief). Every mode is sealed and calibrated
  separately.

Scenes declare only the **vocabulary** (tools) and the **price**
(budgets). A scene never describes good behaviour: the teach-leak
ablation — remove a sentence, rerun, see whether the behaviour was
discovered or taught — is part of scene acceptance, permanently.
A scene on which every agent scores 1.0 is a broken scene, not a good
cohort.

## Two scoring layers

1. **Events** — facts only, computed programmatically from the record:
   calls, walls hit, budgets died, which sources were read, whose story
   the report carries. Maze-family events are **replay-based**: the
   world is rebuilt from the seed and the recorded calls are re-run —
   record + seed name one walk, bit-exact. A claimed exit that was
   never reached is caught by the replay, not by an opinion.
2. **Judgment** — the questions no counter can answer (was the route
   change *informed*? is the wall *priced*? is the story *borrowed*?)
   go to a judge, one small call per rubric item, verdict echoed from a
   published label set. Unparsed verdicts are never silently kept.

## Judges take the exam too

The judge is pluggable. The default is the endpoint itself — zero
setup, and the report is stamped **NOT COMPARABLE** in capitals,
because self-judgment is measurably lenient (our first archived live
run contains a report that blends a planted false cause into its
conclusion — and the self-judge called it grounded).

Comparable scores require a judge that has passed the **qualification
exam**: every rubric item answered over a labelled calibration set,
per-item accuracy published beside the verdicts. The v0 synthetic set
grants only a PROVISIONAL badge. The real set — currently **v2_real, 70
cases across all seven judged axes** — is distilled from reference-run
transcripts: each case is the full record exactly as the judge will
see it.

**How v2 labels were made (the second labelling, 2026-08-23).** Not by
vote. A council of three model families (claude-sonnet-5, kimi-k2,
grok-4.3) labelled every case in a blind round — label plus one
verbatim quote, no deliberation budget — then saw each other's
label-and-quote anonymously and answered once more; every change of
mind was logged with its reason and classified by a blind auditor as
evidence-driven or conformity (16 of 18 were evidence-driven; a fourth
reader that flipped 4/4 by conformity on the pilot was dropped). A
label is sealed only when at least two families support it; two
cases the council split were ruled by the maintainer; empty-measure is
labelled mechanically, because its v2 definition counts barren
readings rather than interpreting them. The rubric questions
themselves went through the same council first — three rounds at
most, then sealed — which is why they are published verbatim and
shared by the exam, the judge and the scene pages. Round-by-round
records are kept by the maintainers. The 0.8 per-axis threshold is
frozen; cases are ordered hardest-first so a failing exam exits early.
No judge — including ours — is exempt, and under v2 ours did not pass.

## Reproducibility and contamination

- Runs are **sequential by design**: concurrent batching perturbs
  local-model numerics (measured: prompt-cache reuse alone breaks
  bit-level reproducibility; with the cache off, a 15-turn ceremony
  reproduced bit-exact, name included).
- Every report carries its **seal**: bench version, per-scene source
  md5, seeds, model, agent-system md5, agent params verbatim — and its
  own reproduction command. On a local llama.cpp with the prompt cache
  off, reruns are bit-exact.
- Scenes are procedural where it matters (the labyrinth and the bench
  generate fresh worlds per seed). Public seed sets let anyone verify;
  held-out seed sets arrive with the leaderboard phase.
- **Honesty clause:** a benchmark that becomes famous becomes a
  curriculum. Procedural worlds, held-out seeds and process-trace
  scoring slow that decay; nothing stops it. This clause ships with
  every report.

## Reports

Profile first (per-axis, per-seed, n visible), composite only when its
weights are grounded in measurement. Evidence quotes always (WHERE IT
HELD / WHERE IT BROKE, in the agent's own words). Cost always. Stamps
always: self-judged, non-standard scenes or seeds, unreported usage.
Single-seed scores are never published as results.

## Provenance

Journeyman grew out of a private character-engineering programme for
local models, where the mechanisms here — frozen gates, blind judges, teach-leak
ablations, replay determinism, judge calibration — were first used on
our own agents. That private history is not published; what is
published is every run, exam and council record made since the port. The scenes were ported; the
calibration history was not: a port changes the scene text, and
calibration does not transfer across worlds.

## Report format & interoperability

There is no universal standard for *process-quality* agent reports. The
closest de-facto format, `lm-evaluation-harness`'s `results.json`, is
built for static task accuracy, not per-axis process profiles; OpenAI
Evals, SARIF, and experiment trackers (MLflow, W&B) all model something
else. So Journeyman's `report.json` is its own format — but a
**specified, versioned one**, not an ad-hoc dump:

- The contract is published as JSON Schema at
  `journeyman/schema/report.schema.json` (shipped in the package) and
  validated against real runs in CI.
- Every field carries provenance: the `seal` alone reproduces the run;
  `self_judged` / `nonstandard` make an un-comparable score
  self-declaring; `cost` is always present (or explicitly UNREPORTED).
- Because the shape is stable and flat, converting a report into an
  MLflow/W&B run or a leaderboard row is a few lines — the axes are
  already `{score, per_seed, n}` per metric.

If a community standard for agent process-reports emerges, mapping onto
it is a converter, not a rewrite: the measurements are the asset, the
serialization is replaceable.

## Looking for an arXiv endorser (cs.AI / cs.LG)

The write-up is in progress. What it will describe is already public and
checkable: a labelled calibration set that every judge must pass before it may
score, a [judge registry](judges.md) that publishes the judges which
failed as prominently as the ones that passed, a
[leaderboard](leaderboard.md) whose numbers are generated by script from
sealed runs, and an ablation separating how much of a verdict came from the
rubric rather than the agent. Releases are archived with a DOI
([10.5281/zenodo.22085820](https://doi.org/10.5281/zenodo.22085820)).

arXiv requires an endorsement for a first submission in a category, and we
have no institutional affiliation to bypass it. If you publish in this area
and think the work is worth endorsing, please open an issue — and if you read
it and think it is not, that is useful to hear too.

---
**Docs:** [README](../README.md) · [scenes](scenes.md) · [grounds](grounds/service-host.md) · [run guide](run-guide.md) · [FAQ](faq.md) · [methodology](methodology.md) · [versioning](versioning.md)
