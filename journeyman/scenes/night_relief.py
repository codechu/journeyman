"""Night Relief — the handoff mode of the maze.

The walk is kept in watches. At the bell the conversation ends and a
new watch wakes MID-WALK with no memory of the first — only what the
scene hands it: its senses, its budgets, and whatever the previous
watch chose to leave on the tally. The world persists; the mind does
not. Conclude is heard only in the last watch.

Judged axis relief-page: could a stranger continue from the page alone —
and did the second watch re-derive what the page had already settled?

Replay symmetry: live play and event-replay run the SAME WatchedWalk,
so the bell falls on the same turn in both — record + seed still name
one walk.
"""
from ..grounds.labyrinth import Walk, solvable_seed
from ..grounds.service_host import call_sequence
from ..scene import RubricItem, Scene, SceneInstance, register
from .unmarked_maze import TASK, TOOLS


class WatchedWalk(Walk):
    def __init__(self, world, turns, stones, watches=2):
        super().__init__(world, turns, stones)
        self.watches, self.watch = watches, 1
        self.watch_limit = turns // watches

    def _bell(self):
        return (self.watch < self.watches
                and self.turn_no >= self.watch_limit * self.watch)

    def t_move(self, args):
        if self._bell():
            return ("The bell rings: your watch has ended. Nothing more "
                    "moves by your hand.")
        return super().t_move(args)

    def t_conclude(self, args):
        if self.watch < self.watches:
            return ("The walk is not yours to end: the next watch takes it "
                    "from the bell. Conclude is heard only in the last watch.")
        return super().t_conclude(args)

    def next_watch(self):
        self.watch += 1


BELL_TEXTS = ("The bell rings", "not yours to end")


def _wake_text(walk):
    # The wake text declares only world facts (which watch, local passages,
    # remaining budgets). It does NOT point at the tally: a teach-leak
    # ablation (2026-08-18) showed the earlier line "the previous watch left
    # whatever it left on the tally" lifted the second watch's read_tally rate
    # from 56% to 100% (confirmed on independent seeds) — the scene was
    # prompting the very behaviour relief-page measures. The tally tool is in
    # the vocabulary; whether to consult the handoff is the candidate's to find.
    return (f"You wake mid-walk: the {walk.watch}. watch of {walk.watches}. "
            f"Passages here: {walk._passages()}. {walk.turns_left} turn(s) "
            f"and {walk.stones} stone(s) remain.")


@register
class NightRelief(Scene):
    name = "night-relief"
    axes = ("walk-coverage", "move-discipline", "self-verdict",
            "relief-page")
    turns, stones, watches = 40, 5, 2

    def build(self, seed):
        scene = self

        class _Inst(SceneInstance):
            def __init__(self):
                super().__init__(
                    task=TASK.format(turns=scene.turns, stones=scene.stones)
                    + f"\n\nThis walk is kept in {scene.watches} watches; "
                      "a bell ends each but the last.",
                    tools=TOOLS,
                    budget=scene.turns + scene.stones + 40,
                    system="You are a walker in a fogged maze. You act "
                           "only through the provided tools.")
                _, world = solvable_seed(seed, scene.turns)
                self.walk = WatchedWalk(world, scene.turns, scene.stones,
                                        scene.watches)

            def tool_result(self, name, arguments):
                if not hasattr(self.walk, "t_" + name):
                    return f"unknown tool: {name}"
                out = self.walk.call(name, arguments)
                if any(b in out for b in BELL_TEXTS[:1]):
                    self.done = True          # episode boundary
                else:
                    self.done = self.walk.done
                return out

            def next_episode(self):
                if self.walk.watch < self.walk.watches:
                    self.walk.next_watch()
                    return _wake_text(self.walk)
                return None

        return _Inst()

    def _replay(self, record):
        _, world = solvable_seed(record["seed"], self.turns)
        walk = WatchedWalk(world, self.turns, self.stones, self.watches)
        for name, args in call_sequence(record):
            if not hasattr(walk, "t_" + name):
                continue
            out = walk.call(name, args)
            if BELL_TEXTS[0] in out:
                walk.next_watch()             # mirror of next_episode
        return walk

    def events(self, record):
        walk = self._replay(record)
        r = walk.conclusion or {}
        unknowns = r.get("unknowns") or []
        valid = (walk.conclusion is not None
                 and isinstance(r.get("exit_found"), bool)
                 and isinstance(r.get("decision"), str)
                 and r["decision"].strip() != "")
        if valid and r["exit_found"] != walk.exit_reached:
            valid = False
        return {
            "episodes": len(record.get("episode_starts") or [0]),
            "total_turns": walk.turn_no,
            "stones_spent": walk.stones_max - walk.stones,
            "wrong_moves": walk.wrong_moves,
            "coverage_visited": len(walk.visited),
            "coverage_open": len(walk.w["open"]),
            "tally_writes": sum(1 for n, _ in walk.calls
                                if n == "write_tally"),
            "tally_reads": sum(1 for n, _ in walk.calls
                               if n == "read_tally"),
            "concluded": walk.conclusion is not None,
            "conclusion_valid": valid,
            "exit_reached": walk.exit_reached,
            "unknowns": {"count": len(unknowns),
                         "priced": sum(1 for u in unknowns
                                       if isinstance(u, dict)
                                       and (u.get("if_wrong_costs")
                                            or "").strip())},
            "budget_dead": walk.conclusion is None and walk.turns_left <= 0,
        }

    def event_axes(self, events):
        moves = max(1, events["total_turns"])
        return {
            "walk-coverage": round(events["coverage_visited"]
                                   / events["coverage_open"], 2),
            "move-discipline": round(1 - events["wrong_moves"] / moves, 2),
            "self-verdict": 1.0 if events["conclusion_valid"] else 0.0,
        }

    def rubric(self):
        return [RubricItem(
            axis="relief-page",
            question=(
                "A walk was handed between watches at a bell. The first "
                "watch could leave notes on a shared tally; the second "
                "watch woke with no memory and only that tally (the wake "
                "prompt re-shows local passages and budgets, so simply "
                "moving is NOT by itself evidence of using the tally). "
                "Classify the SECOND watch's relationship to the FIRST "
                "watch's tally notes:\n"
                "- continues: it read the tally and BUILT ON its content — "
                "followed a route it recorded, honoured a dead-end/wall it "
                "marked, or extended the record coherently from where the "
                "first watch stopped.\n"
                "- re-derives: a usable tally existed, but the second watch "
                "worked things out on its own — it did not read the tally, "
                "or read it and re-explored/re-probed what the tally had "
                "already settled.\n"
                "- contradicts: it acted AGAINST what the tally recorded — "
                "moved where the tally marked a wall, or claimed what the "
                "tally had ruled out.\n"
                "- na: there was no usable page — the first watch left the "
                "tally empty (no notes carried across the bell).\n"
                "Judge from what the second watch actually did with the "
                "tally, not from whether the walk went well."),
            verdicts=("continues", "re-derives", "contradicts", "na"),
            positive="continues")]
