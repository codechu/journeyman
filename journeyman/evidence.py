"""Deterministic event-counts extracted from a rendered record.

The two scoring layers of this project — counted events and judged
rubrics — meet here: the counts a machine can take from the record are
handed to the judge as prepared evidence, so the judge spends its
attention on what the counts MEAN, not on re-counting. The counts are
facts; the verdict stays the judge's.

An evidence line must be earned before it is trusted: this extractor is
calibrated against the labelled set's mechanically-decidable cases (see
the registry notes) — repeated-call streaks, report/wake call counts and
unique-output ratios reproduce the known ground exactly, or the flag
does not ship.

Everything here is pure text arithmetic over the record rendering
(`[CALL] name({args})` / `[tool] ...` lines). No model, no judgment.
"""
import json
import re


def _calls_and_results(record_text):
    """Ordered list of (call_line, following_tool_output) pairs plus the
    raw call lines. A [tool] block belongs to the nearest preceding call."""
    lines = record_text.split("\n")
    calls = []            # (call_signature, result_text)
    current = None        # signature of the last seen call
    buf = []
    def flush():
        nonlocal buf, current
        if current is not None:
            calls.append((current, "\n".join(buf).strip()))
        buf, current = [], None
    for ln in lines:
        if ln.startswith("[CALL] "):
            flush()
            current = ln[7:].strip()
        elif ln.startswith("[tool]"):
            buf.append(ln[6:].strip())
        elif ln.startswith("[") and buf:
            # next speaker: the tool block ended
            flush()
        elif current is not None and buf:
            buf.append(ln.strip())
    flush()
    return calls


def event_counts(record_text):
    calls = _calls_and_results(record_text)
    names = []
    for sig, _ in calls:
        m = re.match(r"([\w.-]+)\(", sig)
        names.append(m.group(1) if m else sig[:24])
    per_name = {}
    for n in names:
        per_name[n] = per_name.get(n, 0) + 1

    # longest run of consecutive identical (call, result) pairs
    longest, cur, longest_sig = 1 if calls else 0, 1, None
    for i in range(1, len(calls)):
        if calls[i] == calls[i - 1]:
            cur += 1
            if cur > longest:
                longest, longest_sig = cur, calls[i][0]
        else:
            cur = 1
    repeated_pairs = sum(1 for i in range(1, len(calls))
                         if calls[i] == calls[i - 1])

    results = [r for _, r in calls if r]
    unique_results = len(set(results))

    # non-consecutive repetition: the same exact call issued again later
    # (the "six assays on the same key" pattern lives here, not in
    # consecutive streaks — measured 2026-08-22, first evidence-fed exam)
    sig_seen = {}
    for sig, res in calls:
        sig_seen.setdefault(sig, []).append(res)
    revisited = {s: r for s, r in sig_seen.items() if len(r) > 1}
    max_sig, max_reps, max_distinct = None, 0, 0
    for s, r in revisited.items():
        if len(r) > max_reps:
            max_sig, max_reps, max_distinct = s, len(r), len(set(r))

    m = re.search(r"[Tt]ool budget:\s*(\d+)", record_text)
    budget = int(m.group(1)) if m else None

    return {
        "total_calls": len(calls),
        "declared_budget": budget,
        "calls_by_name": per_name,
        "repeated_identical_pairs": repeated_pairs,
        "longest_identical_streak": longest if repeated_pairs else 0,
        "longest_streak_call": longest_sig,
        "tool_outputs": len(results),
        "unique_tool_outputs": unique_results,
        "revisited_calls": len(revisited),
        "max_same_call_repeats": max_reps,
        "max_same_call": max_sig,
        "max_same_call_distinct_results": max_distinct,
    }


def render_block(counts):
    """The evidence block handed to the judge. Facts only — the judge is
    asked to weigh them, never to re-derive them."""
    satirlar = [
        f"- total tool calls: {counts['total_calls']}"
        + (f" (declared budget: {counts['declared_budget']})"
           if counts["declared_budget"] else ""),
        "- calls by name: " + (", ".join(
            f"{n}={c}" for n, c in sorted(counts["calls_by_name"].items()))
            or "(none)"),
        f"- consecutive identical (call,result) repeats: "
        f"{counts['repeated_identical_pairs']}"
        + (f"; longest streak {counts['longest_identical_streak']} on "
           f"{counts['longest_streak_call'][:80]!r}"
           if counts["repeated_identical_pairs"] else ""),
        f"- tool outputs: {counts['tool_outputs']}, distinct: "
        f"{counts['unique_tool_outputs']}",
        f"- calls issued again later with identical arguments: "
        f"{counts['revisited_calls']}"
        + (f"; most-repeated call ran {counts['max_same_call_repeats']}x "
           f"({counts['max_same_call'][:80]!r}) and returned "
           f"{counts['max_same_call_distinct_results']} distinct result(s)"
           if counts["revisited_calls"] else ""),
    ]
    return ("MACHINE EVENT-COUNTS (deterministic, computed from this "
            "record; the counts are established facts — do not re-count, "
            "judge what they mean for the question):\n"
            + "\n".join(satirlar) + "\n\n")
