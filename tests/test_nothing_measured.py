#!/usr/bin/env python3
"""A run that measured nothing must not look like a run that did.

Both behaviours here shipped in 0.4.0 and were reproduced against it:
`journeyman run` against an endpoint that never answered wrote a full
report.md (header, empty PROFILE, Repro line) and exited 0, so CI counted
it as a finished run; and a mistyped scene name ended in a Python
traceback (`KeyError: 'echo-well'`) instead of the list of scenes.
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from journeyman import __main__ as cli  # noqa: E402

DEAD = "http://127.0.0.1:9/v1"   # discard port: refused at once, no network


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            cli.main(argv)
            code = 0
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class TestNothingMeasured(unittest.TestCase):
    def test_all_invalid_names_the_count_and_the_first_reason(self):
        from journeyman.report import nothing_measured
        cells = [{"invalid": True, "invalid_reason": None},
                 {"invalid": True, "invalid_reason": "URLError(refused)"},
                 {"invalid": True, "invalid_reason": "HTTP 405"}]
        self.assertEqual(nothing_measured(cells), (3, "URLError(refused)"))

    def test_one_valid_cell_is_enough_to_report(self):
        from journeyman.report import nothing_measured
        # The guard must not fire on a partial run: that one still reports.
        cells = [{"invalid": True, "invalid_reason": "x"}, {"invalid": False}]
        self.assertIsNone(nothing_measured(cells))

    def test_a_run_against_a_dead_endpoint_writes_no_report_and_fails(self):
        with tempfile.TemporaryDirectory() as runs:
            code, _, err = _run(["run", "--endpoint", DEAD, "--model", "none",
                                 "--scenes", "assayers-bench", "--seeds", "1",
                                 "--runs-dir", runs, "--quiet"])
            self.assertEqual(code, 1)
            self.assertIn("NO REPORT", err)
            self.assertIn("first reason:", err)
            (run,) = os.listdir(runs)
            self.assertFalse(os.path.exists(os.path.join(runs, run, "report.md")))
            self.assertFalse(os.path.exists(os.path.join(runs, run, "report.json")))
            # the cell records stay, so the failure can be read
            self.assertTrue(os.listdir(os.path.join(runs, run, "cells")))

    def test_rerendering_a_run_that_measured_nothing_also_fails(self):
        with tempfile.TemporaryDirectory() as runs:
            _run(["run", "--endpoint", DEAD, "--model", "none",
                  "--scenes", "assayers-bench", "--seeds", "1",
                  "--runs-dir", runs, "--quiet"])
            (run,) = os.listdir(runs)
            code, _, err = _run(["report", os.path.join(runs, run)])
            self.assertEqual(code, 1)
            self.assertIn("NO REPORT", err)


class TestUnknownScene(unittest.TestCase):
    def test_it_lists_the_scenes_and_exits_2_before_any_call(self):
        with mock.patch.object(cli, "resolve_model",
                               side_effect=AssertionError("model resolved")), \
             mock.patch.object(cli, "run_grid",
                               side_effect=AssertionError("grid started")):
            code, _, err = _run(["run", "--endpoint", DEAD,
                                 "--scenes", "echo-well,assayers-bench",
                                 "--seeds", "1", "--quiet"])
        self.assertEqual(code, 2)
        self.assertIn("unknown scene: echo-well", err)
        self.assertIn("assayers-bench", err.split("available:")[1])
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
