#!/usr/bin/env python3
"""The badges that state a fact are checked against the fact.

Three of the six assert something rather than reporting it: the Python
floor, the dependency count, and the licence. Nothing read them, so
raising `requires-python`, adding a dependency, or changing the licence
would have left a green badge saying otherwise — and a badge is read as
a measurement, which is what makes a stale one worse than none.

The repository already holds that a badge pointing nowhere is decoration
wearing the costume of a signal. A badge asserting an unchecked fact is
the same costume.

The CI and PyPI badges are not here: they report a live state from the
service that owns it, and there is nothing local to compare them to.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def readme():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        return fh.read()


def project():
    """The three fields, read without `tomllib`.

    `tomllib` arrived in 3.11 and this package supports 3.10, so the test
    that checks the Python-floor badge could not run at the floor the
    badge claims. The matrix caught it; a local run on one interpreter
    never would have.
    """
    text = open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8").read()

    def field(name):
        m = re.search(rf'(?m)^{name} = "([^"]+)"', text)
        return m.group(1) if m else None

    m = re.search(r"(?ms)^dependencies = \[(.*?)\]", text)
    deps = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    return {"requires-python": field("requires-python"),
            "license": field("license"),
            "dependencies": deps}


class TestBadgesStateTheTruth(unittest.TestCase):
    def test_python_floor_matches_requires_python(self):
        m = re.search(r"badge/python-([\d.]+)%2B-", readme())
        self.assertTrue(m, "the Python badge changed shape; update this test")
        floor = project()["requires-python"]
        self.assertEqual(
            floor, ">=" + m.group(1),
            f"the badge says {m.group(1)}+ and pyproject says {floor}")

    def test_dependency_count_matches(self):
        m = re.search(r"badge/dependencies-(\d+)-", readme())
        self.assertTrue(m, "the dependency badge changed shape")
        declared = project().get("dependencies") or []
        self.assertEqual(int(m.group(1)), len(declared),
                         f"the badge says {m.group(1)} dependencies and "
                         f"pyproject declares {declared}")

    def test_licence_matches(self):
        # shields escapes a literal "-" as "--", and the trailing segment
        # is the colour. A non-greedy match stops at the first dash and
        # reads "Apache" out of "Apache--2.0" — which is how this test
        # failed on its first run, against a badge that was correct.
        m = re.search(r"badge/license-(.+)-[a-z]+\)", readme())
        self.assertTrue(m, "the licence badge changed shape")
        shown = m.group(1).replace("--", "-")
        self.assertEqual(shown, project()["license"],
                         f"the badge says {shown} and pyproject says "
                         f"{project()['license']}")

    def test_every_badge_is_a_link(self):
        # Same rule as the vitrine standard, held here rather than assumed.
        row = [l for l in readme().splitlines() if l.startswith("[![")]
        self.assertTrue(row, "no badge row found")
        for line in row:
            self.assertRegex(line, r"^\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)$",
                             f"badge is not a link: {line}")


if __name__ == "__main__":
    unittest.main()
