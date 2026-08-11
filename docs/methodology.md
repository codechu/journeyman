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

- A **ground** is physics: a simulated world-engine (service-host file
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
per-item accuracy published beside the verdicts. The v0 calibration set
is synthetic and grants only a PROVISIONAL badge; the real set is
distilled from reference-run records. No judge — including ours — is
exempt.

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
local models, where every mechanism here — frozen gates, blind judges,
teach-leak ablations, replay determinism, judge calibration — was first
used in anger on our own agents. The scenes were ported; the
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
