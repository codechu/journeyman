"""Asking a case's draws at once must not change how the case is decided.

2026-11-12: a dense 27B judge took about three and a half minutes a case,
one call at a time, while the server had four slots and three of them sat
idle — an eighty-two-case exam ran for five hours. `--concurrency` asks a
case's draws together. These tests hold the two things that change has to
keep: the same verdicts, misses and early exit as the sequential exam, and
calls really in flight together (otherwise the flag is decoration).
"""
import threading
import time
import unittest
from collections import Counter
from unittest import mock

from journeyman import qualify as q
from journeyman import scenes  # noqa: F401 — the rubric index reads the registry


class Judge:
    """Answers by record: right on most cases, wrong on some, split on some.
    A split case answers wrong, right, right — in whatever order the calls
    arrive, so the majority does not depend on scheduling."""
    url = "http://localhost:4567/v1"
    api_key = None

    def __init__(self, cases, delay=0.02):
        self.truth = {c["record"]: c for c in cases}
        self.seen = Counter()
        self.lock = threading.Lock()
        self.in_flight = self.peak = 0
        self.delay = delay

    def _label(self, prompt):
        for record, case in self.truth.items():
            if record in prompt:
                break
        else:
            raise AssertionError("prompt without a known record")
        k = sum(map(ord, case["record"][:200])) % 5
        with self.lock:
            n = self.seen[record]
            self.seen[record] += 1
        if k == 0:
            return "wrong-label"                       # a miss
        if k == 1:
            return "wrong-label" if n == 0 else case["true_label"]   # split, right wins
        return case["true_label"]

    def chat(self, messages, tools, seed=None):
        with self.lock:
            self.in_flight += 1
            self.peak = max(self.peak, self.in_flight)
        try:
            time.sleep(self.delay)
            return {"content": f"VERDICT: {self._label(messages[0]['content'])}"}, {}
        finally:
            with self.lock:
                self.in_flight -= 1


def _exam(concurrency, early_exit=False, n=24):
    cal = q.load_set()
    cal = dict(cal, cases=cal["cases"][:n])
    judge = Judge(cal["cases"])
    with mock.patch("journeyman.driver.list_models", lambda *a, **k: ["m"]):
        result = q.qualify(judge, cal=cal, log=lambda *a: None, repeats=3,
                           early_exit=early_exit, concurrency=concurrency)
    result.pop("stamp")
    return result, judge


class TestConcurrency(unittest.TestCase):
    def test_same_verdicts_and_misses_as_sequential(self):
        seq, _ = _exam(1)
        par, _ = _exam(3)
        self.assertEqual(par, seq)
        # equality of two empty exams proves nothing: cases were scored,
        # and the fixture really produced misses
        self.assertEqual(sum(a["n"] for a in seq["axes"].values()), 24)
        self.assertTrue(any(a["misses"] for a in seq["axes"].values()))

    def test_same_early_exit_as_sequential(self):
        seq, _ = _exam(1, early_exit=True, n=82)
        par, _ = _exam(3, early_exit=True, n=82)
        self.assertEqual(par, seq)
        self.assertIn("early_exit", seq, "the fixture never triggered an early exit")

    def test_draws_are_really_in_flight_together(self):
        _, judge = _exam(3, n=6)
        self.assertEqual(judge.peak, 3)

    def test_a_long_draw_does_not_idle_the_other_slots(self):
        # The first call of the exam is slow (a judge thinking at length);
        # while it runs, the freed slots must take the following cases'
        # draws instead of waiting for it. Per-case batching starts only
        # the case's own three calls before that draw ends.
        cal = q.load_set()
        cal = dict(cal, cases=cal["cases"][:6])
        judge = Judge(cal["cases"], delay=0.01)
        first = {"end": None, "starts": []}
        lock = threading.Lock()
        plain = judge.chat

        def chat(messages, tools, seed=None):
            with lock:
                first["starts"].append(time.monotonic())
                slow = len(first["starts"]) == 1
            out = plain(messages, tools)
            if slow:
                time.sleep(0.3)
                first["end"] = time.monotonic()
            return out

        judge.chat = chat
        with mock.patch("journeyman.driver.list_models", lambda *a, **k: ["m"]):
            q.qualify(judge, cal=cal, log=lambda *a: None, repeats=3,
                      concurrency=3)
        started_meanwhile = sum(t < first["end"] for t in first["starts"])
        self.assertGreater(started_meanwhile, 3)

    def test_sequential_stays_one_call_at_a_time(self):
        _, judge = _exam(1, n=6)
        self.assertEqual(judge.peak, 1)


if __name__ == "__main__":
    unittest.main()
