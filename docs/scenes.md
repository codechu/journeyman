# The Scenes

## Why these seven?

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
| handoffs a stranger cannot continue | Night Relief |

One pressure per scene, so a score points at a muscle, not a blur.
Scenes declare only tools and budgets — the temptation is always
world-texture, never instruction — and a scene every agent aces is
treated as broken.

Seven sealed scenes/modes on three grounds. Each scene has its own
detailed page — world, task, trap mechanics, counted events, the
judge's question verbatim, and success/failure signatures:

- [Closed Roads](scenes/closed-roads.md) — detour & no-way-through
- [The Assayer's Bench](scenes/assayers-bench.md)
- [The Finished Cart](scenes/finished-cart.md)
- [The Borrowed Story](scenes/borrowed-story.md)
- [The Unmarked Maze](scenes/unmarked-maze.md)
- [Night Relief](scenes/night-relief.md)

Each page opens with its own illustration and walks a real transcript excerpt from an archived run.

## The three grounds

A **ground** is the physics — a simulated world-engine, written once and
shared by many scenes. A scene is that engine set to one pressure; a
mode is a dial-setting of a scene. This is the layer that lets seven
scenes cost far less than seven bespoke worlds, and where new scenes get
their footing.

- **[service-host](grounds/service-host.md)** — a stub Linux service tree explored with
  `read` / `list` / `report`. Rides it: Closed Roads, The Finished Cart,
  The Borrowed Story — three scenes, one physics, three different
  pressures (route, object-hold, grounding).
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

---
**Docs:** [README](../README.md) · [scenes](scenes.md) · [grounds](grounds/service-host.md) · [run guide](run-guide.md) · [FAQ](faq.md) · [methodology](methodology.md) · [versioning](versioning.md)
