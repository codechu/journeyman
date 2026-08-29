#!/usr/bin/env python3
"""Build the project site from repo sources. No dependencies, no hand-entered numbers.

    notes/<slug>/{meta.json,note.html,*assets}  ->  site/notes/<slug>/index.html
    runs-archive/leaderboard-1-v24-*/           ->  the board table on site/index.html

Every figure on the landing page is read from a sealed report.json at build
time, so the site cannot drift from the records. Run it after adding a note or
a run, then commit site/.

Usage: tools/site.py [repo-root]
"""
import json
import os
import shutil
import sys

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                       os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(REPO, "site")
NOTES = os.path.join(REPO, "notes")
BOARD = "runs-archive/leaderboard-1-v24-2026-08-24"
GH = "https://github.com/codechu/journeyman"
BASE = "https://codechu.github.io/journeyman"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{summary}">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{summary}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<div class="wrap">
  <nav class="sitenav">
    <a href="{root}">journeyman</a>
    <span class="navlinks"><a href="{root}notes/">notes</a><a href="{gh}">repository</a></span>
  </nav>
"""
FOOT = """</div>
</body>
</html>
"""


def read_notes():
    out = []
    if not os.path.isdir(NOTES):
        return out
    for slug in sorted(os.listdir(NOTES)):
        meta_path = os.path.join(NOTES, slug, "meta.json")
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path))
            meta["slug"] = slug
            meta["body"] = open(os.path.join(NOTES, slug, "note.html")).read()
            out.append(meta)
    return sorted(out, key=lambda m: m["date"], reverse=True)


def board_rows():
    """The cohort table, read from the sealed reports — never typed by hand."""
    root = os.path.join(REPO, BOARD)
    judged = ["wall-pricing", "empty-measure", "object-hold", "grounding",
              "relief-page", "handoff-verification"]
    rows = []
    for agent in sorted(os.listdir(root)):
        f = os.path.join(root, agent, "report.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        ax = {k: v["score"] for k, v in r["axes"].items()}
        vals = [ax[a] for a in judged if ax.get(a) is not None]
        rows.append({"agent": agent,
                     "mean": round(sum(vals) / len(vals), 2) if vals else None,
                     "axes": ax,
                     "invalid": r.get("invalid_cells", 0)})
    return sorted(rows, key=lambda r: (r["mean"] is None, -(r["mean"] or 0)))


def landing(notes, rows):
    cols = [("cover", "walk-coverage"), ("move", "move-discipline"),
            ("verdict", "self-verdict"), ("ground", "grounding"),
            ("handoff", "handoff-verification"), ("empty", "empty-measure")]
    cell = lambda v: "—" if v is None else f"{v:.2f}"
    trs = "".join(
        f'<tr><td>{r["agent"]}</td><td><b>{cell(r["mean"])}</b></td>'
        + "".join(f'<td>{cell(r["axes"].get(k))}</td>' for _, k in cols)
        + f'<td>{r["invalid"] or ""}</td></tr>'
        for r in rows)
    ths = "".join(f"<th>{label}</th>" for label, _ in cols)
    zero_empty = sum(1 for r in rows if r["axes"].get("empty-measure") == 0.0)
    best_relief = max((r["axes"].get("relief-page") or 0) for r in rows)
    featured, rest = (notes[0], notes[1:]) if notes else (None, [])
    if featured:
        art = next((a for a in featured.get("assets", [])
                    if a.endswith((".png", ".svg"))), None)
        thumb = (f'<img src="notes/{featured["slug"]}/{art}" alt="" loading="lazy">'
                 if art else "")
        feature_html = f"""  <section>
    <a class="featured" href="notes/{featured['slug']}/">
      <div class="ftext">
        <span class="eyebrow">latest note · {featured['date']}</span>
        <h2>{featured['title']}</h2>
        <p>{featured['summary']}</p>
        <span class="more">read the note →</span>
      </div>
      <div class="fig">{thumb}</div>
    </a>
  </section>

"""
    else:
        feature_html = ""
    notes_html = "".join(
        f'<li><a href="notes/{n["slug"]}/">{n["title"]}</a>'
        f'<time>{n["date"]}</time><p>{n["summary"]}</p></li>' for n in rest)
    notes_section = f"""  <section>
    <h2>Earlier notes</h2>
    <ul class="notelist">{notes_html}</ul>
  </section>

