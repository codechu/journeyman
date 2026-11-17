"""Two runs of the same agent, read as a pair: what did the instruction buy?

An agent is run twice on the same scenes and seeds, once without and once
with a system text (`run --system-file`). Read axis by axis, the pair says
more than either run: an axis that was low and opened was missing knowledge;
one that stayed low was not helped by being told; one that fell paid for the
instruction somewhere else (measured 2026-11-14: a "verify before you
report" instruction raised two axes and sank two others, because the report
then arrived after the budget).

The comparison is only as good as the pairing. Everything in the two seals
except the agent's system text has to match — a sampling parameter that
never bound still changed behaviour in the same measurement — so every
other difference is listed and the pair is stamped NOT PAIRED. One run per
arm is a small sample: a difference smaller than one cell is called
unchanged, and n is printed on every row.
"""
import json
import os

from .record import RunDir
from .report import axis_scores

LOW = 0.5   # below this an axis is "low"


def _load(path):
    rd = RunDir.attach(path)
    cells = list(rd.read_cells())
    if not cells:
        raise SystemExit(f"no cells in {path}")
    rep = os.path.join(rd.path, "report.json")
    judge = json.load(open(rep)).get("judge") if os.path.exists(rep) else None
    return cells, cells[0].get("seal") or {}, judge


def pairing(seal_a, seal_b, judge_a, judge_b):
    """What differs between the arms besides the agent's system text."""
    diffs = []
    for k in sorted(set(seal_a) | set(seal_b)):
        if k != "agent_system_md5" and seal_a.get(k) != seal_b.get(k):
            diffs.append(k)
    if judge_a != judge_b:
        diffs.append("judge")
    return diffs


def label(a, b, n):
    """Name the movement; less than one cell's worth is not a movement."""
    if a is None or b is None:
        return "no data"
    step = (1.0 / n if n else 1.0) - 0.006   # scores are rounded to 2 places
    d = b - a
    if d >= step:
        if a >= LOW:
            return "improved"
        return "opened" if b >= LOW else "moved up, still low"
    if d <= -step:
        return "side effect"
    return "still low" if b < LOW else "unchanged"


def _hints(cells):
    valid = [c for c in cells if not c["invalid"]]
    return {"cells": len(cells), "invalid": len(cells) - len(valid),
            # None: records written before the field existed say nothing
            "late": (sum(1 for c in valid if c.get("late_closing"))
                     if any("late_closing" in c for c in valid) else None),
            "calls": sum(c["calls"] for c in valid)}


def compare(path_a, path_b):
    cells_a, seal_a, judge_a = _load(path_a)
    cells_b, seal_b, judge_b = _load(path_b)
    ax_a, ax_b = axis_scores(cells_a), axis_scores(cells_b)
    rows = []
    for axis in sorted(set(ax_a) | set(ax_b)):
        a, b = ax_a.get(axis, {}), ax_b.get(axis, {})
        n = min(a.get("n", 0), b.get("n", 0))
        sa, sb = a.get("score"), b.get("score")
        rows.append({"axis": axis, "a": sa, "b": sb, "n": n,
                     "delta": (round(sb - sa, 2) if sa is not None and sb is not None else None),
                     "label": label(sa, sb, n)})
    return {"a": path_a, "b": path_b,
            "system_a": seal_a.get("agent_system_md5"), "system_b": seal_b.get("agent_system_md5"),
            "not_paired": pairing(seal_a, seal_b, judge_a, judge_b),
            "same_system": seal_a.get("agent_system_md5") == seal_b.get("agent_system_md5"),
            "rows": rows, "hints": {"a": _hints(cells_a), "b": _hints(cells_b)}}


def _n(v):
    return "not recorded" if v is None else v


def render(result):
    f = lambda v: "—" if v is None else f"{v:.2f}"   # noqa: E731
    out = ["JOURNEYMAN — paired comparison", "",
           f"A : {result['a']}  (system {result['system_a'] or 'none'})",
           f"B : {result['b']}  (system {result['system_b'] or 'none'})"]
    if result["not_paired"]:
        out.append("Pair: ⚠ NOT PAIRED — the runs also differ in: "
                   + ", ".join(result["not_paired"])
                   + " — a difference below may come from that, not from the instruction")
    elif result["same_system"]:
        out.append("Pair: same system text in both runs — this reads the spread of a repeat, not an instruction")
    else:
        out.append("Pair: seals match except the agent's system text")
    out += ["", f"{'AXIS':<24}{'A':>6}{'B':>6}{'Δ':>7}{'n':>4}  reading"]
    for r in result["rows"]:
        d = "—" if r["delta"] is None else f"{r['delta']:+.2f}"
        out.append(f"{r['axis']:<24}{f(r['a']):>6}{f(r['b']):>6}{d:>7}{r['n']:>4}  {r['label']}")
    ha, hb = result["hints"]["a"], result["hints"]["b"]
    out += ["", "Where a side effect may come from (A → B):",
            f"  invalid cells {ha['invalid']} → {hb['invalid']} · "
            f"late closing calls {_n(ha['late'])} → {_n(hb['late'])} · tool calls {ha['calls']} → {hb['calls']}",
            "", "One run per arm: a difference under one cell is called unchanged; "
            "repeat the pair before resting anything on a single row."]
    return "\n".join(out)
