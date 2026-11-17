"""`journeyman compare`: two runs read as a pair, and a pair that is not one says so."""
import os
import tempfile
import unittest

from journeyman import scenes  # noqa: F401 — the registry
from journeyman.compare import compare, label, pairing, render
from journeyman.record import RunDir


def _run(system_md5, verdicts, extra_seal=None, late=None):
    """A run dir with one wall-pricing-style cell per seed: verdicts = {seed: label}."""
    rd = RunDir(os.path.join(tempfile.mkdtemp(), "runs"))
    seal = {"agent_system_md5": system_md5, "agent_params": None, "bench": "x",
            "scene_set": "dev", "scene_md5": {"s": "1"}, "seeds": sorted(verdicts), "model": "m"}
    seal.update(extra_seal or {})
    for seed, v in verdicts.items():
        cell = {"cell_id": f"finished-cart_s{seed}", "scene": "finished-cart", "seed": seed, "seal": seal,
                "invalid": False, "invalid_reason": None, "events": {}, "event_axes": None,
                "verdicts": {"object-hold": {"verdict": v, "positive": "object"}},
                "messages": [], "final_text": None, "budget": 12, "calls": 5,
                "tokens_in": 0, "tokens_out": 0, "seconds": 1.0}
        if late is not None:
            cell["late_closing"] = late
        rd.write_cell(cell["cell_id"], cell)
    return rd.path


class TestLabels(unittest.TestCase):
    def test_one_cell_is_the_smallest_movement(self):
        self.assertEqual(label(0.0, 0.67, 3), "opened")
        self.assertEqual(label(0.0, 0.33, 3), "moved up, still low")   # rounded 1/3 still counts as a cell
        self.assertEqual(label(0.67, 1.0, 3), "improved")
        self.assertEqual(label(0.67, 0.33, 3), "side effect")
        self.assertEqual(label(0.0, 0.0, 3), "still low")
        self.assertEqual(label(0.60, 0.73, 6), "unchanged")            # under one cell of six
        self.assertEqual(label(None, 0.5, 3), "no data")


class TestCompare(unittest.TestCase):
    def test_paired_runs_read_axis_by_axis(self):
        a = _run(None, {1: "procedure", 2: "procedure", 3: "procedure"})
        b = _run("abc", {1: "object", 2: "object", 3: "procedure"}, late=1)
        r = compare(a, b)
        self.assertEqual(r["not_paired"], [])
        row = [x for x in r["rows"] if x["axis"] == "object-hold"][0]
        self.assertEqual((row["a"], row["b"], row["delta"], row["n"], row["label"]), (0.0, 0.67, 0.67, 3, "opened"))
        self.assertEqual((r["hints"]["a"]["late"], r["hints"]["b"]["late"]), (None, 3))
        text = render(r)
        self.assertIn("seals match except the agent's system text", text)
        self.assertIn("late closing calls not recorded → 3", text)

    def test_a_pair_that_differs_elsewhere_is_stamped(self):
        a = _run(None, {1: "object"})
        b = _run("abc", {1: "object"}, extra_seal={"agent_params": {"max_tokens": 16384}, "model": "other"})
        r = compare(a, b)
        self.assertEqual(r["not_paired"], ["agent_params", "model"])
        self.assertIn("NOT PAIRED — the runs also differ in: agent_params, model", render(r))

    def test_same_system_is_a_repeat_not_an_instruction(self):
        a = _run("abc", {1: "object"})
        r = compare(a, _run("abc", {1: "object"}))
        self.assertTrue(r["same_system"])
        self.assertIn("spread of a repeat", render(r))

    def test_repeats_show_the_range_and_overlap_is_not_a_movement(self):
        O, P = "object", "procedure"
        a = [_run(None, {1: P, 2: P, 3: P}), _run(None, {1: O, 2: P, 3: P})]          # 0.00 and 0.33
        b_clear = [_run("abc", {1: O, 2: O, 3: P}), _run("abc", {1: O, 2: O, 3: O})]  # 0.67 and 1.00
        b_noisy = [_run("abc", {1: O, 2: P, 3: P}), _run("abc", {1: O, 2: O, 3: O})]  # 0.33 and 1.00
        clear = [x for x in compare(a, b_clear)["rows"] if x["axis"] == "object-hold"][0]
        self.assertEqual((clear["a"], clear["b"], clear["n"]), (0.17, 0.83, 6))
        self.assertEqual((clear["range_a"], clear["range_b"]), ((0.0, 0.33), (0.67, 1.0)))
        self.assertEqual(clear["label"], "opened")
        noisy = [x for x in compare(a, b_noisy)["rows"] if x["axis"] == "object-hold"][0]
        self.assertEqual(noisy["label"], "within repeat spread")   # 0.33 is in both ranges
        self.assertIn("[0.00–0.33]", render(compare(a, b_clear)))

    def test_repeats_inside_an_arm_must_share_a_seal(self):
        a = [_run(None, {1: "object"}), _run(None, {1: "object"}, extra_seal={"model": "other"})]
        r = compare(a, [_run("abc", {1: "object"})])
        self.assertIn("arm A runs differ in model", r["not_paired"])

    def test_judge_difference_breaks_the_pair(self):
        self.assertEqual(pairing({"model": "m"}, {"model": "m"}, "judge-1", "judge-2"), ["judge"])


class TestUplift(unittest.TestCase):
    def test_uplift_runs_both_arms_interleaved_and_compares(self):
        import contextlib
        import io
        from unittest import mock
        from journeyman import __main__ as m
        calls = []

        def fake_arm(run_args, runs_dir, system_file):
            calls.append((os.path.basename(runs_dir), system_file, tuple(run_args)))
            good = system_file is not None
            return _run("abc" if good else None, {1: "object" if good else "procedure",
                                                  2: "object" if good else "procedure"})
        buf = io.StringIO()
        with mock.patch.object(m, "_run_arm", fake_arm), contextlib.redirect_stdout(buf), \
                self.assertRaises(SystemExit) as cm:
            m.main(["uplift", "--system-file", "sys.txt", "--repeats", "2", "--",
                    "--endpoint", "http://x/v1", "--model", "m"])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual([(c[0], c[1]) for c in calls],
                         [("uplift-A", None), ("uplift-B", "sys.txt")] * 2)
        self.assertEqual(calls[0][2], ("--endpoint", "http://x/v1", "--model", "m"))
        self.assertIn("opened", buf.getvalue())
        self.assertIn("Runs per arm: 2 and 2", buf.getvalue())

    def test_uplift_refuses_a_system_file_in_the_run_arguments(self):
        from journeyman import __main__ as m
        with self.assertRaises(SystemExit) as cm:
            m.main(["uplift", "--system-file", "s", "--", "--endpoint", "x", "--system-file", "other"])
        self.assertIn("drop it", str(cm.exception.code))


if __name__ == "__main__":
    unittest.main()
