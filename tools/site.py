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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board  # noqa: E402

def _repo():
    """argv only counts when this file is the program — under a test runner
    sys.argv[1] belongs to the runner, not to us."""
    if __name__ == "__main__" and len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


REPO = _repo()
SITE = os.path.join(REPO, "site")
NOTES = os.path.join(REPO, "notes")
SRC = os.path.join(REPO, "site-src")   # everything under site/ is generated
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
{ogimage}<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{root}style.css">
<link rel="alternate" type="application/atom+xml" title="journeyman notes" href="{root}feed.xml">
</head>
<body>
<div class="wrap">
  <nav class="sitenav">
    <a href="{root}./"{current}>journeyman</a>
    <span class="navlinks"><a href="{root}notes/">notes</a><a href="{gh}">repository</a></span>
  </nav>
"""
FOOT = """</div>
</body>
</html>
"""


def version():
    """The shipping version, from pyproject — not a literal in this file."""
    for line in open(os.path.join(REPO, "pyproject.toml")):
        if line.startswith("version"):
            return line.split("=")[1].strip().strip('"')
    return "?"


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
    """One reader for both surfaces — see tools/board.py."""
    return board.rows(os.path.join(REPO, BOARD))


def landing(notes, rows):
    mean_axes = [("wall", "wall-pricing"), ("empty", "empty-measure"),
                 ("object", "object-hold"), ("ground", "grounding"),
                 ("relief", "relief-page"), ("handoff", "handoff-verification")]
    mech_axes = [("coverage", "walk-coverage"), ("move", "move-discipline"),
                 ("verdict", "self-verdict"), ("route", "route-discipline")]

    def cell(a, judged=True):
        """A judged axis over three seeds takes four values — 0.00, 0.33, 0.67,
        1.00 — because it is a count of 3 wearing a decimal. Print the count.
        Mechanical axes are ratios over a whole walk and stay decimals."""
        if not a:
            return "—"
        if a.get("score") is None:
            return "n/a" if a.get("not_applicable") else "—"
        n = a.get("n") or 0
        if judged and n:
            per_seed = a.get("per_seed") or {}
            k = (sum(1 for v in per_seed.values() if v == 1.0) if per_seed
                 else round(a["score"] * n))
            dots = "".join("●" if i < k else "○" for i in range(n))
            return f'<span class="dots">{dots}</span><span class="kn">{k}/{n}</span>'
        return f'{a["score"]:.2f}<span class="n">n={n}</span>' if n else f'{a["score"]:.2f}'

    def table(cols, rows_, mean=False):
        ths = "".join(f"<th>{label}</th>" for label, _ in cols)
        head = ("<th>agent</th>" + ths + "<th>mean</th><th>flags</th>"
                if mean else "<th>agent</th>" + ths)
        trs = ""
        for r in rows_:
            tds = "".join(f'<td>{cell(r["axes"].get(k), mean)}</td>' for _, k in cols)
            tail = ""
            if mean:
                m = "—" if r["mean"] is None else f'{r["mean"]:.2f}<span class="n">({r["mean_n"]})</span>'
                flags = []
                if r["partial"]:
                    flags.append("partial run")
                if r["invalid"]:
                    flags.append(f'{r["invalid"]} invalid')
                if r["bench"] != "0.0.7":
                    flags.append(f'bench {r["bench"]}')
                if r["agent"].startswith("qwen3.6"):
                    flags.append("judge affinity")
                if r["agent"].startswith("kimi"):
                    flags.append("council")
                tail = f'<td>{m}</td><td class="flag">{" · ".join(flags)}</td>' 
            trs += f'<tr><td>{r["agent"]}</td>{tds}{tail}</tr>'
        foot = ""
        if mean:
            cells = []
            for _, k in cols:
                graded = [r for r in rows_
                          if (r["axes"].get(k) or {}).get("score") is not None]
                floor = sum(1 for r in graded if r["axes"][k]["score"] == 0.0)
                cells.append(f'<td>{floor}/{len(graded)}</td>')
            foot = ('<tfoot><tr><td>at zero</td>' + "".join(cells)
                    + '<td></td><td></td></tr></tfoot>')
        cls = 'board' if mean else 'mech'
        return (f'<div class="tablewrap"><table class="{cls}"><thead><tr>{head}</tr></thead>'
                f'<tbody>{trs}</tbody>{foot}</table></div>')

    scenes = rows[0]["scenes"] if rows else 0
    seeds = rows[0]["seeds"] if rows else 0
    benches = sorted({r["bench"] for r in rows})
    graded_empty = [r for r in rows
                    if (r["axes"].get("empty-measure") or {}).get("score") is not None]
    zero_empty = sum(1 for r in graded_empty if r["axes"]["empty-measure"]["score"] == 0.0)
    best_relief = max((r["axes"].get("relief-page") or {}).get("score") or 0 for r in rows)
    tok = sum((r["cost"].get("tokens_in", 0) + r["cost"].get("tokens_out", 0))
              for r in rows) / max(len(rows), 1)

    featured, rest = (notes[0], notes[1:]) if notes else (None, [])
    feature_html = f"""  <section>
    <a class="featured" href="notes/{featured['slug']}/">
      <span class="eyebrow">latest note · {featured['date']}</span>
      <h2>{featured['title']}</h2>
      <p>{featured['summary']}</p>
      <span class="more">read the note →</span>
    </a>
  </section>

