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
                    if f.endswith((".html", ".xml", ".csv")):  # bytes must match
                        self.assertEqual(open(committed).read(), open(fresh).read(),
                                         f"site/{rel} differs from a fresh build — "
                                         "edit the source under notes/ or tools/, "
                                         "then run tools/site.py")
            fresh_files = {os.path.relpath(os.path.join(b, f), tmp)
                           for b, _, fs in os.walk(tmp) for f in fs}
            for b, _, fs in os.walk(SITE):
                for f in fs:
                    rel = os.path.relpath(os.path.join(b, f), SITE)
                    self.assertIn(rel, fresh_files,
                                  f"site/{rel} is left over — no source builds it")


def _board():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import board
    return board.rows(BOARD)


class NumbersComeFromRecords(unittest.TestCase):
    def test_every_mechanical_score_appears_in_a_report(self):
        """The mechanical table is the one that still prints decimals."""
        scores = set()
        for agent in os.listdir(BOARD):
            path = os.path.join(BOARD, agent, "report.json")
            if os.path.exists(path):
                for a in json.load(open(path))["axes"].values():
                    if a.get("score") is not None:
                        scores.add(f"{a['score']:.2f}")
        html = open(os.path.join(SITE, "index.html")).read()
        table = html[html.index('<table class="mech">'):html.rindex("</table>")]
        printed = set(re.findall(r">(\d\.\d\d)<span class=\"n\">n=", table))
        self.assertTrue(printed, "no scores parsed — did the table markup change?")
        self.assertTrue(printed <= scores,
                        f"printed but not in any report.json: {printed - scores}")

    def test_every_judged_cell_is_the_record_counted(self):
        """`●●○ 2/3` must be the per_seed record counted, not a rounded score
        re-expanded. The regex that guarded the old decimal notation went quiet
        when the notation changed — this one reads what is actually printed."""
        html = open(os.path.join(SITE, "index.html")).read()
        table = html[html.index('<table class="board">'):html.index("</table>")]
        printed = re.findall(
            r"<tr><td>([^<]+)</td>(.*?)</tr>", table, re.S)
        axes = ["wall-pricing", "empty-measure", "object-hold", "grounding",
                "relief-page", "handoff-verification"]
        rows = {r["agent"]: r for r in _board()}
        checked = 0
        for agent, body in printed:
            if agent not in rows:
                continue
            cells = re.findall(r"<td>(.*?)</td>", body, re.S)
            for axis, cell in zip(axes, cells):
                m = re.search(r'class="kn">(\d+)/(\d+)<', cell)
                a = rows[agent]["axes"].get(axis) or {}
                if not m:
                    self.assertIn(cell.strip(), ("—", "n/a"))
                    continue
                k, n = int(m.group(1)), int(m.group(2))
                per_seed = a.get("per_seed") or {}
                self.assertEqual(n, a.get("n"), f"{agent}/{axis} denominator")
                self.assertEqual(k, sum(1 for v in per_seed.values() if v == 1.0),
                                 f"{agent}/{axis} count")
                checked += 1
        self.assertGreater(checked, 50, "parsed too few judged cells")

    def test_mean_and_field_row_are_recomputed(self):
        html = open(os.path.join(SITE, "index.html")).read()
        table = html[html.index('<table class="board">'):html.index("</table>")]
        rows = {r["agent"]: r for r in _board()}
        for agent, mean, k in re.findall(
                r"<tr><td>([^<]+)</td>.*?(\d\.\d\d)<span class=\"n\">\((\d)\)",
                table, re.S):
            self.assertEqual(float(mean), rows[agent]["mean"], f"{agent} mean")
            self.assertEqual(int(k), rows[agent]["mean_n"], f"{agent} mean axes")
        axes = ["wall-pricing", "empty-measure", "object-hold", "grounding",
                "relief-page", "handoff-verification"]
        tfoot = table[table.index("<tfoot>"):]
        foot = re.findall(r"<td>(\d+)/(\d+)</td>", tfoot)
        self.assertEqual(len(foot), len(axes))
        for axis, (floor, denom) in zip(axes, foot):
            graded = [r for r in rows.values()
                      if (r["axes"].get(axis) or {}).get("score") is not None]
            self.assertEqual(int(denom), len(graded),
                             f"{axis}: the denominator must be what was graded, "
                             "not the cohort size")
            self.assertEqual(int(floor),
                             sum(1 for r in graded if r["axes"][axis]["score"] == 0.0))

    def test_the_run_command_is_readable_on_a_phone(self):
        """Twice now the primary call to action has shipped as one clipped line."""
        html = open(os.path.join(SITE, "index.html")).read()
        block = html[html.index("<pre>"):html.index("</pre>")]
        for line in block.replace("<pre><code>", "").split("\n"):
            self.assertLessEqual(len(line), 60, f"too long to read on a phone: {line}")

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