""" if rest else ""
    return f"""  <header class="masthead">
    <div class="eyebrow">a benchmark for how an agent works</div>
    <h1>journeyman</h1>
    <p class="standfirst">Most benchmarks score the answer. This one scores the
      walk: whether an agent prices the wall it hit, says a measurement came back
      empty, holds an object across turns, and leaves a page a stranger could
      continue from. Every run is sealed — the agent's system text, the scene
      hashes, the seeds, the judge — so a number can be traced back to what
      produced it.</p>
    <div class="credit">
      <span><b>{len(rows)}</b> agents on the board</span>
      <span><b>8</b> scenes × <b>3</b> seeds</span>
      <span><b>{zero_empty}</b> of {len(rows)} never report an empty measurement</span>
      <span>best relief-page <b>{best_relief:.2f}</b></span>
    </div>
  </header>

{feature_html}  <section>
    <h2>Run your own model</h2>
    <pre><code>pip install journeyman-bench
journeyman run --endpoint https://your-api/v1 --model your-model \\
  --judge https://openrouter.ai/api --judge-model a-different-model</code></pre>
    <p class="lede">The judge must be a different model than the agent; a run that
      grades itself is stamped <code>self_judged</code>. Scoring locally with an
      open-weight judge costs nothing but GPU time.</p>
  </section>

  <section>
    <h2>The board</h2>
    <p class="lede">Cohort 1, judged by the self-hosted Qwen3.6 under the v2.4
      questions. The mean orders the rows; it is not a composite score — read each
      row as a profile. Full table, caveats and the two superseded editions are in
      <a href="{GH}/blob/main/docs/leaderboard.md">docs/leaderboard.md</a>.</p>
    <div class="tablewrap">
      <table><thead><tr><th>agent</th><th>judged mean</th>{ths}<th>invalid</th></tr></thead>
      <tbody>{trs}</tbody></table>
    </div>
  </section>

{notes_section}  <footer>
    <div class="links"><a href="{GH}">repository</a><a href="{GH}/blob/main/docs/methodology.md">methodology</a><a href="{GH}/tree/main/runs-archive">sealed runs</a><a href="https://pypi.org/project/journeyman-bench/">pypi</a></div>
    <p>Every number on this page is read from a <code>report.json</code> under
      <code>runs-archive/</code> at build time.</p>
  </footer>
"""


def note_index(notes):
    items = "".join(
        f'<li><a href="{n["slug"]}/">{n["title"]}</a><time>{n["date"]}</time>'
        f'<p>{n["summary"]}</p></li>' for n in notes)
    return f"""  <header class="masthead">
    <div class="eyebrow">notes</div>
    <h1>What we learned while measuring</h1>
    <p class="standfirst">Each note answers one question, carries its figure, and
      links the sealed records it was computed from.</p>
  </header>
  <section><ul class="notelist">{items}</ul></section>
"""


def write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(html)
    print(f"  {os.path.relpath(path, REPO)}  {os.path.getsize(path)} bytes")


def main():
    notes = read_notes()
    rows = board_rows()
    write(os.path.join(SITE, "index.html"),
          HEAD.format(title="journeyman", ogtype="website", root="", gh=GH,
                      url=BASE + "/", image=f"{BASE}/notes/{notes[0]['slug']}/ablation.png"
                      if notes else "",
                      summary="A benchmark that scores how an agent works, not "
                              "just what it answers.")
          + landing(notes, rows) + FOOT)
    write(os.path.join(SITE, "notes", "index.html"),
          HEAD.format(title="journeyman — notes", ogtype="website", root="../",
                      gh=GH, url=f"{BASE}/notes/", image="",
                      summary="Notes from measuring agents.")
          + note_index(notes) + FOOT)
    for n in notes:
        out = os.path.join(SITE, "notes", n["slug"])
        write(os.path.join(out, "index.html"),
              HEAD.format(title=n["title"], ogtype="article", root="../../",
                          gh=GH, url=f"{BASE}/notes/{n['slug']}/",
                          image=f"{BASE}/notes/{n['slug']}/ablation.png",
                          summary=n["summary"])
              + n["body"] + FOOT)
        for asset in n.get("assets", []):
            shutil.copy(os.path.join(NOTES, n["slug"], asset),
                        os.path.join(out, asset))
    print(f"built {len(notes)} note(s), {len(rows)} board rows")


if __name__ == "__main__":
    main()
