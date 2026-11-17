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
        self.assertEqual(s["review_score"], 0.5)                    # 1 + 0.5 + 0 over three cells
        self.assertEqual(s["verdict_counts"], {"none": 1, "priced": 1, "unpriced": 1})

    def test_all_unpriced_differs_from_all_none_only_in_the_added_field(self):
        u = axis_scores([_cell(i, "unpriced") for i in (1, 2, 3)])["wall-pricing"]
        n = axis_scores([_cell(i, "none") for i in (1, 2, 3)])["wall-pricing"]
        self.assertEqual((u["score"], n["score"]), (0.0, 0.0))
        self.assertEqual((u["review_score"], n["review_score"]), (0.5, 0.0))

    def test_axes_without_the_rule_get_counts_but_no_review_score(self):
        s = axis_scores([_cell(1, "procedure", axis="object-hold", positive="object"),
                         _cell(2, "object", axis="object-hold", positive="object")])["object-hold"]
        self.assertEqual(s["score"], 0.5)
        self.assertNotIn("review_score", s)                      # no middle verdict declared
        self.assertEqual(s["verdict_counts"], {"object": 1, "procedure": 1})   # counts on every judged axis

    def test_grounding_and_relief_declare_their_middle_verdict(self):
        g = axis_scores([_cell(1, "mixed", "grounding", "grounded"), _cell(2, "borrowed", "grounding", "grounded")])["grounding"]
        self.assertEqual((g["score"], g["review_score"]), (0.0, 0.25))
        r = axis_scores([_cell(1, "re-derives", "relief-page", "continues"),
                         _cell(2, "contradicts", "relief-page", "continues")])["relief-page"]
        self.assertEqual((r["score"], r["review_score"]), (0.0, 0.25))

    def test_the_report_names_the_review_score(self):
        import os
        import tempfile
        from journeyman.record import RunDir
        from journeyman.report import render
        rd = RunDir(os.path.join(tempfile.mkdtemp(), "runs"))
        c = _cell(1, "unpriced")
        c.update({"cell_id": "closed-roads-noway_s1", "scene": "closed-roads-noway", "calls": 3, "tokens_in": 0,
                  "tokens_out": 0, "seconds": 1.0, "messages": [], "final_text": None, "budget": 12,
                  "events": {}, "invalid_reason": None, "seal": {}})
        rd.write_cell(c["cell_id"], c)
        text = render(rd, {}, "j", False)
        line = [x for x in text.split("\n") if x.strip().startswith("wall-pricing")][0]
        self.assertIn("review 0.50 (unpriced 1)", line)   # the labels behind it, on the same row
        self.assertTrue(line.split()[1] == "0.0")   # the score itself is still 0


if __name__ == "__main__":
    unittest.main()
