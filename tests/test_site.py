"""The published site must be a rendering of the records, not a page someone typed.

Two failures this guards against, both of which shipped before it existed:
a number typed into the generator under a footer claiming every number is read
from a report.json, and a note whose chart data was a hand-written array sitting
above the words "regenerated from the sealed reports, not hand-entered".
"""
import contextlib
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
BOARD = os.path.join(ROOT, "runs-archive", "leaderboard-1-v24-2026-08-24")


class SiteIsGenerated(unittest.TestCase):
    def test_committed_site_matches_a_fresh_build(self):
        """If someone edits site/ by hand, this fails and tells them where."""
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import site as _site  # noqa: F401 — shadowed intentionally below
        import importlib
        spec = importlib.util.spec_from_file_location(
            "site_builder", os.path.join(ROOT, "tools", "site.py"))
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                builder.main(site_dir=tmp)
            for base, _, files in os.walk(tmp):
                for f in files:
                    fresh = os.path.join(base, f)
                    rel = os.path.relpath(fresh, tmp)
                    committed = os.path.join(SITE, rel)
                    self.assertTrue(os.path.exists(committed),
                                    f"site/{rel} is missing — run tools/site.py")
                    if f.endswith((".html", ".xml", ".csv")):
                        self.assertEqual(open(committed).read(), open(fresh).read(),
                                         f"site/{rel} differs from a fresh build — "
                                         "edit the source under notes/ or tools/, "
                                         "then run tools/site.py")


class NumbersComeFromRecords(unittest.TestCase):
    def test_every_board_score_appears_in_a_report(self):
        scores = set()
        for agent in os.listdir(BOARD):
            path = os.path.join(BOARD, agent, "report.json")
            if os.path.exists(path):
                for a in json.load(open(path))["axes"].values():
                    if a.get("score") is not None:
                        scores.add(f"{a['score']:.2f}")
        html = open(os.path.join(SITE, "index.html")).read()
        table = html[html.index("<table>"):html.rindex("</table>")]
        printed = set(re.findall(r">(\d\.\d\d)<span class=\"n\">n=", table))
        self.assertTrue(printed, "no scores parsed — did the table markup change?")
        self.assertTrue(printed <= scores,
                        f"printed but not in any report.json: {printed - scores}")

    def test_note_chart_data_equals_its_csv(self):
        slug = "three-verdicts"
        html = open(os.path.join(SITE, "notes", slug, "index.html")).read()
        data = json.loads(html[html.index("const DATA = ") + 13:
                               html.index("];", html.index("const DATA = ")) + 1])
        with open(os.path.join(ROOT, "notes", slug, "ablation.csv")) as f:
            table = [r for r in csv.reader(f)
                     if r and not r[0].startswith("#") and r[0] != "axis"]
        self.assertEqual(len(data), len(table))
        for row, src in zip(data, table):
            self.assertEqual(row["ax"], src[0])
            self.assertAlmostEqual(row["judge"], float(src[1]))
            self.assertAlmostEqual(row["rubric"], float(src[3]))


if __name__ == "__main__":
    unittest.main()
