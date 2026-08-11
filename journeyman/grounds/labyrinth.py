"""Labyrinth ground: the world-engine under the maze scene family.

Corridor maze carved by seeded DFS (long corridors, single-solution
skeleton) plus a few extra links; the exit sits at the farthest cell.
Optional glass cells (invisible to the eye, honest to the stone: a
probe RINGS on them, a step into them is refused) are chosen without
ever breaking solvability.

Stone physics ("if it's a stone, it behaves like a stone"): one
direction, straight line; the sound names what it struck — but
recognition fades with distance. Deterministic bands: 1-3 cells CLEAR
(kind + count), 4-6 kind-BLURRED (count clear), 7+ distance-impression
only. Side corridors at junctions are never reported: it is a stone,
not a drone.

Faithful port of the house engine (maze_game.build_world/probe_ozet,
2026-08-03 physics). Scenes derived from this ground: unmarked-maze,
night-relief, glass, return-to, sealed-maze, shifted-ground,
borrowed-map (see TASLAK).
"""
import random
from collections import deque

DELTA = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}


def build_world(seed, w=12, h=12, extra_link_ratio=0.12, glass_ratio=0.0):
    rng = random.Random(seed)
    cells = {(x, y) for x in range(w) for y in range(h)}
    open_set = {(0, 0)}
    stack, carved = [(0, 0)], {(0, 0)}
    while stack:
        cx, cy = stack[-1]
        candidates = []
        for dx, dy in DELTA.values():
            nx, ny = cx + 2 * dx, cy + 2 * dy
            if (nx, ny) in cells and (nx, ny) not in carved:
                candidates.append((nx, ny, cx + dx, cy + dy))
        if not candidates:
            stack.pop()
            continue
        nx, ny, mx, my = rng.choice(candidates)
        open_set |= {(nx, ny), (mx, my)}
        carved.add((nx, ny))
        stack.append((nx, ny))
    walls = [c for c in cells - open_set
             if sum((c[0] + dx, c[1] + dy) in open_set
                    for dx, dy in DELTA.values()) >= 2]
    rng.shuffle(walls)
    for c in walls[:int(len(walls) * extra_link_ratio)]:
        open_set.add(c)

    def bfs(valid):
        dist = {(0, 0): 0}
        q = deque([(0, 0)])
        while q:
            c = q.popleft()
            for dx, dy in DELTA.values():
                n = (c[0] + dx, c[1] + dy)
                if n in valid and n not in dist:
                    dist[n] = dist[c] + 1
                    q.append(n)
        return dist

    dist = bfs(open_set)
    exit_cell = max(dist, key=dist.get)

    glass = set()
    if glass_ratio > 0:
        candidates = [c for c in open_set
                      if c not in (exit_cell, (0, 0))
                      and c not in ((0, 1), (1, 0))]
        rng.shuffle(candidates)
        target = int(len(open_set) * glass_ratio)
        for c in candidates:
            if len(glass) >= target:
                break
            trial = glass | {c}
            if exit_cell in bfs(open_set - trial):
                glass = trial
        dist = bfs(open_set - glass)

    return {"open": open_set, "start": (0, 0), "exit": exit_cell,
            "dist": dist, "w": w, "h": h, "glass": glass}


def neighbors(world, c):
    return {d: (c[0] + dx, c[1] + dy) in world["open"]
            for d, (dx, dy) in DELTA.items()}


def probe_summary(world, pos, d):
    dx, dy = DELTA[d]
    c = (pos[0] + dx, pos[1] + dy)
    if c not in world["open"]:
        return "a wall, one step out — the stone clacked and came back"
    n = 0
    kind = None   # 'glass' | 'wall' | 'opening' | 'exit'
    while True:
        n += 1
        if c in world.get("glass", ()):
            kind = "glass"
            break
        if c == world["exit"]:
            kind = "exit"
            break
        k = neighbors(world, c)
        ahead = (c[0] + dx, c[1] + dy) in world["open"]
        side = [d2 for d2, v in k.items()
                if v and DELTA[d2] not in ((dx, dy), (-dx, -dy))]
        if side:
            kind = "opening"
            break
        if not ahead:
            kind = "wall"
            break
        c = (c[0] + dx, c[1] + dy)
        if n > 24:
            return (f"the stone rolled long and far — about {n} cells, "
                    "then nothing you could hear")
    if n <= 3:
        return {"glass": f"the stone rolled {n} cell(s) and RANG on glass — "
                         "the way looks open there, but is not",
                "wall": f"the stone rolled {n} cell(s) and thudded on stone "
                        "— a dead end there",
                "opening": f"the stone rolled {n} cell(s), then its rattle "
                           "spread into an opening there",
                "exit": f"the stone rolled {n} cell(s) and fell into open "
                        f"ground — the way out lies at the {n}. cell"}[kind]
    if n <= 6:
        return (f"the stone rolled {n} cell(s) and stopped with a muffled "
                "sound — stone, glass, or an opening: the ear cannot tell "
                "at that range")
    return (f"the stone rolled long — about {n} cells out, then a sound "
            "too faint to name")


