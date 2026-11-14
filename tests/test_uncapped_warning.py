#!/usr/bin/env python3
"""An uncapped agent run says so before the first cell.

Incident (2026-11-14): with no max_tokens, a runaway generation ran to the
300 s transport timeout and was re-sent; on a deterministic local server each
attempt reproduced it, and one cell took 14+ minutes and 35k tokens. Nothing
in the run output said the run was uncapped.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from journeyman.__main__ import uncapped_warning  # noqa: E402


class TestUncappedWarning(unittest.TestCase):
    def test_no_params_warns(self):
        w = uncapped_warning(None, 300)
        self.assertIn("uncapped", w)
        self.assertIn("300s", w)

    def test_params_without_cap_warn(self):
        self.assertIn("uncapped", uncapped_warning({"temperature": 0.6}, 300))

    def test_a_cap_silences_it(self):
        for k in ("max_tokens", "max_completion_tokens"):
            self.assertIsNone(uncapped_warning({k: 16384}, 300), k)

    def test_minus_one_is_uncapped(self):
        # llama.cpp reads max_tokens -1 as "no limit"
        for v in (-1, 0, None):
            self.assertIn("uncapped", uncapped_warning({"max_tokens": v}, 300), v)


if __name__ == "__main__":
    unittest.main()
