#!/usr/bin/env python3
"""An empty closing turn is a starved turn, not a silent agent.

A reasoning model spends a fixed budget thinking before it writes. When the
budget runs out first the body comes back empty — the model produced no
move, which is the same category as a timeout and is voided that way.
Scored as behaviour instead, it zeroes every axis that reads the closing
report, and the profile then describes the token budget rather than the
agent.

*Incident (2026-08-29):* a full standard run of a production identity came
back with eighteen of twenty-four cells "no report" and four axes at 0.00.
The last turn of each carried zero characters of content and an average of
1380 characters of reasoning. Nothing in the record said so, because
`finish_reason` was read and thrown away.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from journeyman.driver import run_grid  # noqa: E402
from journeyman.record import RunDir  # noqa: E402
from journeyman import scenes  # noqa: E402,F401
from journeyman.scene import REGISTRY  # noqa: E402


class _Agent:
    """Answers one tool call, then returns an empty closing turn."""
    model = "starved"

    def __init__(self, reasoning="", finish_reason=None):
        self.reasoning = reasoning
        self.finish_reason = finish_reason
        self.turns = 0

    def chat(self, messages, tools, seed=None):
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        self.turns += 1
        msg = {"role": "assistant", "content": ""}
        if self.reasoning:
            msg["reasoning_content"] = self.reasoning
        if self.finish_reason:
            msg["finish_reason"] = self.finish_reason
        return (msg, usage)


def _run(agent):
    scene = sorted(REGISTRY)[0]
    with tempfile.TemporaryDirectory() as tmp:
        rd = RunDir(tmp)
        run_grid(agent, [scene], [4242], rd, log=lambda *a: None)
        return list(rd.read_cells())[0]


class TestStarvedTurn(unittest.TestCase):
    def test_a_long_think_and_an_empty_body_voids_the_cell(self):
        cell = _run(_Agent(reasoning="x" * 1400))
        self.assertTrue(cell["invalid"], "a starved turn is not behaviour")
        self.assertIn("starved", cell["invalid_reason"].lower())
        self.assertIn("max_tokens", cell["invalid_reason"])

    def test_finish_reason_length_voids_it_too(self):
        cell = _run(_Agent(finish_reason="length"))
        self.assertTrue(cell["invalid"])
        self.assertIn("length", cell["invalid_reason"])

    def test_an_agent_that_simply_says_nothing_is_still_scored(self):
        """Silence with no thinking behind it is behaviour, and stays so.

        The distinction is the whole point: voiding every empty closing
        would hide an agent that genuinely never reports.
        """
        cell = _run(_Agent())
        self.assertFalse(cell["invalid"],
                         "an empty turn with no reasoning is silence, "
                         "and silence is what several axes measure")


if __name__ == "__main__":
    unittest.main()
