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

The transformation is the whole contract: a target that is not a URL and
not a bare fragment is a repository path, and gets an absolute prefix at
**the tag being released** — never a branch. A branch name inside a
published description makes the branch load-bearing forever, because the
description cannot be edited afterwards.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "README.md"
DST = ROOT / "README.pypi.md"


def ref():
    """The tag this version will be released under.

    Not a branch. A published description cannot be edited, so a branch
    name in it makes the branch load-bearing forever: rename it and every
    image on every past release page breaks, with no way to repair them.
    A tag is immutable, and it also makes each description point at the
    exact tree that produced the package.
    """
    version = re.search(r'(?m)^version = "([^"]+)"',
                        (ROOT / "pyproject.toml").read_text()).group(1)
    return "v" + version


def render(text, ref_=None):
    r = ref_ or ref()
    blob = f"https://github.com/codechu/journeyman/blob/{r}/"
    raw = f"https://raw.githubusercontent.com/codechu/journeyman/{r}/"

    def local(target):
        return not target.startswith(("http://", "https://", "mailto:", "#"))

    def link(m):
        return m.group(0) if not local(m.group(1)) else "](" + blob + m.group(1) + ")"

    def src(m):
        # Images are HTML here (centred), so they never matched the markdown
        # rewrite and were absolute in the source instead — which is how the
        # branch name got into the published description in the first place.
        return m.group(0) if not local(m.group(2)) else f'{m.group(1)}="{raw}{m.group(2)}"'

    text = re.sub(r"\]\(([^)]+)\)", link, text)
    return re.sub(r'\b(src|href)="([^"]+)"', src, text)


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
