#!/usr/bin/env python3
"""The release notes come from CHANGELOG.md; this runs the shipped extractor.

Not a copy of it — the script is pulled out of `.github/workflows/release.yml`
and executed, so the test cannot pass on a workflow that has since changed.

Two failures it holds shut, both found by reading the old version:
  * the pattern required a following `## `, so the newest section matched
    only because older ones sat under it — a first release, or a changelog
    whose older entries had been archived, fell through;
  * the fall-through wrote "No CHANGELOG section for X." and the release
    published anyway, with a body indistinguishable from a real one.
"""
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "release.yml")


def extractor():
    """The python heredoc the release workflow actually runs."""
    body = open(WORKFLOW, encoding="utf-8").read()
    m = re.search(r"<<'PY'\n(.*?)\n\s*PY\n", body, re.S)
    assert m, "release.yml no longer embeds a PY heredoc"
    return textwrap.dedent(m.group(1))


def run(changelog, version):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "CHANGELOG.md"), "w") as fh:
            fh.write(changelog)
        script = os.path.join(d, "notes.py")
        with open(script, "w") as fh:
            fh.write(extractor())
        return subprocess.run([sys.executable, script, version], cwd=d,
                              capture_output=True, text=True)


class TestReleaseNotes(unittest.TestCase):
    def test_it_reads_the_section_for_the_version(self):
        p = run("# Changelog\n\n## 1.2.3 — 2026-01-01\n\n- a thing\n\n"
                "## 1.2.2 — 2025-12-01\n\n- older\n", "1.2.3")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "- a thing")

    def test_the_only_section_still_matches(self):
        p = run("# Changelog\n\n## 1.0.0 — 2026-01-01\n\n- the first\n", "1.0.0")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "- the first")

    def test_a_missing_section_fails_instead_of_publishing_a_placeholder(self):
        p = run("# Changelog\n\n## 9.9.9 — 2026-01-01\n\n- other\n", "1.0.0")
        self.assertNotEqual(p.returncode, 0,
                            "a release with no changelog entry must not "
                            "publish a placeholder body")
        self.assertIn("1.0.0", p.stderr)

    def test_an_empty_section_fails_too(self):
        p = run("# Changelog\n\n## 1.0.0 — 2026-01-01\n\n## 0.9.0\n\n- old\n",
                "1.0.0")
        self.assertNotEqual(p.returncode, 0, "an empty section is not notes")

    def test_the_packaged_version_has_notes_today(self):
        version = re.search(r'^version = "([^"]+)"',
                            open(os.path.join(ROOT, "pyproject.toml")).read(),
                            re.M).group(1)
        changelog = open(os.path.join(ROOT, "CHANGELOG.md"),
                         encoding="utf-8").read()
        p = run(changelog, version)
        self.assertEqual(p.returncode, 0,
                         f"cutting {version} today would fail: {p.stderr}")
        self.assertTrue(p.stdout.strip())


if __name__ == "__main__":
    unittest.main()
