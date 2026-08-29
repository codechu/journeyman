#!/usr/bin/env python3
"""Generate README.pypi.md from README.md.

PyPI renders the long description outside the repository, so every
relative link in README.md — LICENSE, docs/, runs-archive/ — would 404
there. README.pypi.md is the same file with those links made absolute.

It was maintained by hand: 268 lines, kept in step by remembering to.
Nothing checked, so a README edit that forgot the copy would ship a
PyPI page one revision behind, and only a reader would notice.

    tools/pypi_readme.py           # rewrite README.pypi.md
    tools/pypi_readme.py --check   # exit 1 if it is out of date

The transformation is the whole contract: a link target that is not a
URL and not a bare fragment is a repository path, and gets BLOB in
front of it. tests/test_readme_pypi.py runs --check.
"""
import pathlib
import re
import sys

BLOB = "https://github.com/codechu/journeyman/blob/master/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "README.md"
DST = ROOT / "README.pypi.md"


def render(text):
    def absolute(m):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        return "](" + BLOB + target + ")"

    return re.sub(r"\]\(([^)]+)\)", absolute, text)


def main(argv):
    want = render(SRC.read_text())
    if "--check" in argv:
        have = DST.read_text() if DST.exists() else ""
        if have == want:
            return 0
        print("README.pypi.md is stale — run tools/pypi_readme.py",
              file=sys.stderr)
        return 1
    DST.write_text(want)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
