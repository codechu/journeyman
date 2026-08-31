"""Run records: the seal, the cells, the event stream.

Three views of one truth: live terminal lines, events.jsonl, final report.
They can never disagree because the terminal and the report are both
rendered FROM the records written here.

Cell record (cells/<cell_id>.json):
  {"cell_id", "scene", "seed", "seal", "messages", "final_text",
   "budget", "invalid", "invalid_reason", "events", "event_axes",
   "verdicts", "calls", "tokens_in", "tokens_out", "seconds"}

  The two scoring layers arrive under SEPARATE keys, and the difference
  is load-bearing: "verdicts" holds judged axes (a model answered a
  rubric question; each entry carries the `positive` label it is scored
  against), "event_axes" holds counted axes (computed from replayed
  events by Scene.event_axes, no judge involved). Anything carrying a
  score elsewhere must keep them apart — a counted fact presented as a
  model's opinion, or the reverse, misstates what was measured.

The seal makes a run reproducible or it is not a run:
  bench version + scene-set id + scene md5s + seeds + endpoint model.
"""
import hashlib
import json
import os
import time


def md5(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]


def world_source(cls):
    """The bytes that define a scene's world.

    NOT the class body: a scene's task text, file corpus, generators and
    physics all live at module level, and its ground lives in another
    module entirely. Hashing `inspect.getsource(cls)` left all of that
    unpinned — caught on 2026-08-31, when a fix that rewrote Night
    Alarm's two logs left the seal byte-identical to the run before it.
    A seal that does not move when the world moves is not a seal.
    """
    import inspect, re, sys
    mod = sys.modules[cls.__module__]
    src = inspect.getsource(mod)
    parts = [src]
    for ground in sorted(set(re.findall(r"grounds\.(\w+)", src))):
        gm = sys.modules.get(f"journeyman.grounds.{ground}")
        if gm is not None:
            parts.append(inspect.getsource(gm))
    return "\n".join(parts)


def make_seal(bench_version, scene_set, scenes, seeds, model,
              agent_system=None, agent_params=None):
    return {
        # the submitter's system text is part of the AGENT definition:
        # hashed so the run stays reproducible (None = agent adds none)
        "agent_system_md5": md5(agent_system) if agent_system else None,
        # sampling params: agent definition too — published VERBATIM
        # (small and transparency beats a hash here)
        "agent_params": agent_params,
        "bench": bench_version,
        "scene_set": scene_set,
        # the seal hashes scene SOURCE bytes — a seal that does not pin
        # the world it sealed is not a seal. That means the scene's whole
        # module and the ground it stands on, not just the class body.
        "scene_md5": {name: md5(world_source(cls))
                      for name, cls in scenes.items()},
        "seeds": seeds,
        "model": model,
    }


class RunDir:
    """runs/<stamp>/ — events.jsonl + cells/ + report.*"""

    @classmethod
    def attach(cls, path):
        """Open an EXISTING run dir (re-render/re-judge) without creating."""
        import os as _os
        if not _os.path.isdir(_os.path.join(path, "cells")):
            raise SystemExit(f"not a run dir (no cells/): {path}")
        obj = cls.__new__(cls)
        obj.path = path
        obj._events = open(_os.path.join(path, "events.jsonl"), "a",
                           buffering=1)
        return obj

    def __init__(self, root="runs", stamp=None):
        self.path = os.path.join(root, stamp or time.strftime("%Y-%m-%d_%H%M%S"))
        os.makedirs(os.path.join(self.path, "cells"), exist_ok=True)
        self._events = open(os.path.join(self.path, "events.jsonl"), "a",
                            buffering=1)  # line-buffered: tail -f friendly

    def event(self, kind, **fields):
        line = {"t": round(time.time(), 3), "ev": kind, **fields}
        self._events.write(json.dumps(line, ensure_ascii=False) + "\n")
        return line

    def cell_path(self, cell_id):
        return os.path.join(self.path, "cells", f"{cell_id}.json")

    def cell_done(self, cell_id):
        return os.path.exists(self.cell_path(cell_id))

    def write_cell(self, cell_id, record):
        with open(self.cell_path(cell_id), "w") as f:
            json.dump(record, f, ensure_ascii=False, indent=1)

    def read_cells(self):
        cdir = os.path.join(self.path, "cells")
        for fn in sorted(os.listdir(cdir)):
            if fn.endswith(".json"):
                yield json.load(open(os.path.join(cdir, fn)))

# A call past the declared budget is NOT answered by the scene: the driver
# returns this sentinel instead. The record keeps the attempt, so anything
# reading the record must skip it — a report the scene never received was
# not filed. (2026-08-23: the events layer counted such attempts; 40 of 526
# live cells carried a decision-bearing lie, five calibration cases too.)
BUDGET_REFUSED = "budget exhausted: no further calls are answered"


def answered_calls(record):
    """(tool_name, args) for every call the scene actually answered."""
    answered = {}
    for m in record["messages"]:
        if m.get("role") == "tool" and m.get("tool_call_id") is not None:
            answered[m["tool_call_id"]] = m.get("content") or ""
    out = []
    for m in record["messages"]:
        for tc in (m.get("tool_calls") or []):
            result = answered.get(tc.get("id"))
            if result is not None and result.startswith(BUDGET_REFUSED):
                continue
            fn = tc["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                args = {}
            out.append((fn["name"], args))
    return out
