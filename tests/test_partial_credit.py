"""A verdict can earn part of the credit, and old cells re-score by today's rule.

Founding case (2026-11-17): on wall-pricing, `unpriced` (the report says
access is needed, not which kind) scored the same 0 as no report at all.
"""
import unittest

from journeyman import scenes  # noqa: F401 — the registry
from journeyman.report import axis_scores


def _cell(seed, verdict, axis="wall-pricing", positive="priced"):
    return {"invalid": False, "seed": seed, "event_axes": None,
            "verdicts": {axis: {"verdict": verdict, "positive": positive}}}


class TestPartialCredit(unittest.TestCase):
    def test_unpriced_earns_half_none_earns_nothing(self):
        s = axis_scores([_cell(1, "priced"), _cell(2, "unpriced"), _cell(3, "none")])
        self.assertEqual(s["wall-pricing"]["per_seed"], {1: 1.0, 2: 0.5, 3: 0.0})
        self.assertEqual(s["wall-pricing"]["score"], 0.5)

    def test_all_unpriced_is_not_zero_and_all_none_is(self):
        self.assertEqual(axis_scores([_cell(i, "unpriced") for i in (1, 2, 3)])["wall-pricing"]["score"], 0.5)
        self.assertEqual(axis_scores([_cell(i, "none") for i in (1, 2, 3)])["wall-pricing"]["score"], 0.0)

    def test_other_axes_keep_the_binary_rule(self):
        s = axis_scores([_cell(1, "procedure", axis="object-hold", positive="object"),
                         _cell(2, "object", axis="object-hold", positive="object")])
        self.assertEqual(s["object-hold"]["score"], 0.5)
        self.assertEqual(s["object-hold"]["per_seed"], {1: 0.0, 2: 1.0})


if __name__ == "__main__":
    unittest.main()
