#!/usr/bin/env python3
"""The release guide is checked against the pipeline it describes.

It drifted once already, in both directions at the same time: a helper
script came back and the guide never mentioned it, while a step still
instructed `gh release create` months after the workflow began doing it
from the tag. Following it literally would have created the release by
hand and left the workflow to collide with it.

A guide is prose, and prose drifts silently. These are the two claims
that can be checked against the other side rather than against a fixture.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "docs", "versioning.md")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "release.yml")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class TestReleaseDoc(unittest.TestCase):
    def setUp(self):
        self.doc = read(DOC)
        i = self.doc.index("## Cutting a release")
        j = self.doc.index("## Standing rules")
        self.section = self.doc[i:j]

    def test_every_tool_it_names_exists(self):
        named = set(re.findall(r"`(tools/[\w./-]+\.py)", self.section))
        self.assertTrue(named, "the guide names no tooling at all")
        for path in named:
            self.assertTrue(os.path.exists(os.path.join(ROOT, path)),
                            f"the guide tells the operator to run {path}, "
                            f"which does not exist")

    def test_it_names_the_tools_the_release_actually_uses(self):
        for path in ("tools/bump.py", "tools/pypi_readme.py"):
            self.assertIn(path, self.section,
                          f"{path} is part of cutting a release and the guide "
                          f"does not mention it")

    def test_it_does_not_instruct_a_step_the_workflow_owns(self):
        workflow = read(WORKFLOW)
        if "gh release create" not in workflow:
            self.skipTest("the workflow no longer creates the release")
        # The guide may forbid the command; it may not instruct it. The
        # exemption is the exact phrase "do not" — an earlier version of
        # this test exempted any line containing "not", and `--notes-file`
        # carries one, so the check passed on the very line it was written
        # to catch.
        for line in self.section.splitlines():
            if "gh release create" in line and "do not" not in line.lower():
                self.fail("the workflow creates the GitHub release from the "
                          "tag; the guide still instructs it by hand: "
                          + line.strip())


if __name__ == "__main__":
    unittest.main()
