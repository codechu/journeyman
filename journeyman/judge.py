"""Judge layer — pluggable; default is the endpoint itself (dev mode).

Self-judged scores are marked NOT COMPARABLE, always. Comparable numbers
come only from a pinned, qualified reference judge. Anyone may bring a
judge; it earns the badge through the qualification exam (labelled
calibration set, published per-item accuracy).

Skeleton wiring: one judge call per rubric item per cell (small focused
calls — a single giant call dilutes attention; measured in the house:
0/2 blindness on fresh drops). Verdict must echo one of the declared
labels verbatim, else the item is marked unparsed (never silently kept).

TODO(muscle): reference-judge pinning · qualification exam command ·
calibration registry format · self-awareness-gap derived metric.
"""
import json
import re
import urllib.request


JUDGE_PREAMBLE = (
    "You are judging one aspect of an agent's work from its raw record. "
    "Judge ONLY from the record. Quote a short verbatim fragment as "
    "evidence. End with exactly one line:  VERDICT: <label>\n"
    "Allowed labels: {labels}\n\nQUESTION: {question}\n\nRECORD:\n{record}\n")


def _record_text(record, limit=6000):
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
            record=_record_text(record))
        msg, _ = judge_endpoint.chat(
            [{"role": "user", "content": prompt}], tools=[])
        text = msg.get("content") or ""
        m = re.search(r"VERDICT:\s*([a-zA-Z_-]+)", text)
        label = m.group(1).lower() if m else None
        if label not in item.verdicts:
            label = "__unparsed__"
        verdicts[item.axis] = {"verdict": label, "positive": item.positive,
                               "raw": text[-800:]}
        log(f"[judge] {record['cell_id']} · {item.axis} → {label}")
    return verdicts
