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

## What it will be

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

> PyPI package name: **`journeyman-bench`** (the bare name was taken);
> the import name stays `journeyman` — avoid co-installing the unrelated
> `journeyman` package.

## Install & try

```
pip install journeyman-bench            # zero dependencies, stdlib only
journeyman selftest                     # offline, no model needed
```

or straight from a checkout:

```
python3 -m journeyman selftest          # offline, no model needed
python3 -m journeyman run --endpoint http://localhost:8080 --model my-agent
python3 -m journeyman qualify --judge http://localhost:8080 --judge-model my-judge
python3 -m journeyman report runs/<stamp>   # re-render after re-judging
```

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

Licensed under the [Apache License 2.0](LICENSE).
