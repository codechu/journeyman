# Ground: labyrinth

A fogged maze the agent walks blind, one glimpse at a time. The world is
generated from the seed, so the same seed is the same maze, bit-for-bit
— and a whole walk can be **replayed** from its seed and call record.

## Vocabulary

| tool | effect |
|---|---|
| `move(dir)` | step one cell (N/S/E/W); **costs one turn** |
| `probe(dir)` | throw a sounding-stone down a line; **costs one stone, no turn** |
| `status()` | remaining turns, stones, and the passages here — free |
| `write_tally(line)` / `read_tally()` | the agent's own record — free |
| `conclude(...)` | end the walk with a strict-shape report |

## Mechanics that matter

- **The maze is carved, not random noise.** Seeded DFS gives long
  corridors and a single-solution skeleton plus a few extra links; the
  exit sits at the farthest reachable cell. No map, no goal coordinates.
- **Stone physics — sound fades with distance.** A probe rolls straight
  and the sound names what it struck: 1–3 cells CLEAR (kind + count),
  4–6 kind-BLURRED (count only), 7+ a distance impression. Side
  corridors are never reported — it's a stone, not a drone.
- **Move accounting.** Steps cost turns; a wall bump and a re-entered
  cell each count as a wrong move; the exit announces itself. `conclude`
  demands a strict shape (`exit_found`, `path_known`, priced `unknowns`,
  `decision`).
- **Glass cells (optional mode).** Invisible to the eye, honest to the
  stone: a probe *rings* on glass, a step into it is refused — chosen so
  solvability is never broken.
- **Replay is the lie-catcher.** Events aren't parsed from prose — the
  maze is rebuilt from the seed and every recorded call is re-run
  through the same engine. So a claimed `exit_found: true` by an agent
  that never stood on the exit is caught by arithmetic, not opinion.
- **Watches (Night Relief mode).** The walk can be split into watches:
  at the bell the conversation ends and the next watch wakes mid-walk
  with no memory — only the tally carries across. The world persists;
  the mind does not.

## Events it exposes

Turns, wrong moves, stones spent, coverage (visited/open), tally
writes/reads, first probe turn, whether the conclusion is valid against
the replayed world, exit reached, priced unknowns.

## Scenes on this ground

[The Unmarked Maze](../scenes/unmarked-maze.md) and its
[Night Relief](../scenes/night-relief.md) mode.

---
**Grounds:** [service-host](service-host.md) · [bench](bench.md) · [labyrinth](labyrinth.md)  
[← all scenes](../scenes.md) · [README](../../README.md)
