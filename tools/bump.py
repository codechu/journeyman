#!/usr/bin/env python3
"""Move the version in the four places that carry it, together.

The version lives in pyproject.toml, journeyman/__init__.py, CITATION.cff and
.zenodo.json. The test suite checks they agree; nothing was moving them, so
they were moved by hand, and 0.1.1 went out with one bumped and three behind.
The package said 0.1.1 while every report it produced was stamped 0.1.0.

    tools/bump.py 0.1.3        # edit the four, then add the changelog entry

It does not tag, commit, or push: the tag is the release signature and stays
a deliberate act. It also refuses to run if the four disagree beforehand,
because starting from a drifted state hides which one was wrong.
"""
import json
import pathlib
import re
import sys

FILES = {
    "pyproject.toml": (r'(?m)^version = "([^"]+)"', 'version = "{v}"'),
    "journeyman/__init__.py": (r'(?m)^__version__ = "([^"]+)"', '__version__ = "{v}"'),
    "CITATION.cff": (r'(?m)^version: (\S+)', 'version: {v}'),
}


def current():
    seen = {}
    for f, (pat, _) in FILES.items():
        seen[f] = re.search(pat, pathlib.Path(f).read_text()).group(1)
    seen[".zenodo.json"] = json.loads(pathlib.Path(".zenodo.json").read_text())["version"]
    return seen


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", argv[1]):
        print(__doc__)
        return 64
    new = argv[1]
    seen = current()
    if len(set(seen.values())) != 1:
        print("refusing: the four already disagree — fix that first, since "
              "starting from a drifted state hides which one was wrong")
        for f, v in seen.items():
            print(f"  {f}: {v}")
        return 1
    old = next(iter(seen.values()))
    for f, (pat, repl) in FILES.items():
        p = pathlib.Path(f)
        p.write_text(re.sub(pat, repl.format(v=new), p.read_text(), count=1))
    z = pathlib.Path(".zenodo.json")
    d = json.loads(z.read_text())
    d["version"] = new
    z.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print(f"{old} -> {new} in {len(FILES) + 1} files")
    print("next: write the CHANGELOG entry, run the suite, then tag")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
