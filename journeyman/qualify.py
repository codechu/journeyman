"""Judge qualification exam.

Anyone may bring a judge; the badge is earned, never assumed. The judge
answers every case in the labelled calibration set through the SAME
prompt path used in real scoring; per-axis accuracy is published beside
the verdict. Even the guild's own reference judge sits this exam.

A synthetic calibration set (v0) can grant only a PROVISIONAL badge —
the real set is distilled from reference-run records, labelled by a blind
three-labeller panel with maintainer adjudication on contested cases.

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
                                "calibration", "v2_real.json")
    return json.load(open(path))


def qualify(judge_endpoint, cal=None, log=print, repeats=3, early_exit=False,
            evidence=False):
    """repeats: judge draws per case, majority vote. A badge is a decision;
    a single stochastic draw is noise (a well-calibrated judge can still
    hallucinate one label), so each case is asked an odd number of times and
    the majority label is scored. repeats=1 restores the old single-draw path.

    evidence: hand the judge deterministic event-counts computed from each
    record (see evidence.py) as prepared facts. Changes what is being
    examined, so the badge is labelled separately: an evidence-fed badge
    never masquerades as a bare one.
    """
    cal = cal or load_set()
    rubric = _rubric_index()
    import re
    from collections import Counter
    # per-axis case totals, for mathematical elimination (early_exit)
    axis_total = Counter(c["axis"] for c in cal["cases"])
    per_axis = {}
    eliminated = None
    for case in cal["cases"]:
        item = rubric.get(case["axis"])
        if item is None:
            log(f"[qualify] no registered scene feeds axis "
                f"{case['axis']!r} — case skipped")
            continue
        ev = ""
        if evidence:
            from .evidence import event_counts, render_block
            ev = render_block(event_counts(case["record"]))
        prompt = JUDGE_PREAMBLE.format(
            labels=", ".join(item.verdicts), question=item.question,
            evidence=ev, record=case["record"])
        draws = []
        for _ in range(repeats):
            # transient network faults must not void a whole exam: one
            # timed-out call killed a 51-case run on its last case
            # (2026-08-20). Three attempts, then the exam fails loudly.
            for attempt in range(3):
                try:
                    msg, _ = judge_endpoint.chat(
                        [{"role": "user", "content": prompt}], tools=[])
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    print(f"[qualify] transient judge error, retrying: {e}")
                    # 429s answer immediate retries with more 429s — an
                    # unslept retry loop is the impolite one (2026-08-22)
                    time.sleep(5 * (attempt + 1))
            text = msg.get("content") or ""
            m = re.search(r"VERDICT:\s*([a-zA-Z_-]+)", text)
            # labels are declared with hyphens; judges sometimes echo them
            # with underscores — same label, not a miss (measured 2026-08-19)
            draws.append(m.group(1).lower().replace("_", "-") if m
                         else "__unparsed__")
        got = Counter(draws).most_common(1)[0][0]   # majority label
        ok = got == case["true_label"]
        a = per_axis.setdefault(case["axis"], {"n": 0, "ok": 0, "misses": []})
        a["n"] += 1
        a["ok"] += ok
        if not ok:
            a["misses"].append({"expected": case["true_label"], "got": got,
                                 "draws": draws,
                                 # audit anchor: without it, mapping a miss
                                 # back to its case needs order-forensics
                                 # (bitten twice, 2026-08-20)
                                 "record_head": case["record"][:80],
                                 # the head is the scene's system line —
                                 # identical across a scene's cases, so it
                                 # could not tell two grounding cases apart
                                 # (2026-08-23); the id can
                                 "case_id": f"{case['axis']}-{__import__('hashlib').md5(case['record'].encode()).hexdigest()[:8]}"})
        log(f"[qualify] {case['axis']}: expected {case['true_label']}, "
            f"got {got} {'✓' if ok else '✗'}"
            + (f"  draws={draws}" if repeats > 1 else ""))
        if early_exit:
            ax = case["axis"]
            best = (axis_total[ax] - (a["n"] - a["ok"])) / axis_total[ax]
            if best < THRESHOLD:   # axis can no longer reach the bar
                eliminated = ax
                log(f"[qualify] EARLY EXIT — {ax} can no longer reach "
                    f"{THRESHOLD} ({a['n'] - a['ok']} misses of "
                    f"{axis_total[ax]} total); remaining cases skipped")
                break
    result = {"set": cal["set"], "synthetic": cal.get("synthetic", False),
              "stamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "threshold": THRESHOLD, "evidence_fed": bool(evidence),
              # audit anchor: a registry row that does not pin WHO sat the
              # exam forces name-forensics later (bitten 2026-08-22 — the
              # ledger table had to be reassembled from file names and
              # campaign notes)
              "judge_model": getattr(judge_endpoint, "model", None),
              "judge_endpoint": getattr(judge_endpoint, "url", None),
              "axes": {}}
    qualified = True
    for axis, a in per_axis.items():
        acc = round(a["ok"] / a["n"], 2)
        passed = acc >= THRESHOLD
        qualified = qualified and passed
        result["axes"][axis] = {"accuracy": acc, "n": a["n"],
                                "passed": passed, "misses": a["misses"]}
    result["qualified"] = qualified and bool(per_axis) and eliminated is None
    if eliminated:
        result["early_exit"] = eliminated
    result["badge"] = ("PROVISIONAL (synthetic set)" if result["qualified"]
                       and cal.get("synthetic") else
                       "QUALIFIED" if result["qualified"] else "NOT QUALIFIED")
    if evidence and result["qualified"] and not cal.get("synthetic"):
        result["badge"] = "QUALIFIED (evidence-fed)"
    return result


def main(args, endpoint):
    cal = load_set(getattr(args, "cal_set", None))
    result = qualify(endpoint, cal=cal, repeats=getattr(args, "repeats", 3),
                     early_exit=getattr(args, "early_exit", False),
                     evidence=getattr(args, "evidence", False))
    out = os.path.join(args.runs_dir, f"qualify-{time.strftime('%Y%m%d-%H%M%S')}.json")
    os.makedirs(args.runs_dir, exist_ok=True)
    json.dump(result, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\nBADGE: {result['badge']}")
    for axis, a in result["axes"].items():
        print(f"  {axis:<20} accuracy {a['accuracy']} (n={a['n']})"
              f" {'PASS' if a['passed'] else 'FAIL'}")
    print(f"registry entry: {out}")
    return 0 if result["qualified"] else 1
