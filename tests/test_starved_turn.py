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

    def __init__(self, reasoning="", finish_reason=None, field="reasoning_content"):
        self.reasoning = reasoning
        self.finish_reason = finish_reason
        self.field = field
        self.turns = 0

    def chat(self, messages, tools, seed=None):
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        self.turns += 1
        msg = {"role": "assistant", "content": ""}
        if self.reasoning:
            if self.field == "reasoning_details":
                msg["reasoning_details"] = [{"type": "reasoning.text",
                                             "text": self.reasoning}]
            else:
                msg[self.field] = self.reasoning
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


class TestReasoningIsFoundWhateverItIsCalled(unittest.TestCase):
    """The guard must read the field the provider actually sends.

    It read `reasoning_content` only. OpenRouter sends `reasoning` (and
    `reasoning_details`), so on 2026-08-31 five cells of a calibration
    run closed with an empty turn after 77-256 characters of visible
    reasoning and were recorded as silent agents — the guard shipped in
    0.2.3 had never once fired outside the test suite. The fixture below
    is the real shape, taken from an archived cell of that run:

      {"role": "assistant",
       "reasoning": "It doesn't mention paging. There might be ...",
       "reasoning_details": [{"type": "reasoning.text", "text": "..."}],
       "finish_reason": "stop"}
    """

    def test_openrouter_shape_is_read(self):
        from journeyman.driver import reasoning_text
        real = {"role": "assistant", "content": None,
                "reasoning": "It doesn't mention paging. There might be a "
                             "script that triggers pager.",
                "reasoning_details": [{"type": "reasoning.text",
                                       "text": "It doesn't mention paging."}],
                "finish_reason": "stop"}
        self.assertIn("mention paging", reasoning_text(real))

    def test_details_only_is_read(self):
        from journeyman.driver import reasoning_text
        msg = {"role": "assistant", "content": None,
               "reasoning_details": [{"type": "reasoning.text", "text": "abc"},
                                     {"type": "reasoning.text", "text": "def"}]}
        self.assertEqual(reasoning_text(msg), "abc\ndef")

    def test_no_reasoning_is_empty(self):
        from journeyman.driver import reasoning_text
        self.assertEqual(reasoning_text({"role": "assistant"}), "")

    def test_a_starved_turn_is_caught_through_each_spelling(self):
        for field in ("reasoning_content", "reasoning", "reasoning_details"):
            cell = _run(_Agent(reasoning="x" * 1400, field=field))
            self.assertTrue(cell["invalid"], f"{field}: starved turn scored as behaviour")
            self.assertIn("starved turn", cell["invalid_reason"])


class TestStopAfterInvalid(unittest.TestCase):
    """A grid whose cells keep coming back invalid should stop, not finish.

    Measured 2026-08-31: a reasoning model against a 4000-token cap starved
    5 of 30 cells — every one on its FIRST turn, zero tool calls. The cause
    was identical in all five and visible in the first, but the grid ran to
    the end anyway: two and a half hours for a result the frozen card had
    already declared unreadable. The money was eight cents; the time was
    the loss.
    """

    def _grid(self, limit):
        from journeyman.driver import StoppedOnInvalid
        scene = sorted(REGISTRY)[0]
        agent = _Agent(reasoning="x" * 1400)      # every cell starves
        with tempfile.TemporaryDirectory() as tmp:
            rd = RunDir(tmp)
            stopped = None
            try:
                run_grid(agent, [scene], [1, 2, 3, 4], rd,
                         log=lambda *a: None, stop_after_invalid=limit)
            except StoppedOnInvalid as e:
                stopped = e
            return stopped, list(rd.read_cells())

    def test_it_stops_at_the_limit_and_keeps_what_ran(self):
        stopped, cells = self._grid(2)
        self.assertIsNotNone(stopped, "four invalid cells, limit 2, no stop")
        self.assertEqual(len(cells), 2, "stopped late or threw away cells")
        self.assertIsNotNone(stopped.seal, "seal lost — the partial run "
                                           "cannot be judged or reported")

    def test_without_the_flag_the_grid_still_runs_to_the_end(self):
        stopped, cells = self._grid(None)
        self.assertIsNone(stopped, "stopped without being asked to")
        self.assertEqual(len(cells), 4)
