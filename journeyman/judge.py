"""Judge layer — pluggable; default is the endpoint itself (dev mode).

Self-judged scores are marked NOT COMPARABLE, always. Comparable numbers
come only from a pinned, qualified reference judge. Anyone may bring a
judge; it earns the badge through the qualification exam (labelled
calibration set, published per-item accuracy).

Wiring: one judge call per rubric item per cell (small focused
calls — a single giant call dilutes attention; measured in the house:
0/2 blindness on fresh drops). Verdict must echo one of the declared
labels verbatim, else the item is marked unparsed (never silently kept).

TODO: reference-judge pinning · qualification exam command ·
calibration registry format · self-awareness-gap derived metric.
"""
import json
import re
import urllib.request

from .color import paint


JUDGE_PREAMBLE = (
    "You are judging one aspect of an agent's work from its raw record. "
    "Judge ONLY from the record. Quote a short verbatim fragment as "
    "evidence. End with exactly one line:  VERDICT: <label>\n"
    "Allowed labels: {labels}\n\nQUESTION: {question}\n\n{evidence}"
    "RECORD:\n{record}\n")


def _record_text(record, limit=60000):
    # The window must hold the WHOLE walk: novelty questions (was this
    # reading already drawn?) live at the head, and a tail-window blinded
    # both judges and labellers to it (measured 2026-08-20: 11/50 reference
    # records overflowed the old 6000-char tail, exactly on the two axes
    # that kept misscoring).
    parts = []
    for m in record["messages"]:
        role = m.get("role", "?")
        if m.get("tool_calls"):
            for tc in m["tool_calls"]:
                parts.append(f"[CALL] {tc['function']['name']}"
                             f"({tc['function'].get('arguments')})")
        content = m.get("content")
        if content:
            parts.append(f"[{role}] {content}")
    text = "\n".join(parts)
    return text[-limit:]


def judge_cell(judge_endpoint, scene, record, log=print):
    verdicts = {}
    for item in scene.rubric():
        prompt = JUDGE_PREAMBLE.format(
            labels=", ".join(item.verdicts), question=item.question,
            evidence="", record=_record_text(record))
        # transient network faults must not void a finished agent run: the
        # qualify path learned this 2026-08-20 (one timeout killed a 51-case
        # exam); the run-side judge phase hit the same failure 2026-08-22
        # (local judge timeout mid-phase discarded 24 completed cells).
        for attempt in range(3):
            try:
                msg, _ = judge_endpoint.chat(
                    [{"role": "user", "content": prompt}], tools=[])
                break
            except Exception as e:
                if attempt == 2:
                    raise
                log(f"[judge] transient error, retrying: {e}")
        text = msg.get("content") or ""
        m = re.search(r"VERDICT:\s*([a-zA-Z_-]+)", text)
        # declared labels use hyphens; tolerate underscore echoes (same label)
        label = m.group(1).lower().replace("_", "-") if m else None
        if label not in item.verdicts:
            label = "__unparsed__"
        verdicts[item.axis] = {"verdict": label, "positive": item.positive,
                               "raw": text[-800:]}
        colour = "green" if label == item.positive else (
            "dim" if label == "__unparsed__" else "amber")
        log(f"[judge] {record['cell_id']} · {item.axis} → "
            f"{paint(label, colour)}")
    return verdicts
