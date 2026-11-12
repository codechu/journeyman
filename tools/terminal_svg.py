#!/usr/bin/env python3
"""Render assets/terminal.svg from a REAL `journeyman run` console log.

The README image used to be drawn by hand and fell behind the code (it
showed v0.0.5, seven scenes and status words the CLI no longer prints).
This tool draws it from a log instead, so refreshing it is one command:

    python3 tools/terminal_svg.py <run.log> [--out assets/terminal.svg] [--cmd "<command line shown>"]

What is kept, in order and verbatim: the banner version, the judge line,
the first three cell lines and the ETA line after them, the first
"still working" line (if any), the first two judge verdicts, the first
three profile axes, and the report path (rewritten to the default runs/
layout, so no local directory reaches a public image). The scene list is
shortened to its count. Everything else is dropped, and the title bar says "abridged".
"""
import argparse
import html
import re
import sys

GREEN, RED, AMBER, DIM, TEXT = "#7bbf6a", "#e06c60", "#e8a33d", "#8892a8", "#c8d0e0"


def pick(lines):
    out = {"version": None, "scenes": None, "judge": None, "cells": [], "eta": None, "still": None, "verdicts": [], "profile": [], "report": None}
    in_profile = False
    for raw in lines:
        s = raw.rstrip("\n")
        m = re.search(r"JOURNEYMAN\s+(v[\d.]+)", s)
        if m and not out["version"]:
            out["version"] = m.group(1)
        if s.startswith("scenes ") and not out["scenes"]:
            n = len(re.findall(r"'[^']+'", s.split("·")[0])); seeds = s.split("·", 1)[1].strip() if "·" in s else ""
            out["scenes"] = f"scenes [{n} · standard set] · {seeds}"
        if s.startswith("judge:") and not out["judge"]:
            out["judge"] = s
        if re.match(r"\[\s*\d+/\d+\]", s) and len(out["cells"]) < 3:
            out["cells"].append(s)
        if s.strip().startswith("cells ") and len(out["cells"]) == 3 and not out["eta"]:
            out["eta"] = s.strip()
        if s.strip().startswith("still ") and not out["still"]:
            out["still"] = s.strip()
        if s.startswith("[judge]") and len(out["verdicts"]) < 2:
            out["verdicts"].append(s)
        if s.startswith("PROFILE"):
            in_profile = True; out["profile_head"] = s; continue
        if in_profile:
            if s.startswith("  ") and len(out["profile"]) < 3 and s.strip():
                out["profile"].append(s)
            elif not s.strip() or not s.startswith("  "):
                in_profile = False
        if s.startswith("report:"):   # local absolute path → the default runs/ layout (no user directory in a public image)
            m = re.search(r"(\d{4}-\d{2}-\d{2}_\d{6}|\d{4}-\d{2}-\d{2}_\d{4})/report\.md", s)
            out["report"] = f"report: runs/{m.group(1)}/report.md" if m else s
    missing = [k for k in ("version", "scenes", "cells", "verdicts", "profile", "report") if not out[k]]
    if missing:
        raise SystemExit(f"log lacks {missing} — not a finished run log")
    return out


def t(x, y, s, fill=TEXT, **kw):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'  <text x="{x}" y="{y}" fill="{fill}"{extra}>{html.escape(s)}</text>'


def status_split(line):
    """'… · ✓ closed' → (head, '✓ closed', colour)."""
    for mark, col in (("✓", GREEN), ("✗", RED)):
        if mark in line:
            i = line.index(mark); return line[:i].rstrip(), line[i:].strip(), col
    return line, "", TEXT


def score_colour(v):
    try:
        f = float(v)
    except ValueError:
        return DIM
    return GREEN if f >= 0.9 else (AMBER if f >= 0.4 else RED)


def render(p, cmd):
    W, y, rows = 760, 60, []
    rows.append(t(20, y, "$ " + cmd, DIM)); y += 14
    rows.append(f'  <rect x="20" y="{y}" width="486" height="52" rx="6" fill="none" stroke="{AMBER}" stroke-width="1.5"/>')
    rows.append(t(38, y + 23, f"JOURNEYMAN {p['version']}", AMBER, font_weight="bold"))
    rows.append(t(250, y + 23, "process-quality bench", "#c98f36", font_size="12"))
    rows.append(t(38, y + 42, "measures how agents work — and how they fail", "#b7c0d4", font_size="12")); y += 78
    rows.append(t(20, y, p["scenes"])); y += 18
    if p["judge"]:
        rows.append(t(20, y, p["judge"][:96], AMBER, font_size="12")); y += 22
    for c in p["cells"]:   # status at a fixed column, as a terminal would align it
        head, st, col = status_split(c); rows.append(t(20, y, head)); rows.append(t(470, y, st, col)); y += 18
    if p["eta"]:
        rows.append(t(20, y, "        " + p["eta"], DIM)); y += 18
    if p["still"]:
        rows.append(t(20, y, "    " + p["still"], DIM)); y += 18
    y += 10; rows.append(t(20, y, "--- judging phase ---", DIM)); y += 18
    for v in p["verdicts"]:
        head, _, verdict = v.rpartition("→")
        rows.append(t(20, y, head.rstrip() + " →")); rows.append(t(470, y, verdict.strip(), AMBER)); y += 18
    y += 14; rows.append(t(20, y, p.get("profile_head", "PROFILE"), DIM)); y += 20
    for a in p["profile"]:   # the line verbatim (spacing preserved); only the score is coloured
        m = re.match(r"(\s*\S+\s+)(\S+)(.*)", a)
        pre, score, rest = m.groups()
        rows.append(f'  <text x="20" y="{y}" fill="{TEXT}">{html.escape(pre)}<tspan fill="{score_colour(score)}">{html.escape(score)}</tspan><tspan fill="{DIM}">{html.escape(rest)}</tspan></text>'); y += 18
    y += 4; rows.append(t(20, y, p["report"], DIM)); H = y + 16
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace, Menlo, Consolas, monospace" font-size="13" xml:space="preserve">',
            f'  <rect width="{W}" height="{H}" rx="10" fill="#1b2130"/>', f'  <rect width="{W}" height="34" rx="10" fill="#242c3f"/>',
            f'  <rect y="24" width="{W}" height="10" fill="#242c3f"/>',
            '  <circle cx="22" cy="17" r="6" fill="#e06c60"/><circle cx="44" cy="17" r="6" fill="#e0b050"/><circle cx="66" cy="17" r="6" fill="#7bbf6a"/>',
            t(380, 21, "journeyman run — real log, abridged", DIM, font_size="12", text_anchor="middle")]
    return "\n".join(head + rows + ["</svg>", ""])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("log"); ap.add_argument("--out", default="assets/terminal.svg")
    ap.add_argument("--cmd", default="journeyman run --endpoint http://localhost:8080 --model my-agent")
    a = ap.parse_args()
    with open(a.log, encoding="utf-8") as fh:
        svg = render(pick(fh.readlines()), a.cmd)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {a.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    sys.exit(main())
