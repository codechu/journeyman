"""Run records: the seal, the cells, the event stream.

Three views of one truth: live terminal lines, events.jsonl, final report.
They can never disagree because the terminal and the report are both
rendered FROM the records written here.

Cell record (cells/<cell_id>.json):
  {"cell_id", "scene", "seed", "seal", "messages", "final_text",
   "budget", "invalid", "invalid_reason", "events", "verdicts",
   "calls", "tokens_in", "tokens_out", "seconds"}

The seal makes a run reproducible or it is not a run:
  bench version + scene-set id + scene md5s + seeds + endpoint model.
"""
import hashlib
import json
import os
import time


def md5(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]


def make_seal(bench_version, scene_set, scenes, seeds, model,
              agent_system=None, agent_params=None):
    import inspect
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
        # the world it sealed is not a seal
        "scene_md5": {name: md5(inspect.getsource(cls))
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
