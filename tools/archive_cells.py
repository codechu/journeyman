#!/usr/bin/env python3
"""Publish a run's cell records next to its archived report.

A report shows scores; the cells show what the agent did and what the judge
answered, which is what a re-scoring or a second opinion needs. Records are
written one JSON line per cell into <dest>/cells.jsonl.zst, after folding
what identifies the maintainer's machine instead of the run:

  - private hosts and absolute paths in the fields that describe the run
    (report.public_label) — never in the transcript, the judge's reasoning
    or the scene's events: the paths there belong to the scene's world
    (`/srv/app/logs/crash.log`), and on wall-pricing they are the evidence,
  - opaque provider blobs (encrypted reasoning) — replaced by their length.

Usage: tools/archive_cells.py <run dir with cells/> <dest dir>
"""
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from journeyman.report import public_label  # noqa: E402

OPAQUE_MIN = 2000


WORLD = ("messages", "verdicts", "final_text", "events", "event_axes")   # the scene's own content


def fold(o, key=None, world=False):
    if isinstance(o, dict):
        return {k: fold(v, k, world or k in WORLD) for k, v in o.items()}
    if isinstance(o, list):
        return [fold(v, key, world) for v in o]
    if isinstance(o, str):
        if key == "data" and len(o) >= OPAQUE_MIN and " " not in o[:200]:
            return f"<opaque provider blob removed: {len(o)} chars>"
        return o if world else public_label(o)
    return o


def main(src, dest):
    files = sorted(glob.glob(os.path.join(src, "cells", "*.json")))
    if not files:
        sys.exit(f"no cells under {src}")
    os.makedirs(dest, exist_ok=True)
    lines = [json.dumps(fold(json.load(open(f))), ensure_ascii=False, sort_keys=True)
             for f in files]
    out = os.path.join(dest, "cells.jsonl.zst")
    subprocess.run(["zstd", "-19", "-q", "-f", "-o", out],
                   input=("\n".join(lines) + "\n").encode(), check=True)
    print(f"{out}: {len(lines)} cells, {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main(*sys.argv[1:3])
