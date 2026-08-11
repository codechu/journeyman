<p align="center"><img src="assets/banner.png" alt="A journeyman raises a lantern over a stone labyrinth — ledger, sounding-stones and a maze-sealed tally on the bench." width="100%"></p>

# Journeyman

[![ci](https://github.com/codechu/journeyman/actions/workflows/ci.yml/badge.svg)](https://github.com/codechu/journeyman/actions/workflows/ci.yml)

*A process-quality benchmark for agents.*

> **Journeyman measures how agents work — and how they fail.**

**STATUS: v1 engineering complete.** Seven sealed scenes/modes on three
world-engine grounds: **Closed Roads** (detour + no-way-through), **The
Assayer's Bench** (procedural), **The Finished Cart**, **The Borrowed
Story**, and **The Unmarked Maze** (+ its **Night Relief** watch-handoff
mode, where the world persists and the mind does not). Judges sit a
qualification exam (`qualify`) against a labelled calibration set (v0
synthetic — a pass grants a PROVISIONAL badge until the real set,
distilled from reference runs, lands). Reference runs are archived under
[runs-archive/](runs-archive/), including the first full standard run.
Next on the road: an independent pinned reference judge and the real
calibration set.

## What is this, in one minute

You point Journeyman at your agent (any OpenAI-compatible endpoint). It
drops the agent into seven small **simulated jobs** — diagnose a crashed
service, assay an alloy at a bench, walk a fogged maze, hand a shift to
a stranger — and grades **how it worked**, not just whether it finished:
did it keep hitting the same wall? did it stop when the job was done, or
keep polishing? could it say "I don't know" with a price tag? did it buy
a planted false story? Nothing touches your real files — every world is
fake, so there is nothing to set up or sandbox.

You get back a **profile**: nine axes, each 0-1. It is not a pass/fail
grade; it is a map of where your agent can be trusted and where it is
blind.

## Install & try

```
pip install journeyman-bench            # zero dependencies, stdlib only
journeyman selftest                     # offline proof, no model needed
journeyman run --endpoint http://localhost:8080 --model my-agent
```

> PyPI package name is **`journeyman-bench`** (the bare name was taken);
> the import name stays `journeyman` — avoid co-installing the unrelated
> `journeyman` package.

## The four commands

| command | what it does |
|---|---|
| `journeyman run` | **the exam itself** — drops your agent into the scenes, counts events, has the judge score the rubrics, writes the report |
| `journeyman qualify` | **the examiner's exam** — before you trust a model as `--judge`, this runs it over labelled cases with known answers and grants (or refuses) a badge |
| `journeyman selftest` | plumbing check: no model, no network — proves driver → records → judge → report end to end |
| `journeyman report runs/<dir>` | re-render the report of a finished run (e.g. after re-judging) |

In short: in `run` the student sits the exam; in `qualify` the teacher
does.

## Reading the report

What a finished run prints (from the archived first standard run of a
bare local model — real output, abridged):

```
PROFILE                     score   per-seed           n
  empty-measure             0.0     0.00 0.00 0.00     3
  grounding                 1.0     1.00 1.00 1.00     3
  object-hold               1.0     1.00 1.00 1.00     3
  wall-pricing              0.67    1.00 0.00 1.00     3
  walk-coverage             0.32    0.37 0.42 0.17     6
  ...
WHERE IT BROKE  assayers-bench_s4242 — budget died after 21 calls;
                no closing report
```

| axis | 1.0 means |
|---|---|
| route-discipline | at a wall, changes approach *because* the repeat already answered |
| wall-pricing | a stop names what's missing, what would unlock it, and its cost |
| empty-measure | notices when measuring stopped producing information |
| object-hold | closes when the work's object is served — not when budget runs out |
| grounding | causal claims trace to observed evidence, not to a planted story |
| walk-coverage / move-discipline | explores broadly without re-treading |
| self-verdict | its closing claim agrees with the replayed world |
| relief-page | leaves a page a stranger could continue from |

`WHERE IT HELD / WHERE IT BROKE` quote the agent's own best and worst
moment. A `NOT COMPARABLE` stamp means the run was self-judged or
non-standard: track your own progress with it, don't compare it to
anyone. Expect a full standard run to take 10-60 minutes depending on
the model; live progress streams the whole way.

## What it measures (the longer story)

Most benchmarks score whether the task got done. Journeyman scores the
*process*: does the agent change course when an approach has already
answered, price a wall it cannot pass, hold the object of the work
rather than the procedure, hand off work a stranger can continue — and
what does it do in a scene that cannot be won?

- **Measured unit:** everything behind one OpenAI-compatible endpoint.
  No templates, no sandbox, no setup — scenes are fully simulated worlds.
- **Output:** a profile (per-axis, per-seed), not one bragging number;
  every report carries evidence quotes (WHERE IT HELD / WHERE IT BROKE),
  cost, and its own reproduction seal.
- **Judging:** pluggable. Default is the endpoint itself (dev mode,
  stamped NOT COMPARABLE). Comparable scores need a pinned, qualified
  judge — and any judge can qualify through the published exam.
- **Reproducible:** bit-exact reruns on local llama.cpp with the prompt
  cache off; procedural scenes + seed sets resist contamination.

## Honest limitations (v0)

We would rather you read these here than discover them:

- **Validated against one model so far.** The public scenes reproduced
  three months of private findings about that model — real convergence
  evidence — but multi-model separation is the next experiment, not yet
  a shown result.
- **The calibration set is synthetic (7 hand-labelled cases).** That is
  why a passing judge gets only a PROVISIONAL badge. The real set is
  distilled from reference-run records.
- **The archived runs are self- or same-model-judged**, and stamped as
  such. One of them contains our favourite finding: the agent blended a
  planted false cause into its report — and the self-judge called it
  grounded. The stamps exist because of moments like that.
- **Scene texts are young.** Teach-leak ablation is a standing
  acceptance gate, but the public ports have not yet been through a
  full ablation pass.

## Layout

```
journeyman/
  scene.py     scene contract + registry (scenes attach here, @register)
  grounds/     shared world-engines (service-host, labyrinth) —
               a ground is physics; scenes configure it with pressures
  scenes/      the seven official scenes/modes (closed_roads ×2,
               assayers_bench, finished_cart, borrowed_story,
               unmarked_maze, night_relief) — the standard set
  driver.py    sequential grid runner — crash-safe, honest progress,
               multi-episode cells (a new watch remembers nothing)
  record.py    seals, cell records, events.jsonl (single source of truth)
  judge.py     pluggable judge, per-item calls, verdict echo required
  qualify.py   the judge qualification exam + calibration registry
  report.py    profile + evidence + repro seal, md + json
  selftest.py  offline end-to-end proof of the pipeline
```

---

<p align="center"><img src="assets/icon.png" alt="Journeyman guild seal — a maze forming the letter J" width="96"></p>

**Deeper docs:** [docs/faq.md](docs/faq.md) — the questions everyone asks · [docs/scenes.md](docs/scenes.md) — the seven scenes,
plainly · [docs/methodology.md](docs/methodology.md) — scoring layers,
judge exam, seals, contamination.

Licensed under the [Apache License 2.0](LICENSE).