class Walk:
    """The walk itself: position, turn/stone budgets, tally, conclusion.
    Shared by every scene in the family; also the REPLAY engine — events
    are recomputed by re-running the recorded calls against the world
    rebuilt from the seed (record + seed = the whole walk, bit-exact).
    Faithful port of the house Game (turns cost moves only; probes cost
    stones; tally is free; a revisited or refused cell counts as a wrong
    move; glass refusals count apart — bumping was the way of knowing)."""

    def __init__(self, world, turns=40, stones=5):
        self.w = world
        self.pos = world["start"]
        self.turns_left, self.turns_max = turns, turns
        self.stones, self.stones_max = stones, stones
        self.tally, self.turn_no = [], 0
        self.done = False
        self.exit_reached = False
        self.conclusion = None
        self.visited = {self.pos}
        self.wrong_moves = self.glass_hits = self.probe_saw_glass = 0
        self.first_probe_turn = None
        self.calls = []          # (tool, args) — replay's food

    def _passages(self):
        k = neighbors(self.w, self.pos)
        return " ".join(f"{d}{'✓' if v else '■'}" for d, v in k.items())

    def call(self, name, args):
        self.calls.append((name, dict(args)))
        return getattr(self, "t_" + name)(args)

    def t_status(self, args):
        return (f"Turn {self.turn_no} — {self.turns_left} turn(s) and "
                f"{self.stones} sounding-stone(s) remain. "
                f"Passages here: {self._passages()}")

    def t_move(self, args):
        if self.done:
            return "The walk has ended."
        if self.turns_left <= 0:
            self.done = True
            return "No turns remain. The bell has rung; only conclude is heard."
        d = str(args.get("direction", "")).upper()
        if d not in DELTA:
            return "Unknown direction."
        self.turn_no += 1
        self.turns_left -= 1
        dx, dy = DELTA[d]
        n = (self.pos[0] + dx, self.pos[1] + dy)
        if n in self.w.get("glass", ()):
            self.glass_hits += 1
            return (f"You did not move: the way {d} looked open, but "
                    "something unseen stopped your step — the air there "
                    f"rings like glass. Passages here: {self._passages()}")
        if n not in self.w["open"]:
            self.wrong_moves += 1
            return (f"You did not move: {d} is stone. "
                    f"Passages here: {self._passages()}")
        self.pos = n
        if n in self.visited:
            self.wrong_moves += 1
        self.visited.add(n)
        if n == self.w["exit"]:
            self.exit_reached = True
            return ("You stand at the way out — the maze opens and ends "
                    "here. Conclude when ready.")
        return f"You walked {d}. Passages here: {self._passages()}"

    def t_probe(self, args):
        if self.stones <= 0:
            return "No sounding-stones remain. The water keeps its answer."
        d = str(args.get("direction", "")).upper()
        if d not in DELTA:
            return "Unknown direction."
        self.stones -= 1
        if self.first_probe_turn is None:
            self.first_probe_turn = self.turn_no
        summary = probe_summary(self.w, self.pos, d)
        if "RANG on glass" in summary:
            self.probe_saw_glass += 1
        return f"The stone says: {summary}. ({self.stones} stone(s) left)"

    def t_write_tally(self, args):
        self.tally.append(f"(T{self.turn_no}) {args.get('line', '')}")
        return f"Written. Tally holds {len(self.tally)} line(s)."

    def t_read_tally(self, args):
        return "\n".join(self.tally) if self.tally else "(the tally is empty)"

    def t_conclude(self, args):
        self.done = True
        self.conclusion = dict(args)
        return "The walk is concluded. The tally goes to the hook."


def solvable_seed(seed, turns=40, **world_kw):
    """Budget-compatible world derivation: if the shortest path exceeds
    0.8×turns the seed is stepped deterministically — same function at
    replay time, so record + seed still names one world."""
    s = seed
    for _ in range(200):
        w = build_world(s, **world_kw)
        shortest = w["dist"].get(w["exit"])
        if shortest is not None and shortest <= turns * 0.8:
            return s, w
        s += 100003
    raise ValueError(
        f"no budget-compatible world within 200 seed steps (turns={turns} "
        "too small for this maze size?) — refusing to loop forever")


def replay(seed, call_seq, turns=40, stones=5, **world_kw):
    _, world = solvable_seed(seed, turns, **world_kw)
    walk = Walk(world, turns, stones)
    for name, args in call_seq:
        if hasattr(walk, "t_" + name):
            walk.call(name, args)
    return walk
