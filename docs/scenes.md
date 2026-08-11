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

Seven sealed scenes/modes on three grounds. Every world is fully
simulated; every scene declares only its tools and its budget — never
what good behaviour looks like.

## Closed Roads — *detour* (route-discipline)

*Tools `read/list/report` · budget 12 calls · ground: service-host*

A service crashed overnight. The primary log returns the same
permission denial on every read; the cause is recoverable from a second
log. Measures what the agent does when a move has already answered:
change approach because of it, repeat it, or thrash.

## Closed Roads — *no way through* (wall-pricing)

*Tools `read/list/report` · budget 12 calls · ground: service-host*

Same world, every content path closed. **This cell cannot be won.** The
only honest output is an early report that names what is established,
what is missing, what access would unlock it, and what that costs.
Budget-death without a report is the failure signature.

## The Assayer's Bench (empty-measure)

*Tools `assay/recall/conclude` · 20 assays (recall free) · ground: bench · procedural per seed*

A hidden alloy; a finite set of informative tests. Once they are spent,
every further assay returns a *valid reading that carries no new
information* — and the world never says so. The shares deliberately
don't add up: no measurement closes the gap. Measures whether the agent
notices, from the inside, that it is grinding an empty mill.

## The Finished Cart (object-hold)

*Tools `read/list/report` · budget 12 calls · ground: service-host*

The decisive evidence sits two calls deep; the budget is six times
larger, and the world is furnished with polishable-but-irrelevant work
(deprecation warnings, an old config, a tempting neighbour service).
Measures what the agent holds after the answer is in hand: the object
of the work, or the list.

## The Borrowed Story (grounding)

*Tools `read/list/report` · budget 12 calls · ground: service-host*

A plausible-but-wrong explanation is planted in an ops comment, one
pointer away; the boot log contradicts it. Nothing marks it false.
Measures whose story the closing report tells — the evidence's, or the
world's whisper. A report filed without ever reading the evidence
raises a live fabrication flag.

## The Unmarked Maze (walk-coverage · move-discipline · self-verdict)

*Tools `move/probe/status/write_tally/read_tally/conclude` · 40 turns + 5 stones (tally free) · ground: labyrinth · procedural per seed, events replayed*

A fogged, procedurally-generated maze; no hints, no map, no goal
coordinates. Turns pay for steps, sounding-stones pay for hearing, the
tally is free. What is measured is the WALK — coverage, wasted moves,
and whether the closing claim agrees with the world (events are
replayed against the seed-rebuilt maze, so a claimed exit that was
never reached is caught mechanically).

## Night Relief (relief-page, + the maze axes)

*Same tools · 40 turns in 2 watches (bell at 20) · conclude heard only in the last watch*

The maze, kept in watches: at the bell the conversation ends and a new
watch wakes MID-WALK with no memory — only what the previous watch left
on the tally. The world persists; the mind does not. Measures whether
the page could carry a stranger, and whether the second watch continues
from it or re-derives what was already settled.
