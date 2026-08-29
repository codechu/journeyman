"""Report: profile first, composite second, evidence always.

Renders report.md (human) and report.json (machine) from cell records —
the same records the live lines came from; the three views cannot
disagree. Judge stamp sits at the top; self-judged runs carry
NOT COMPARABLE in capitals, not in a footnote.
"""
import json
import re
import os


SCHEMA_VERSION = 1
"""Contract version of report.json — bumped ONLY when the schema changes in
a way that can break a reader, never on an ordinary release. A consumer
pins on this, not on the package version: the package moves for reasons
that do not touch the report at all. Unknown value = stop, do not guess.
1 = the shape published with 0.1.0 (axes carry `kind`)."""


def axis_scores(cells):
    """axis -> {score, per_seed{seed: ratio}, n} from judged verdicts +
    event-layer metrics: judged axes plus pure-event axes."""
    per = {}
    positives = {}
    kinds = {}
    na_means = _na_means_index()
    skipped = {}
    for c in cells:
        if c["invalid"]:
            continue
        for axis, v in (c.get("verdicts") or {}).items():
            # kind is recorded BEFORE the na-skip below: an axis whose every
            # cell was not-applicable still had a judge, and must not read
            # as counted just because no row survived.
            kinds.setdefault(axis, "judged")
            meaning = v.get("na_means") or na_means.get(axis, "failure")
            if v["verdict"] == "na" and meaning == "not-applicable":
                # stimulus never occurred: no evidence either way
                skipped[axis] = skipped.get(axis, 0) + 1
                continue
            per.setdefault(axis, []).append((c["seed"], v["verdict"]))
            positives.setdefault(axis, v.get("positive"))
        for axis, val in (c.get("event_axes") or {}).items():
            # pure-event axis: already a ratio in [0,1], no judge involved
            per.setdefault(axis, []).append((c["seed"], float(val)))
            positives.setdefault(axis, None)
            kinds.setdefault(axis, "counted")
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
                     "per_seed": per_seed, "n": len(allv),
                     "kind": kinds.get(axis, "judged")}
    for axis, k in skipped.items():
        if axis not in out:          # every cell was not-applicable
            out[axis] = {"score": None, "per_seed": {}, "n": 0,
                         "kind": kinds.get(axis, "judged"),
                         "not_applicable": k}
        else:
            out[axis]["not_applicable"] = k
    return out


