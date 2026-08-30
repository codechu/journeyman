#!/usr/bin/env python3
"""Render docs/leaderboard.md from a cohort's sealed reports.

    tools/journeyman_leaderboard.py runs-archive/leaderboard-1-v24-2026-08-24 \
        --cohort "cohort 1, v2.4-judged" --date 2026-08-24 [--notes notes.json]

Rows come from tools/board.py, the same reader the website uses, so the two
surfaces cannot disagree about what a report says.
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from board import markdown, rows  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", help="a cohort directory of <agent>/report.json")
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--notes", default=None, help="sidecar JSON: {model: note}")
    ap.add_argument("--judge-line", default=(
        "the qualified self-hosted judge (Qwen3.6-35B-A3B IQ4_XS, see "
        "[judges.md](judges.md))"))
    args = ap.parse_args()
    notes = json.load(open(args.notes)) if args.notes else {}
    print(markdown(rows(args.directory, notes), args.cohort, args.date,
                   args.judge_line))


if __name__ == "__main__":
    main()
