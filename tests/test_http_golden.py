#!/usr/bin/env python3
"""Golden test for the HTTP agent path.

Freezes what journeyman/driver.run_cell produces for every standard scene
and seed when driven by a deterministic ScriptedAgent.  A later refactor
of journeyman/driver.py can prove it changed nothing by comparing against
this golden.

Scope: this golden guards the single-episode budget/refusal/closing/text-
ending path and the agent_system prefix.  Multi-episode (next_episode) and
late_closing are NOT covered here (test_late_closing covers late closing).

Known-positive assertions are included so the golden cannot be vacuous.
"""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from journeyman.driver import run_cell  # noqa: E402
from journeyman import scenes  # noqa: E402,F401

# ── Standard scene names and seeds (copied from journeyman/__main__.py) ──

STANDARD_SCENES = (
    "closed-roads-detour",
    "closed-roads-noway",
    "assayers-bench",
    "finished-cart",
    "borrowed-story",
    "unmarked-maze",
    "night-relief",
    "night-watch",
    "night-alarm",
    "unsteady-scale",
)

STANDARD_SEEDS = (4242, 777, 31337)

GOLDEN_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "golden", "http_cells.json"
)

AGENT_SYSTEM = "GOLDEN AGENT SYSTEM TEXT"


# ── Deterministic scripted agent ──

def _build_args(schema):
    """Build argument dict from a tool JSON schema's parameters.

    Every property gets:
      - "x" for type string
      - 1 for type integer
      - 1.5 for type number
      - true for type boolean
      - [] for type array
      - {} for type object
    Applied recursively to nested objects/arrays.
    """
    params = schema.get("parameters", {})
    props = params.get("properties", {})
    return _build_props(props)


def _build_props(props):
    result = {}
    for name, spec in props.items():
        t = spec.get("type")
        if t == "string":
            result[name] = "x"
        elif t == "integer":
            result[name] = 1
        elif t == "number":
            result[name] = 1.5
        elif t == "boolean":
            result[name] = True
        elif t == "array":
            result[name] = []
        elif t == "object":
            inner = spec.get("properties")
            if inner:
                result[name] = _build_props(inner)
            else:
                result[name] = {}
        else:
            result[name] = "x"
    return result


class ScriptedAgent:
    """Deterministic duck-typed agent: always returns ONE assistant message
    with ONE tool call, chosen deterministically from the tools list.

    The tools list is sorted by function name; the tool index is
    (number of assistant messages already in messages) % len(tools).
    Arguments are built from the tool's JSON schema.
    """
    model = "golden"
    params = {}
    timeout = 300

    def chat(self, messages, tools, seed=None):
        # Sort tools by function name
        sorted_tools = sorted(tools, key=lambda t: t["function"]["name"])
        # Count assistant messages already in messages
        n = sum(1 for m in messages if m.get("role") == "assistant")
        idx = n % len(sorted_tools)
        tool = sorted_tools[idx]
        fn = tool["function"]
        args = _build_args(fn)
        call_id = f"call_{n}"
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        return (
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": fn["name"],
                            "arguments": json.dumps(args, sort_keys=True),
                        },
                    }
                ],
            },
            usage,
        )


class TextAgent:
    """Like ScriptedAgent on its first turn, then returns plain text 'done'
    on its second turn (covers the plain-text ending / final_text path)."""

    model = "golden-text"
    params = {}
    timeout = 300

    def chat(self, messages, tools, seed=None):
        sorted_tools = sorted(tools, key=lambda t: t["function"]["name"])
        n = sum(1 for m in messages if m.get("role") == "assistant")
        if n == 0:
            # First turn: one tool call, same as ScriptedAgent
            idx = 0  # n % len(sorted_tools) == 0
            tool = sorted_tools[idx]
            fn = tool["function"]
            args = _build_args(fn)
            call_id = "call_0"
            usage = {"prompt_tokens": 10, "completion_tokens": 5}
            return (
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": fn["name"],
                                "arguments": json.dumps(args, sort_keys=True),
                            },
                        }
                    ],
                },
                usage,
            )
        else:
            # Second turn: plain text ending
            return ({"role": "assistant", "content": "done"}, {"prompt_tokens": 10, "completion_tokens": 5})


# ── Snapshot builder ──

def snapshot():
    """Run every standard scene × seed with ScriptedAgent and collect
    the full record shape (as run_grid builds it).

    Also runs each scene × seed with TextAgent for the final_text key.
    """
    from journeyman.scene import REGISTRY

    result = {}
    for name in STANDARD_SCENES:
        for seed in STANDARD_SEEDS:
            scene_cls = REGISTRY[name]
            # run_cell calls scene.build(seed) internally
            rec = run_cell(
                ScriptedAgent(),
                scene_cls(),
                seed,
                log=lambda *a, **k: None,
                agent_system=AGENT_SYSTEM,
            )
            # Build full_record exactly as run_grid does (driver.py:326-328)
            full_record = {
                "cell_id": f"{name}_s{seed}",
                "scene": name,
                "seed": seed,
                "seal": None,
                "invalid": False,
                "invalid_reason": None,
                "events": None,
                "event_axes": None,
                "verdicts": None,
                **rec,
            }
            # Compute events and event_axes from the full record
            scene_obj = scene_cls()
            events = scene_obj.events(full_record)
            event_axes = scene_obj.event_axes(events)
            # Record the bare dict keys (except seconds) plus events/event_axes
            cell_key = f"{name}_s{seed}"
            entry = {k: v for k, v in rec.items() if k != "seconds"}
            entry["events"] = events
            entry["event_axes"] = event_axes
            result[cell_key] = entry

    # TextAgent cells: one per scene×seed, keyed separately
    for name in STANDARD_SCENES:
        for seed in STANDARD_SEEDS:
            scene_cls = REGISTRY[name]
            rec = run_cell(
                TextAgent(),
                scene_cls(),
                seed,
                log=lambda *a, **k: None,
                agent_system=AGENT_SYSTEM,
            )
            cell_key = f"{name}_s{seed}_text"
            entry = {k: v for k, v in rec.items() if k != "seconds"}
            result[cell_key] = entry

    return result