""" if featured else ""
    notes_html = "".join(
        f'<li><a href="notes/{n["slug"]}/">{n["title"]}</a>'
        f'<time datetime="{n["date"]}">{n["date"]}</time><p>{n["summary"]}</p></li>'
        for n in rest)
    notes_section = f"""  <section>
    <h2>Earlier notes</h2>
    <ul class="notelist">{notes_html}</ul>
  </section>

""" if rest else ""

    return f"""  <header class="masthead">
    <div class="eyebrow">a benchmark for how an agent works</div>
    <h1>journeyman</h1>
    <p class="standfirst">Most agent benchmarks score the answer. This one scores
      the walk: whether an agent prices the wall it hit, says a measurement came
      back empty, holds an object across turns, and leaves a page a stranger could
      continue from. Every run is sealed — the scene hashes, the seeds, the model
      and the judge — so a number can be traced back to what produced it. (These
      eleven ran without a system text of their own; the seal carries its md5 when
      one is used.)</p>
    <div class="credit">
      <span><b>{zero_empty}</b> of {len(graded_empty)} graded agents never report an empty measurement</span>
      <span>best relief-page <b>{best_relief:.2f}</b></span>
      <span>{scenes} scenes × {seeds} seeds</span>
    </div>
  </header>

{feature_html}  <section>
    <h2>The board</h2>
    <p class="lede">Cohort 1, judged by the self-hosted Qwen3.6 under the v2.4
      questions, sorted by name. The mean is an unweighted average of the six judged
      axes, with the count it covers — not a composite score, and not a ranking.
      Read a row as a profile. On a narrow screen the axis columns are dropped
      rather than hidden behind a scroll; open the page wider to see them. Full table and caveats:
      <a href="{GH}/blob/main/docs/leaderboard.md">docs/leaderboard.md</a>.</p>
    {table(mean_axes, rows, mean=True)}
    <p class="tnote">●○ = seeds where the axis was met, out of the cells it was
      graded on · — = no valid cell · the foot row counts agents at zero over the
      agents that axis was graded on · "partial run" = fewer cells than the cohort's
      best for that axis; the record does not carry an attempted-cell count</p>
  </section>

  <section>
    <h2>Mechanical axes</h2>
    <p class="lede">Counted from the replayed walk rather than judged, and
      deliberately not in the mean above. Here <code>n/a</code> means the stimulus
      never occurred in any cell, and <code>n=</code> is the cells behind the ratio.</p>
    {table(mech_axes, rows)}
  </section>

  <section>
    <h2>Run your own model</h2>
    <pre><code>pip install journeyman-bench
journeyman run \\
  --endpoint https://your-api/v1 \\
  --model your-model \\
  --judge https://openrouter.ai/api \\
  --judge-model other-model</code></pre>
    <p class="lede">The judge must be a different model than the agent; a run that
      grades itself is stamped <code>self_judged</code>. A full 24-cell run cost
      these agents {tok/1000:.0f}K tokens on average — cents for most, and one
      reasoning model was stopped at 48¢ for 17 cells. A self-hosted judge adds
      about two hours of local GPU and no money.</p>
    <p class="tnote">Reproducibility: this board was produced by journeyman
      {" and ".join(benches)}; PyPI ships {version()}, and reports written by 0.0.x
      no longer validate — run <code>journeyman upgrade</code> over them, or read
      this board as an archive. See
      <a href="{GH}/blob/main/docs/versioning.md">versioning.md</a>.</p>
  </section>

{notes_section}  <footer>
    <div class="links"><a href="{GH}">repository</a><a href="{GH}/blob/main/docs/methodology.md">methodology</a><a href="{GH}/blob/main/docs/glossary.md">glossary</a><a href="{GH}/blob/main/docs/run-guide.md">run guide</a><a href="{GH}/tree/main/runs-archive">sealed runs</a><a href="https://pypi.org/project/journeyman-bench/">pypi</a><a href="feed.xml">feed</a></div>
    <p>Every score, count and flag in these tables is read from a
      <code>report.json</code> under <code>runs-archive/</code> at build time.</p>
  </footer>
"""


def note_index(notes):
    items = "".join(
        f'<li><a href="{n["slug"]}/">{n["title"]}</a>'
        f'<time datetime="{n["date"]}">{n["date"]}</time>'
        f'<p>{n["summary"]}</p></li>' for n in notes)
    return f"""  <header class="masthead">
    <div class="eyebrow">notes</div>
    <h1>What we learned while measuring</h1>
    <p class="standfirst">Each note answers one question, carries its figure, and
      links the sealed records it was computed from.</p>
  </header>
  <section><ul class="notelist">{items}</ul></section>
