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

    def test_nothing_points_at_a_branch(self):
        """A published description cannot be edited.

        Every past release page keeps whatever URLs it shipped with, so a
        branch named in one is load-bearing forever: rename it and those
        pages break with no way to repair them. Only immutable refs.
        """
        with open(os.path.join(ROOT, "README.pypi.md")) as fh:
            text = fh.read()
        for ref in ("/master/", "/main/", "/HEAD/"):
            self.assertNotIn(ref, text,
                             f"{ref} is a branch; a published description "
                             f"must reference a tag")

    def test_it_points_at_the_tag_for_the_packaged_version(self):
        version = re.search(r'(?m)^version = "([^"]+)"',
                            open(os.path.join(ROOT, "pyproject.toml")).read()
                            ).group(1)
        with open(os.path.join(ROOT, "README.pypi.md")) as fh:
            text = fh.read()
        self.assertIn(f"/v{version}/", text)

    def test_images_are_absolute_too(self):
        """The images are HTML, so the markdown rewrite never touched them.

        That is how a branch name reached the published description: the
        source carried absolute raw URLs because nothing else would have
        made them absolute.
        """
        with open(os.path.join(ROOT, "README.pypi.md")) as fh:
            text = fh.read()
        local = [m for m in re.findall(r'src="([^"]+)"', text)
                 if not m.startswith(("http://", "https://"))]
        self.assertEqual(local, [], f"these would not load on PyPI: {local}")

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
