# Ground: service-host

<p align="center"><img src="../../assets/grounds/service-host.jpg" alt="A workshop wall of numbered brass file-slots — some open with scrolls, many sealed with red wax '600' locks — and a 'report' bell-pull at the end." width="100%"></p>

A stub Linux service tree the agent investigates through simulated
tools. Nothing touches a real filesystem — the whole world is a
dictionary of paths to contents, in memory.

## Vocabulary

| tool | effect |
|---|---|
| `read(path)` | returns a file's contents, or `no such file` |
| `list(dir)` | returns a directory listing, or `no such directory` |
| `report(text)` | files the closing report and **ends the cell** |

Paths are normalised: a bare name is resolved under the scene's service
root (e.g. `logs/app.log` → `/srv/app/logs/app.log`), so the agent can
be terse or absolute.

## Mechanics that matter

- **Permissions are content.** A locked file returns
  `permission denied (owner root, mode 600)` — a *readable result*, not
  an error. Whether the agent treats a denial as a dead end or a fact to
  route around is exactly what some scenes measure.
- **The report tool closes the cell.** Calling `report` sets the
  instance done; there is no "keep going after reporting." This makes
  *when* the agent reports a measured decision, not an afterthought.
- **Injected text is world-texture, never instruction.** README notes,
  config comments, deprecation warnings — a scene furnishes the world
  with tempting or misleading detail, but the ground never tells the
  agent what to do with it.

## Events it exposes

The record is a plain call sequence, so scenes compute facts by
replaying it: which paths were read and in what order, identical
repeats, whether/when `report` was called, and budget death. From these
a scene derives its own metrics (wall hits, route change, overwork
delta, evidence-vs-plant reads, …).

## Scenes on this ground

[Closed Roads](../scenes/closed-roads.md) (route-discipline &
wall-pricing) · [The Finished Cart](../scenes/finished-cart.md)
(object-hold) · [The Borrowed Story](../scenes/borrowed-story.md)
(grounding). One physics, three pressures.

---
**Grounds:** [service-host](service-host.md) · [bench](bench.md) · [labyrinth](labyrinth.md)  
[← all scenes](../scenes.md) · [README](../../README.md)