"""


def head(title, summary, root, url, image="", current=False):
    return HEAD.format(title=title, summary=summary, root=root, url=url, gh=GH,
                       ogtype="article" if root else "website",
                       ogimage=(f'<meta property="og:image" content="{image}">\n'
                                if image else ""),
                       current=' aria-current="page"' if current else "")


def feed(notes):
    esc = lambda t: (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    entries = "".join(f"""
  <entry>
    <title>{esc(n['title'])}</title>
    <link href="{BASE}/notes/{n['slug']}/"/>
    <id>{BASE}/notes/{n['slug']}/</id>
    <updated>{n['date']}T00:00:00Z</updated>
    <summary>{esc(n['summary'])}</summary>
  </entry>""" for n in notes)
    updated = (notes[0]["date"] if notes else "1970-01-01") + "T00:00:00Z"
    author = ((notes[0].get("authors") or ["journeyman"])[0] if notes
              else "journeyman")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>journeyman — notes</title>
  <author><name>{author}</name></author>
  <link href="{BASE}/"/>
  <link rel="self" href="{BASE}/feed.xml"/>
  <id>{BASE}/</id>
  <updated>{updated}</updated>{entries}
</feed>
"""


def inject_data(body, csv_path):
    """Replace the note's DATA array with rows read from its CSV at build time.

    The array used to be typed into the page eight lines above the words
    "regenerated from the sealed reports, not hand-entered". Now it is.
    """
    import csv as _csv
    with open(csv_path) as f:
        table = [r for r in _csv.reader(f)
                 if r and not r[0].startswith("#") and r[0] != "axis"]
    notes_col = {
        "wall-pricing": "pricing a wall hit",
        "grounding": "tied to what was seen",
        "object-hold": "an object held",
        "empty-measure": "an empty result said",
        "relief-page": "a page to continue",
        "handoff-verification": "the note checked",
        "route-discipline": "one graded cell",
    }
    data = [{"ax": r[0], "note": notes_col.get(r[0], ""), "judge": float(r[1]),
             "jn": r[2], "rubric": float(r[3]), "rn": r[4]} for r in table]
    fmt = lambda v: ("+" if v > 0 else "\u2212" if v < 0 else "") + f"{abs(v):.3f}"
    static = ('<table><thead><tr><th>axis</th><th>judge swapped</th>'
              '<th>questions changed</th></tr></thead><tbody>'
              + "".join(f'<tr><td>{d["ax"]}</td><td>{fmt(d["judge"])}'
                        f'<span class="n">{d["jn"]}</span></td>'
                        f'<td>{fmt(d["rubric"])}<span class="n">{d["rn"]}</span></td></tr>'
                        for d in data)
              + "</tbody></table>")
    body = body.replace("{{STATIC_TABLE}}", static)
    start = body.index("  const DATA = [")
    end = body.index("];", start) + 2
    return (body[:start] + "  const DATA = "
            + json.dumps(data, indent=2).replace("\n", "\n  ") + ";" + body[end:])


def write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(html)
    print(f"  {os.path.relpath(path, REPO)}  {os.path.getsize(path)} bytes")


def main(site_dir=None):
    global SITE
    SITE = site_dir or SITE
    notes = read_notes()
    rows = board_rows()
    fig = (notes[0].get("figure") or "") if notes else ""
    write(os.path.join(SITE, "index.html"),
          head("journeyman",
               "A benchmark that scores how an agent works, not just what it answers.",
               "", BASE + "/",
               f"{BASE}/notes/{notes[0]['slug']}/{fig}" if fig else "", current=True)
          + landing(notes, rows) + FOOT)
    write(os.path.join(SITE, "notes", "index.html"),
          head("Notes — journeyman", "Notes from measuring agents.", "../",
               f"{BASE}/notes/")
          + note_index(notes) + FOOT)
    for n in notes:
        out = os.path.join(SITE, "notes", n["slug"])
        nfig = n.get("figure") or ""
        if n.get("data"):
            n["body"] = inject_data(n["body"],
                                    os.path.join(NOTES, n["slug"], n["data"]))
        write(os.path.join(out, "index.html"),
              head(f'{n["title"]} — journeyman', n["summary"], "../../",
                   f"{BASE}/notes/{n['slug']}/",
                   f"{BASE}/notes/{n['slug']}/{nfig}" if nfig else "")
              + n["body"] + FOOT)
        for asset in n.get("assets", []):
            shutil.copy(os.path.join(NOTES, n["slug"], asset),
                        os.path.join(out, asset))
    for name in sorted(os.listdir(SRC)):
        os.makedirs(SITE, exist_ok=True)
        shutil.copy(os.path.join(SRC, name), os.path.join(SITE, name))
        print(f"  site/{name}  {os.path.getsize(os.path.join(SITE, name))} bytes")
    write(os.path.join(SITE, "feed.xml"), feed(notes))
    print(f"built {len(notes)} note(s), {len(rows)} board rows")


if __name__ == "__main__":
    main()
