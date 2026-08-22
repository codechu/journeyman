# The Scenes

## Why these eight?

Each scene puts pressure on ONE expensive, real failure family of
working agents — failures we spent months watching real agents commit
before any of this was a benchmark:

| failure family | the scene that filters it |
|---|---|
| hammering a wall that already answered | Closed Roads / detour |
| burning the budget rather than reporting an honest stop | Closed Roads / no-way-through |
| measuring long after measurement stopped informing | The Assayer's Bench |
| polishing past the finish because budget remained | The Finished Cart |
| repeating a plausible story the evidence contradicts | The Borrowed Story |
| wandering without coverage, claiming what the world denies | The Unmarked Maze |
| leaving a handoff a stranger cannot continue | Night Relief |
| repeating an authoritative note the world contradicts | Night Watch |

One pressure per scene, so a score points at a muscle, not a blur.
Scenes declare only tools and budgets — the temptation is always
world-texture, never instruction — and a scene every agent aces is
treated as broken.

Eight sealed scenes/modes on three grounds. Each scene has its own
detailed page — world, task, trap mechanics, counted events, the
judge's question verbatim, and success/failure signatures:

- [Closed Roads](scenes/closed-roads.md) — detour & no-way-through
- [The Assayer's Bench](scenes/assayers-bench.md)
- [The Finished Cart](scenes/finished-cart.md)
- [The Borrowed Story](scenes/borrowed-story.md)
- [The Unmarked Maze](scenes/unmarked-maze.md)
- [Night Relief](scenes/night-relief.md)
- [Night Watch](scenes/night-watch.md)

Each page opens with its own illustration and walks a real transcript excerpt from an archived run.

## The three grounds

A **ground** is the physics — a simulated world-engine, written once and
shared by many scenes. A scene is that engine set to one pressure; a
mode is a dial-setting of a scene. This is the layer that lets eight
scenes cost far less than eight bespoke worlds, and where new scenes get
their footing.

- **[service-host](grounds/service-host.md)** — a stub Linux service tree explored with
  `read` / `list` / `report`. Rides it: Closed Roads, The Finished
  Cart, The Borrowed Story, and Night Watch — four scene families on
  one physics, four different pressures: route, object-hold, grounding,
  handoff-verification. Night Watch adds a scene-local `run` for
  executable scripts.
- **[bench](grounds/bench.md)** — a measurement world: an `assay` that returns readings, a
  free `recall`, a `conclude`. The informative readings are finite and
  the world never says when they run out. Rides it: The Assayer's Bench.
- **[labyrinth](grounds/labyrinth.md)** — a seeded, procedurally-carved maze with
  `move` / `probe` / `status` / a free `tally` / `conclude`. Stone
  physics (sound fades with distance), turn/stone budgets, and a
  deterministic **replay** so a walk re-runs from its seed and record,
  exact. Rides it: The Unmarked Maze and its Night Relief mode.

New scenes usually don't need a new ground — most are a new dial on an
existing one (see [CONTRIBUTING](../CONTRIBUTING.md)). A ground of its
own is warranted only when a genuinely different physics is needed.

## Measured baselines — a floor, not a target

So a reader can place a profile: what two small models actually scored
on the full standard set, judged by a qualified judge (from the
archived
[reference run](../runs-archive/reference-run-2-qualified-judge-2026-08-22/NOTE.md),
2026-08-22 — 3 seeds per scene, so read these as coarse floors, not
rankings). A dash means every one of that model's cells on the scene
came back invalid: it narrated plans instead of calling tools, which is
itself a way to fail a process benchmark.

| axis | fed by | gpt-oss-20b | mistral-small-3.2 |
|---|---|---|---|
| route-discipline | Closed Roads / detour | 0.0 | — |
| wall-pricing | Closed Roads / no-way | 0.33 | — |
| empty-measure | Assayer's Bench | 0.67 | 1.0 |
| object-hold | Finished Cart | 0.33 | 0.67 |
| grounding | Borrowed Story | 0.67 | 0.67 |
| walk-coverage | maze family | 0.01 | 0.03 |
| move-discipline | maze family | 1.0 | 0.77 |
| self-verdict | maze family | 0.0 | 0.25 |
| relief-page | Night Relief | 0.0 | 0.0 |
| handoff-verification | Night Watch | 0.0 | 0.0 |

Two things worth noticing. No model aces the board, and the two fail
in different rows — exactly the shape a filter should have (a scene
every agent aces is treated as broken); the zeroed rows are not dead
axes, they are the hard ones, and the scene pages above show what a
positive looks like on each. And the mechanical axes (move-discipline)
sit far above the judged ones (relief-page, handoff-verification) for
the same models: walking correctly is cheap; verifying and handing off
are not. Each axis is fed by exactly ONE scene — a score points at a
muscle, never a blur — so a low row tells you precisely which page to
read.

---
**Docs:** [README](../README.md) · [scenes](scenes.md) · [grounds](grounds/service-host.md) · [run guide](run-guide.md) · [FAQ](faq.md) · [methodology](methodology.md) · [versioning](versioning.md)
