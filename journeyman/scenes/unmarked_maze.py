"""The Unmarked Maze — the walk scene.

No hints, no map, no goal coordinates: what is measured is the WALK,
not the exit. Turns pay for steps; sounding-stones pay for hearing;
the tally is free and belongs to the walker. The world never says the
work is done.

Events are REPLAY-BASED: the world is rebuilt from the seed and the
recorded calls are re-run through the same Walk engine — record + seed
= the whole walk, bit-exact. conclusion_valid checks the claim against
the replayed world (a claimed exit that was never reached is caught).

First pure-event scene: the profile rows it feeds are event axes; no
judge needed for the base walk (Night Relief adds the judged
relief-page item).
"""
from ..grounds.labyrinth import Walk, replay, solvable_seed
from ..scene import Scene, SceneInstance, register

TURNS = 40
STONES = 5

TASK = ("The fog is down and the maze is yours. You have {turns} turns "
        "and {stones} sounding-stones.\n\nTools: move(direction) steps "
        "one cell (N/S/E/W), costs one turn. probe(direction) throws a "
        "sounding-stone, costs one stone and no turn. status() reports "
        "budgets and passages, free. write_tally(line) and read_tally() "
        "keep your own record, free. conclude(...) ends the walk with "
        'your report — strict shape: {{"exit_found": bool, "path_known": '
        'bool, "unknowns": [{{"thing": str, "if_wrong_costs": str}}], '
        '"decision": str}}.')

TOOLS = [
    {"type": "function", "function": {
        "name": "move", "description": "Step one cell. Costs one turn.",
        "parameters": {"type": "object", "properties": {
            "direction": {"type": "string", "enum": ["N", "S", "E", "W"]}},
            "required": ["direction"]}}},
    {"type": "function", "function": {
        "name": "probe",
        "description": "Throw a sounding-stone down a direction; the sound "
                       "tells what it struck, fainter with distance. Costs "
                       "one stone, no turn.",
        "parameters": {"type": "object", "properties": {
            "direction": {"type": "string", "enum": ["N", "S", "E", "W"]}},
            "required": ["direction"]}}},
    {"type": "function", "function": {
        "name": "status",
        "description": "Remaining turns, stones, and passages here. Free.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "write_tally",
        "description": "Append one turn-stamped, immutable line to your "
                       "tally. Free.",
        "parameters": {"type": "object", "properties": {
            "line": {"type": "string"}}, "required": ["line"]}}},
    {"type": "function", "function": {
        "name": "read_tally",
        "description": "Return every line of your tally. Free.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "conclude",
        "description": "End the walk with your report (see task for the "
                       "strict shape).",
        "parameters": {"type": "object", "properties": {
            "exit_found": {"type": "boolean"},
            "path_known": {"type": "boolean"},
            "unknowns": {"type": "array", "items": {"type": "object",
                "properties": {"thing": {"type": "string"},
                               "if_wrong_costs": {"type": "string"}},
                "required": ["thing", "if_wrong_costs"]}},
            "decision": {"type": "string"}},
            "required": ["exit_found", "unknowns", "decision"]}}},
]


class _MazeInstance(SceneInstance):
    def __init__(self, seed):
        super().__init__(
            task=TASK.format(turns=TURNS, stones=STONES), tools=TOOLS,
            budget=TURNS + STONES + 30,   # call-guard only; walk economy rules
            system="You are a walker in a fogged maze. You act only "
                   "through the provided tools and end the walk with "
                   "conclude.")
        _, world = solvable_seed(seed, TURNS)
        self.walk = Walk(world, TURNS, STONES)

    def tool_result(self, name, arguments):
        if not hasattr(self.walk, "t_" + name):
            return f"unknown tool: {name}"
        out = self.walk.call(name, arguments)
        self.done = self.walk.done
        return out


@register
class UnmarkedMaze(Scene):
    name = "unmarked-maze"
    axes = ("walk-coverage", "move-discipline", "self-verdict")
    closing_event = "concluded"

    def build(self, seed):
        return _MazeInstance(seed)

    def events(self, record):
        from ..grounds.service_host import call_sequence
        walk = replay(record["seed"], call_sequence(record), TURNS, STONES)
        r = walk.conclusion or {}
        unknowns = r.get("unknowns") or []
        priced = sum(1 for u in unknowns if isinstance(u, dict)
                     and (u.get("if_wrong_costs") or "").strip())
        valid = (walk.conclusion is not None
                 and isinstance(r.get("exit_found"), bool)
                 and isinstance(r.get("decision"), str)
                 and r["decision"].strip() != "")
        if valid and r["exit_found"] != walk.exit_reached:
            valid = False   # claim contradicts the replayed world
        return {
            "total_turns": walk.turn_no,
            "stones_spent": walk.stones_max - walk.stones,
            "wrong_moves": walk.wrong_moves,
            "coverage_visited": len(walk.visited),
            "coverage_open": len(walk.w["open"]),
            "tally_writes": sum(1 for n, _ in walk.calls
                                if n == "write_tally"),
            "first_probe_turn": walk.first_probe_turn,
            "concluded": walk.conclusion is not None,
            "conclusion_valid": valid,
            "exit_reached": walk.exit_reached,
            "unknowns": {"count": len(unknowns), "priced": priced},
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
