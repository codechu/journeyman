#!/usr/bin/env python3
"""The README's badge summary follows the ledger.

docs/judges.md is the source of who holds a badge; the README carries a
one-paragraph summary of it. Twice that summary fell behind a ledger
change that did not touch the README (0.5.0, and the Qwen3.6 re-exam that
followed it). This test makes the drift fail instead of waiting to be
noticed: every judge holding a badge in the current ledger section must
be named in the README's badge paragraph, and every exam date written in
that ledger row must appear there too.

Two tamper checks keep the test honest: a README that drops a date, and a
ledger that gains a badge holder, must both fail.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def current_ledger(judges_md):
    """The first '## The ledger' section — the rubric text in force."""
    m = re.search(r"^## The ledger.*?$(.*?)(?=^## )", judges_md, re.M | re.S)
    if not m:
        raise AssertionError("docs/judges.md has no '## The ledger' section")
    return m.group(1)


def holders(ledger):
    """(name, dates in the judge cell) for every **QUALIFIED** row."""
    out = []
    for line in ledger.splitlines():
        if not line.startswith("|") or "**QUALIFIED**" not in line:
            continue
        cell = line.split("|")[1]
        name = re.search(r"\*\*(.+?)\*\*", cell)
        if name:
            out.append((name.group(1).split(" + ")[0].strip(), DATE.findall(cell)))   # "X + identity" is a configuration of X
    return out


def badge_paragraph(readme):
    m = re.search(r"^- \*\*Who holds a badge now\*\*(.*?)(?=^- \*\*|^## )", readme, re.M | re.S)
    if not m:
        raise AssertionError("README has no 'Who holds a badge now' paragraph")
    return " ".join(m.group(1).split())


def segments(para, names):
    """Text after each mention of a name, up to the next mention of any holder (a date must sit in its holder's own segment)."""
    pos = sorted((m.start(), n) for n in names for m in re.finditer(re.escape(n), para))
    seg = {}
    for i, (p, n) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(para)
        seg.setdefault(n, []).append(para[p:end])
    return seg


def missing(judges_md, readme):
    para = badge_paragraph(readme); H = holders(current_ledger(judges_md)); gaps = []
    seg = segments(para, {n for n, _ in H})
    for name, dates in H:
        if name not in seg:
            gaps.append(f"{name}: not named"); continue
        gaps += [f"{name}: exam date {d} not beside its name" for d in dates if not any(d in s for s in seg[name])]
    return sorted(set(gaps))


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as fh:
        return fh.read()


class TestReadmeBadgeSync(unittest.TestCase):
    def setUp(self):
        self.judges, self.readme = read("docs", "judges.md"), read("README.md")

    def test_summary_follows_ledger(self):
        self.assertTrue(holders(current_ledger(self.judges)), "no badge holder parsed — the parser, not the README, is broken")
        self.assertEqual(missing(self.judges, self.readme), [])

    def test_tamper_dropped_date_fails(self):
        dates = {d for _, ds in holders(current_ledger(self.judges)) for d in ds}
        self.assertTrue(dates, "ledger rows carry no dates — tamper check cannot run")
        d = sorted(dates)[0]
        self.assertTrue(missing(self.judges, self.readme.replace(d, "XXXX-XX-XX")))

    def test_catches_the_drift_it_was_born_from(self):
        """The README as it stood before 242db6c: Qwen3.6 dated 2026-08-24 after its 2026-11-12 re-exam (md.47: the guard must fire on its own origin case)."""
        old = self.readme.replace("Qwen3.6-35B-A3B (re-examined 2026-11-12:", "Qwen3.6-35B-A3B (2026-08-24;")
        self.assertNotEqual(old, self.readme, "fixture replacement did not apply — README wording changed")
        self.assertIn("Qwen3.6-35B-A3B: exam date 2026-11-12 not beside its name", missing(self.judges, old))

    def test_tamper_new_holder_fails(self):
        row = "| **Imaginary-9B** (self-hosted) — 2099-01-01 | local | 1.0 | **QUALIFIED** — invented |\n"
        led = re.sub(r"(^## The ledger.*?$\n\n\|[^\n]*\n\|[^\n]*\n)", r"\1" + row, self.judges, count=1, flags=re.M | re.S)
        self.assertIn("Imaginary-9B", led)
        self.assertTrue(any("Imaginary-9B" in g for g in missing(led, self.readme)))


if __name__ == "__main__":
    unittest.main()