def _na_means_index():
    from .scene import REGISTRY
    idx = {}
    for cls in REGISTRY.values():
        for item in cls().rubric():
            idx[item.axis] = getattr(item, "na_means", "failure")
    return idx


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
    Heuristic: held = reported under budget; broke = budget-dead.
    TODO: rank by judged verdicts, quote judge evidence."""
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


PRIVATE_HOST = re.compile(
    r"https?://(?:localhost|127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+"
    r"|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+"
    r"|[\w-]+\.local)(?::\d+)?(?:/\S*)?")
POSIX_PATH = re.compile(r"(?:(?<=^)|(?<=[\s(=]))/(?:[^\s/()]+/){1,}[^\s()]*")
WIN_PATH = re.compile(r"(?:(?<=^)|(?<=[\s(=]))[A-Za-z]:\\(?:[^\s\\()]+\\?)+")


def public_label(label):
    """A judge label safe to publish.

    Provenance has to say WHO judged, not where the maintainer keeps their
    files. A private address (RFC1918, loopback, .local) and an absolute
    filesystem path identify a machine, not a judge — and both have shipped
    inside published archives before. They are folded here, at the single
    place the label is written into report.json and report.md.
    """
    if not label:
        return label
    out = PRIVATE_HOST.sub("self-hosted", label)
    out = POSIX_PATH.sub("<path>", out)
    return WIN_PATH.sub("<path>", out)


def render(run_dir, seal, judge_label, self_judged, nonstandard=None,
           judge_meter=None):
    cells = list(run_dir.read_cells())
    axes = axis_scores(cells)
    held, broke = held_and_broke(cells)
    calls = sum(c["calls"] for c in cells)
    tin = sum(c["tokens_in"] for c in cells)
    tout = sum(c["tokens_out"] for c in cells)
    invalid = sum(1 for c in cells if c["invalid"])

    lines = ["JOURNEYMAN — run report", ""]
    stamp = f"Judge : {public_label(judge_label)}"
    if self_judged:
        stamp += "  ⚠ NOT COMPARABLE — self-judged scores"
    if nonstandard:
        stamp += f"\nRun   : ⚠ NON-STANDARD ({nonstandard}) — not comparable to standard runs"
    usage_ok = all(c.get("usage_reported", True) for c in cells if not c["invalid"])
    cost = (f"Cost: {calls} calls · {tin} in / {tout} out tok" if usage_ok else
            f"Cost: {calls} calls · tokens UNREPORTED by endpoint")
    lines += [f"Seal  : {json.dumps(seal, ensure_ascii=False)}", stamp,
              f"Cells : {len(cells)} ({invalid} invalid) · {cost}", "",
              "PROFILE                     score   per-seed           n"]
    for axis, a in sorted(axes.items()):
        seeds = " ".join(f"{v:.2f}" for _, v in sorted(a["per_seed"].items()))
        if a["score"] is None:
            lines.append(f"  {axis:<26}{'n/a':<8}{'stimulus never occurred':<19}"
                         f" {a['n']}  (na ×{a['not_applicable']})")
            continue
        lines.append(f"  {axis:<26}{a['score']:<8}{seeds:<19}{a['n']}")
    if held:
        lines += ["", f"WHERE IT HELD   {held}"]
    if broke:
        lines += [f"WHERE IT BROKE  {broke}"]
    lines += ["", "Repro : journeyman run … (same seal, same seeds; "
              "bit-exact on local llama.cpp with cache_prompt off)"]
    text = "\n".join(lines) + "\n"

    open(os.path.join(run_dir.path, "report.md"), "w").write(text)
    json.dump({"schema_version": SCHEMA_VERSION,
               "seal": seal, "judge": public_label(judge_label),
               "self_judged": self_judged,
               "nonstandard": nonstandard,
               "axes": axes, "judge_cost": judge_meter or {},
               "cost": {"calls": calls, "tokens_in": tin,
                                      "tokens_out": tout},
               "invalid_cells": invalid},
              open(os.path.join(run_dir.path, "report.json"), "w"),
              ensure_ascii=False, indent=1)
    return text


def axis_kinds_from_registry():
    """{axis: "counted"|"judged"} derived STATICALLY from the registered
    scenes: an axis a scene declares but its rubric does not ask about is
    computed from events, so it is counted. No run, no events, no model.

    This is how a report written before `kind` existed can be upgraded —
    but only for axes belonging to scenes this build knows. A run with
    custom scenes (`nonstandard`) carries axes we cannot classify, and we
    do not guess: guessing is the flattening the field exists to prevent.
    """
    from . import scenes  # noqa: F401 — official scenes register on import
    from .scene import REGISTRY
    out = {}
    for cls in REGISTRY.values():
        try:
            judged = {i.axis for i in cls().rubric()}
        except Exception:          # a scene that cannot be built offline
            continue
        for axis in cls.axes:
            out.setdefault(axis, "judged" if axis in judged else "counted")
    return out


def upgrade_axes(report):
    """Backfill `kind` into a report produced before the field existed.
    Returns (report, unclassified) — `unclassified` names the axes left
    without a kind. Authoritative alternative when the run directory
    still exists: `journeyman report <run_dir>` re-renders from the
    cells, where counted and judged already live under separate keys.
    """
    index = axis_kinds_from_registry()
    unclassified = []
    for axis, body in (report.get("axes") or {}).items():
        if "kind" in body:
            continue
        kind = index.get(axis)
        if kind is None:
            unclassified.append(axis)
        else:
            body["kind"] = kind
    if not unclassified:
        # only now does the document actually satisfy the contract; stamping
        # a version onto a report we could not finish would be a lie the
        # next reader has no way to catch
        report.setdefault("schema_version", SCHEMA_VERSION)
    return report, unclassified
