#!/usr/bin/env python3
"""README.pypi.md is generated, and nothing relative survives in it.

Two assertions, because the first one alone would pass on a generator
that had stopped rewriting anything: the copy matches what the tool
produces today, AND no link in it still points at a repository path
that PyPI cannot resolve.
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "pypi_readme.py")


class TestPypiReadme(unittest.TestCase):
    def test_copy_is_current(self):
        r = subprocess.run([sys.executable, TOOL, "--check"],
                           capture_output=True, text=True)
        self.assertEqual(
            r.returncode, 0,
            "README.pypi.md is stale — run tools/pypi_readme.py\n"
            + r.stderr)

    def test_no_relative_links_survive(self):
        with open(os.path.join(ROOT, "README.pypi.md")) as fh:
            text = fh.read()
        relative = [t for t in re.findall(r"\]\(([^)]+)\)", text)
                    if not t.startswith(("http://", "https://",
                                         "mailto:", "#"))]
        self.assertEqual(relative, [],
                         "these would 404 on PyPI: %r" % (relative,))


if __name__ == "__main__":
    unittest.main()
