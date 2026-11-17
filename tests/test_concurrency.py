"""Cells are independent worlds, so a parallel grid must write the same
records as the sequential one (timing aside). The standard run stays
sequential; parallel is a convenience for slow remote agents."""
import os
import tempfile
import time
import unittest

from journeyman import scenes  # noqa: F401 — the registry
from journeyman.driver import run_grid
from journeyman.record import RunDir

from tests.test_http_golden import ScriptedAgent

CELLS = ["finished-cart", "closed-roads-noway", "night-relief"]   # night-relief: the scripted run differs by seed
SEEDS = [4242, 777]


def _records(concurrency):
    rd = RunDir(os.path.join(tempfile.mkdtemp(), "runs"))
    run_grid(ScriptedAgent(), CELLS, SEEDS, rd, log=lambda *a, **k: None,
             concurrency=concurrency)
    out = {}
    for c in rd.read_cells():
        c = dict(c)
        c.pop("seconds", None)
        out[c["cell_id"]] = c
    return out


class TestConcurrency(unittest.TestCase):
    def test_parallel_grid_writes_the_same_records(self):
        one, two = _records(1), _records(2)
        self.assertEqual(len(one), len(CELLS) * len(SEEDS))
        self.assertEqual(sorted(one), sorted(two))
        for k in one:
            self.assertEqual(one[k], two[k], k)

    def test_parallel_grid_really_runs_in_parallel(self):
        class Slow(ScriptedAgent):
            def chat(self, messages, tools, seed=None):
                time.sleep(0.05)
                return super().chat(messages, tools, seed)

        def wall(concurrency):
            rd = RunDir(os.path.join(tempfile.mkdtemp(), "runs"))
            t0 = time.time()
            run_grid(Slow(), ["finished-cart", "closed-roads-noway", "night-watch", "borrowed-story"],
                     [4242], rd, log=lambda *a, **k: None, concurrency=concurrency)
            return time.time() - t0
        self.assertLess(wall(4), 0.6 * wall(1))


if __name__ == "__main__":
    unittest.main()
