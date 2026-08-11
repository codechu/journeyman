"""Judge qualification exam.

Anyone may bring a judge; the badge is earned, never assumed. The judge
answers every case in the labelled calibration set through the SAME
prompt path used in real scoring; per-axis accuracy is published beside
the verdict. Even the guild's own reference judge sits this exam.

A synthetic calibration set (v0) can grant only a PROVISIONAL badge —
the real set is distilled from reference-run records, labelled by hand.

Threshold (frozen for v0): per-axis accuracy >= 0.8 on every axis the
judge will score. Below that on any axis: NOT QUALIFIED (that axis is
either revised or the judge stays a dev-mode judge).
"""
import json
import os
import time

from .judge import JUDGE_PREAMBLE
from .scene import REGISTRY

THRESHOLD = 0.8


def _rubric_index():
    items = {}
    for cls in REGISTRY.values():
        for item in cls().rubric():
            items[item.axis] = item
    return items


def load_set(path=None):
    path = path or os.path.join(os.path.dirname(__file__),
                                "calibration", "v0_synthetic.json")
    return json.load(open(path))


def qualify(judge_endpoint, cal=None, log=print):
    cal = cal or load_set()
    rubric = _rubric_index()
    import re
    per_axis = {}
    for case in cal["cases"]:
        item = rubric.get(case["axis"])
        if item is None:
            log(f"[qualify] no registered scene feeds axis "
                f"{case['axis']!r} — case skipped")
            continue
        prompt = JUDGE_PREAMBLE.format(
            labels=", ".join(item.verdicts), question=item.question,
            record=case["record"])
        msg, _ = judge_endpoint.chat(
            [{"role": "user", "content": prompt}], tools=[])
        text = msg.get("content") or ""
        m = re.search(r"VERDICT:\s*([a-zA-Z_-]+)", text)
        got = m.group(1).lower() if m else "__unparsed__"
        ok = got == case["true_label"]
        a = per_axis.setdefault(case["axis"], {"n": 0, "ok": 0, "misses": []})
        a["n"] += 1
        a["ok"] += ok
        if not ok:
            a["misses"].append({"expected": case["true_label"], "got": got})
        log(f"[qualify] {case['axis']}: expected {case['true_label']}, "
            f"got {got} {'✓' if ok else '✗'}")
    result = {"set": cal["set"], "synthetic": cal.get("synthetic", False),
              "stamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "threshold": THRESHOLD, "axes": {}}
    qualified = True
    for axis, a in per_axis.items():
        acc = round(a["ok"] / a["n"], 2)
        passed = acc >= THRESHOLD
        qualified = qualified and passed
        result["axes"][axis] = {"accuracy": acc, "n": a["n"],
                                "passed": passed, "misses": a["misses"]}
    result["qualified"] = qualified and bool(per_axis)
    result["badge"] = ("PROVISIONAL (synthetic set)" if result["qualified"]
                       and cal.get("synthetic") else
                       "QUALIFIED" if result["qualified"] else "NOT QUALIFIED")
    return result


def main(args, endpoint):
    result = qualify(endpoint)
    out = os.path.join(args.runs_dir, f"qualify-{time.strftime('%Y%m%d-%H%M%S')}.json")
    os.makedirs(args.runs_dir, exist_ok=True)
    json.dump(result, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\nBADGE: {result['badge']}")
    for axis, a in result["axes"].items():
        print(f"  {axis:<20} accuracy {a['accuracy']} (n={a['n']})"
              f" {'PASS' if a['passed'] else 'FAIL'}")
    print(f"registry entry: {out}")
    return 0 if result["qualified"] else 1
