#!/usr/bin/env python3
"""A closing call refused for budget is counted, not hidden in the axis.

Incident (2026-11-14): in one local run three 'no report' verdicts were
reports sent after the tool budget ran out. The scene refused them, the
judge scored them as no report, and nothing in the report separated them
from an agent that never tried to close.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from journeyman.driver import run_grid  # noqa: E402
from journeyman.record import RunDir  # noqa: E402
from journeyman import scenes  # noqa: E402,F401
from journeyman.scene import REGISTRY  # noqa: E402
from journeyman.report import render  # noqa: E402

SCENE = "finished-cart"   # service_host ground: `list` reads, `report` closes


class _Agent:
    """Spends `spend` calls on `list`, then calls `report` (unless None)."""
    model = "late"

    def __init__(self, spend, closer="report"):
        self.spend, self.closer, self.n = spend, closer, 0

    def chat(self, messages, tools, seed=None):
        usage = {"prompt_tokens": 1, "completion_tokens": 1}
        if self.n > self.spend:
            return ({"role": "assistant", "content": "done"}, usage)
        self.n += 1
        name, args = (("list", '{"dir": "/"}') if self.n <= self.spend
                      else (self.closer, '{"text": "fixed"}'))
        return ({"role": "assistant", "content": "", "tool_calls": [
            {"id": f"c{self.n}", "type": "function",
             "function": {"name": name, "arguments": args}}]}, usage)


def _cell(agent):
    with tempfile.TemporaryDirectory() as tmp:
        rd = RunDir(tmp)
        seal = run_grid(agent, [SCENE], [4242], rd, log=lambda *a: None)
        cell = list(rd.read_cells())[0]
        md = render(rd, seal, "test", True)
        return cell, md


class TestLateClosing(unittest.TestCase):
    def setUp(self):
        self.budget = REGISTRY[SCENE]().build(4242).budget

    def test_report_after_budget_is_counted(self):
        cell, md = _cell(_Agent(spend=self.budget))
        self.assertFalse(cell["invalid"], cell["invalid_reason"])
        self.assertEqual(cell["late_closing"], 1)
        self.assertIn("Late  : 1 cell(s)", md)

    def test_report_within_budget_is_not_late(self):
        cell, md = _cell(_Agent(spend=self.budget - 1))
        self.assertEqual(cell["late_closing"], 0)
        self.assertNotIn("Late  :", md)

    def test_refused_non_closing_call_is_not_late(self):
        cell, _ = _cell(_Agent(spend=self.budget + 1, closer="list"))
        self.assertEqual(cell["late_closing"], 0)

    def test_probe_leaves_the_world_untouched(self):
        cell, _ = _cell(_Agent(spend=self.budget))
        self.assertFalse(cell["events"].get("reported"),
                         "a refused report must not count as filed")


if __name__ == "__main__":
    unittest.main()
