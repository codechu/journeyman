#!/usr/bin/env python3
"""The README terminal image is drawn from a real run log, not by hand.

It was hand-drawn once and stayed at v0.0.5 with seven scenes while the
package moved to 0.5.0 and ten. `tools/terminal_svg.py` now renders it
from a log; this test fails when the image is not that tool's output, or
when its banner version is behind the package by a major or minor step
(a patch release does not demand a fresh run).
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def banner_version(svg):
    m = re.search(r"JOURNEYMAN (v[\d.]+)", svg)
    return m.group(1) if m else None


def behind(img, pkg):
    """True when the image's major.minor is older than the package's."""
    a = tuple(int(x) for x in img.lstrip("v").split(".")[:2]); b = tuple(int(x) for x in pkg.split(".")[:2])
    return a < b


class TestTerminalSvg(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "assets", "terminal.svg"), encoding="utf-8") as fh:
            self.svg = fh.read()
        import journeyman
        self.pkg = journeyman.__version__

    def test_drawn_from_a_log(self):
        self.assertIn("real log, abridged", self.svg, "terminal.svg was not rendered by tools/terminal_svg.py")

    def test_not_behind_the_package(self):
        v = banner_version(self.svg)
        self.assertIsNotNone(v, "no banner version in terminal.svg")
        self.assertFalse(behind(v, self.pkg), f"terminal.svg shows {v}, package is {self.pkg} — rerun and render: tools/terminal_svg.py")

    def test_tamper(self):
        self.assertTrue(behind("v0.0.5", "0.5.0"))
        self.assertFalse(behind("v0.5.0", "0.5.3"))
        self.assertEqual(banner_version(self.svg.replace("JOURNEYMAN v", "JOURNEYMAN-v")), None)


if __name__ == "__main__":
    unittest.main()
