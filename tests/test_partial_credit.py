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
    def test_score_keeps_its_meaning_and_the_credit_sits_beside_it(self):
        s = axis_scores([_cell(1, "priced"), _cell(2, "unpriced"), _cell(3, "none")])["wall-pricing"]
        self.assertEqual(s["per_seed"], {1: 1.0, 2: 0.0, 3: 0.0})   # only the positive verdict counts
        self.assertEqual(s["score"], 0.33)
        self.assertEqual(s["score_partial"], 0.5)                    # 1 + 0.5 + 0 over three cells
        self.assertEqual(s["verdict_counts"], {"none": 1, "priced": 1, "unpriced": 1})

    def test_all_unpriced_differs_from_all_none_only_in_the_added_field(self):
        u = axis_scores([_cell(i, "unpriced") for i in (1, 2, 3)])["wall-pricing"]
        n = axis_scores([_cell(i, "none") for i in (1, 2, 3)])["wall-pricing"]
        self.assertEqual((u["score"], n["score"]), (0.0, 0.0))
        self.assertEqual((u["score_partial"], n["score_partial"]), (0.5, 0.0))

    def test_axes_without_the_rule_get_no_new_field(self):
        s = axis_scores([_cell(1, "procedure", axis="object-hold", positive="object"),
                         _cell(2, "object", axis="object-hold", positive="object")])["object-hold"]
        self.assertEqual(s["score"], 0.5)
        self.assertNotIn("score_partial", s)
        self.assertNotIn("verdict_counts", s)


if __name__ == "__main__":
    unittest.main()