# ── Golden test ──

class TestGoldenHttpCells(unittest.TestCase):
    """Compare snapshot() against the golden data file.

    If JOURNEYMAN_REGEN_GOLDEN=1, write the golden file.
    If the file is MISSING and the variable is not set, FAIL.
    Otherwise load and assert equality.
    """

    @classmethod
    def setUpClass(cls):
        cls._golden = None
        _regen = os.environ.get("JOURNEYMAN_REGEN_GOLDEN") == "1"
        _regen_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".regen_golden"
        )
        if _regen or os.path.isfile(_regen_file):
            # Regenerate
            data = snapshot()
            os.makedirs(os.path.dirname(GOLDEN_PATH), exist_ok=True)
            with open(GOLDEN_PATH, "w") as f:
                json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
            cls._golden = data
            # Clean up the trigger file
            if os.path.isfile(_regen_file):
                os.remove(_regen_file)
        elif not os.path.isfile(GOLDEN_PATH):
            cls._golden = None  # will trigger failure in test
        else:
            with open(GOLDEN_PATH) as f:
                cls._golden = json.load(f)

    def test_golden_equality(self):
        """snapshot() must match the golden data exactly."""
        if self._golden is None:
            self.fail(
                f"Golden file {GOLDEN_PATH} is missing. "
                "Set JOURNEYMAN_REGEN_GOLDEN=1 to generate it."
            )
        data = snapshot()
        if data != self._golden:
            # Find first differing cell key
            all_keys = sorted(set(list(data.keys()) + list(self._golden.keys())))
            for key in all_keys:
                if key not in data:
                    self.fail(f"Missing cell key in snapshot: {key}")
                if key not in self._golden:
                    self.fail(f"Extra cell key in snapshot: {key}")
                if data[key] != self._golden[key]:
                    self.fail(f"First differing cell key: {key}")
            self.fail("snapshot() != golden data (keys differ)")

    def test_known_positive(self):
        """Known-positive assertions measured on 2026-11-17 with exactly
        this scripted agent (seed 4242)."""
        data = snapshot()
        for seed in STANDARD_SEEDS:
            # (a) night-relief cells have calls > budget (budget/refusal path)
            nr_key = f"night-relief_s{seed}"
            nr = data[nr_key]
            self.assertGreater(
                nr["calls"], nr["budget"],
                f"night-relief_s{seed}: calls={nr['calls']} should be > budget={nr['budget']}"
            )

            # (b) at least one cell per seed has calls < budget (closing path)
            has_under_budget = False
            for name in STANDARD_SCENES:
                if name == "night-relief":
                    continue
                key = f"{name}_s{seed}"
                if data[key]["calls"] < data[key]["budget"]:
                    has_under_budget = True
                    break
            self.assertTrue(
                has_under_budget,
                f"No cell under budget for seed {seed}"
            )

            # (c) every standard scene appears
            for name in STANDARD_SCENES:
                key = f"{name}_s{seed}"
                self.assertIn(key, data, f"Missing scene {name} for seed {seed}")

        # (d) TextAgent cells have final_text == "done"
        # (for scenes where the first tool call doesn't close the scene)
        # Scenes where sorted tools[0] closes immediately:
        #   unmarked-maze (conclude sets done=True),
        #   unsteady-scale (conclude sets done=True)
        # night-relief's conclude does NOT set done=True (bell does),
        # so TextAgent gets a second turn there.
        _CLOSE_FIRST = {"unmarked-maze", "unsteady-scale"}
        for name in STANDARD_SCENES:
            for seed in STANDARD_SEEDS:
                key = f"{name}_s{seed}_text"
                ft = data[key]["final_text"]
                if name in _CLOSE_FIRST:
                    self.assertIsNone(
                        ft,
                        f"TextAgent {key}: final_text={ft}"
                    )
                else:
                    self.assertEqual(
                        ft, "done",
                        f"TextAgent {key}: final_text={ft}"
                    )

        # (e) no cell has late_closing > 0
        for name in STANDARD_SCENES:
            for seed in STANDARD_SEEDS:
                key = f"{name}_s{seed}"
                self.assertEqual(
                    data[key]["late_closing"], 0,
                    f"{key}: late_closing={data[key]['late_closing']}"
                )

        # (f) no cell reaches a second episode (episode_starts has only one entry)
        for name in STANDARD_SCENES:
            for seed in STANDARD_SEEDS:
                key = f"{name}_s{seed}"
                self.assertEqual(
                    len(data[key]["episode_starts"]), 1,
                    f"{key}: episode_starts={data[key]['episode_starts']}"
                )


if __name__ == "__main__":
    unittest.main()
