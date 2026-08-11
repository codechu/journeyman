"""Report: profile first, composite second, evidence always.

Renders report.md (human) and report.json (machine) from cell records —
the same records the live lines came from; the three views cannot
disagree. Judge stamp sits at the top; self-judged runs carry
NOT COMPARABLE in capitals, not in a footnote.
"""
import json
import os


def axis_scores(cells):
    """axis -> {score, per_seed{seed: ratio}, n} from judged verdicts +
    event-layer metrics. Skeleton: judged axes only; event-axes attach
    with the real scenes (TODO(muscle))."""
    per = {}
    positives = {}
    for c in cells:
        if c["invalid"]:
            continue
        for axis, v in (c.get("verdicts") or {}).items():
            per.setdefault(axis, []).append((c["seed"], v["verdict"]))
            positives.setdefault(axis, v.get("positive"))
        for axis, val in (c.get("event_axes") or {}).items():
            # pure-event axis: already a ratio in [0,1], no judge involved
            per.setdefault(axis, []).append((c["seed"], float(val)))
            positives.setdefault(axis, None)
    out = {}
    for axis, rows in per.items():
        positive = positives.get(axis)
        seeds = {}
        for seed, verdict in rows:
            ok = (float(verdict) if positive is None
                  else (1.0 if verdict == positive else 0.0))
            seeds.setdefault(seed, []).append(ok)
        per_seed = {s: round(sum(v) / len(v), 2) for s, v in seeds.items()}
        allv = [x for v in seeds.values() for x in v]
        out[axis] = {"score": round(sum(allv) / len(allv), 2),
                     "per_seed": per_seed, "n": len(allv)}
    return out


def _closing_text(cell):
    """The agent's own closing words live in the report/conclude tool
    call, not in final_text — quote from there when final_text is empty."""
    import json as _json
    text = ""
    for m in cell.get("messages") or []:
        for tc in (m.get("tool_calls") or []):
            fn = tc["function"]
            if fn["name"] in ("report", "conclude"):
                try:
                    args = _json.loads(fn.get("arguments") or "{}")
                except ValueError:
                    continue
                text = args.get("text") or args.get("decision") or text
    return text


def held_and_broke(cells):
    """Signature section: best and worst cell, with the agent's own words.
    Skeleton heuristic: held = reported under budget; broke = budget-dead.
    TODO(muscle): rank by judged verdicts, quote judge evidence."""
    held = broke = None
    for c in cells:
        if c["invalid"]:
            continue
        ev = c.get("events") or {}
        if (ev.get("reported") or ev.get("concluded")) and not held:
            quote = (c.get("final_text") or _closing_text(c))[:140]
            held = f"{c['cell_id']} — \"{quote}\""
        if ev.get("budget_dead") and not broke:
            broke = (f"{c['cell_id']} — budget died after {c['calls']} calls; "
                     f"no closing report")
    return held, broke


def render(run_dir, seal, judge_label, self_judged, nonstandard=None):
    cells = list(run_dir.read_cells())
    axes = axis_scores(cells)
    held, broke = held_and_broke(cells)
    calls = sum(c["calls"] for c in cells)
    tin = sum(c["tokens_in"] for c in cells)
    tout = sum(c["tokens_out"] for c in cells)
    invalid = sum(1 for c in cells if c["invalid"])

    lines = ["JOURNEYMAN — run report", ""]
    stamp = f"Judge : {judge_label}"
    if self_judged:
        stamp += "  ⚠ NOT COMPARABLE — self-judged scores"
    if nonstandard:
        stamp += f"\nRun   : ⚠ NON-STANDARD ({nonstandard}) — not comparable to standard runs"
    usage_ok = all(c.get("usage_reported", True) for c in cells if not c["invalid"])
    cost = (f"Cost: {calls} calls · {tin} in / {tout} out tok" if usage_ok else
            f"Cost: {calls} calls · tokens UNREPORTED by endpoint")
    lines += [f"Seal  : {json.dumps(seal, ensure_ascii=False)}", stamp,
              f"Cells : {len(cells)} ({invalid} invalid) · {cost}", "",
              "PROFILE                     score   per-seed    n"]
    for axis, a in sorted(axes.items()):
        seeds = " ".join(f"{v:.2f}" for _, v in sorted(a["per_seed"].items()))
        lines.append(f"  {axis:<26}{a['score']:<8}{seeds:<12}{a['n']}")
    if held:
        lines += ["", f"WHERE IT HELD   {held}"]
    if broke:
        lines += [f"WHERE IT BROKE  {broke}"]
    lines += ["", "Repro : journeyman run … (same seal, same seeds; "
              "bit-exact on local llama.cpp with cache_prompt off)"]
    text = "\n".join(lines) + "\n"

    open(os.path.join(run_dir.path, "report.md"), "w").write(text)
    json.dump({"seal": seal, "judge": judge_label, "self_judged": self_judged,
               "nonstandard": nonstandard,
               "axes": axes, "cost": {"calls": calls, "tokens_in": tin,
                                      "tokens_out": tout},
               "invalid_cells": invalid},
              open(os.path.join(run_dir.path, "report.json"), "w"),
              ensure_ascii=False, indent=1)
    return text
