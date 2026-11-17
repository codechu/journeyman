#!/usr/bin/env python3
"""Tests for the Ledger class in journeyman/driver.py.

Verifies that the per-call budget logic extracted from run_cell behaves
correctly: budget counting, refusal, malformed-JSON handling, runaway
detection, and dict-vs-string argument equivalence.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from journeyman import scenes  # noqa: F401
from journeyman.driver import Ledger  # noqa: E402
from journeyman.record import BUDGET_REFUSED  # noqa: E402
from journeyman.scene import REGISTRY  # noqa: E402


class TestLedger(unittest.TestCase):
    """Ledger behaviour tests."""

    def _make_ledger(self):
        """Build a real scene instance and a Ledger on it."""
        scene = REGISTRY["finished-cart"]().build(4242)
        return Ledger(scene)

    def _make_fresh_scene(self):
        """Build a fresh scene instance (not yet built into an instance)."""
        return REGISTRY["finished-cart"]().build(4242)

    # (a) First inst.budget calls return non-BUDGET_REFUSED and ledger.calls counts them
    def test_budget_calls_returned(self):
        ledger = self._make_ledger()
        scene = ledger.inst
        for i in range(scene.budget):
            result = ledger.answer("list", {"dir": "/"})
            self.assertNotIn(BUDGET_REFUSED, result,
                             f"call {i+1} should not be refused")
        self.assertEqual(ledger.calls, scene.budget)

    # (b) The next call returns exactly BUDGET_REFUSED
    def test_call_after_budget_refused(self):
        ledger = self._make_ledger()
        scene = ledger.inst
        # Spend the budget
        for _ in range(scene.budget):
            ledger.answer("list", {"dir": "/"})
        # Next call must be refused
        result = ledger.answer("list", {"dir": "/"})
        self.assertEqual(result, BUDGET_REFUSED)

    # (c) Malformed JSON gives same result as _unparsed on a fresh instance
    def test_malformed_json_handled(self):
        ledger = self._make_ledger()
        scene = ledger.inst
        # Call with malformed JSON
        result = ledger.answer("list", "not json")
        self.assertEqual(ledger.calls, 1)
        # Compare against a fresh instance with _unparsed
        fresh = self._make_fresh_scene()
        expected = fresh.tool_result("list", {"_unparsed": "not json"})
        self.assertEqual(result, expected)

    # (d) runaway is False at budget+2 and True at budget+3
    def test_runaway_detection(self):
        ledger = self._make_ledger()
        scene = ledger.inst
        # Spend budget calls
        for _ in range(scene.budget):
            ledger.answer("list", {"dir": "/"})
        # At budget+1
        ledger.answer("list", {"dir": "/"})
        self.assertFalse(ledger.runaway)
        # At budget+2
        ledger.answer("list", {"dir": "/"})
        self.assertFalse(ledger.runaway)
        # At budget+3
        ledger.answer("list", {"dir": "/"})
        self.assertTrue(ledger.runaway)

    # (f) answer(name, None), answer(name, ""), answer(name, {}) same as tool_result(name, {})
    def test_none_empty_dict_arguments(self):
        ledger = self._make_ledger()
        scene = ledger.inst
        r_none = ledger.answer("list", None)
        r_empty = ledger.answer("list", "")
        r_dict = ledger.answer("list", {})
        fresh = self._make_fresh_scene()
        expected = fresh.tool_result("list", {})
        self.assertEqual(r_none, expected)
        self.assertEqual(r_empty, expected)
        self.assertEqual(r_dict, expected)

    # (g) answer(name, {"dir": "/"}) (dict) same as answer(name, '{"dir": "/"}') (string)
    def test_dict_vs_string_arguments(self):
        ledger1 = self._make_ledger()
        ledger2 = self._make_ledger()
        r_dict = ledger1.answer("list", {"dir": "/"})
        r_str = ledger2.answer("list", '{"dir": "/"}')
        self.assertEqual(r_dict, r_str)

    # (e) After budget spent, a refused closing call increases late_closing
    def test_refused_closing_increases_late_closing(self):
        ledger = self._make_ledger()
        scene = ledger.inst
        # Spend the budget on non-closing calls
        for _ in range(scene.budget):
            ledger.answer("list", {"dir": "/"})
        # Now call report (the closing tool) — should be refused and count late_closing
        result = ledger.answer("report", {"text": "done"})
        self.assertEqual(result, BUDGET_REFUSED)
        self.assertEqual(ledger.late_closing, 1)


if __name__ == "__main__":
    unittest.main()
