"""CLI: journeyman run --endpoint <url> --model <name> [--judge <url>]

Commands:
  run       drive the grid, judge, report
  selftest  run the whole pipeline offline against a scripted fake
            endpoint — proves the bones without any model
  upgrade   backfill `kind` into a pre-0.1.0 report.json

"""
import argparse
import os
import sys

from .driver import Endpoint, StoppedOnInvalid, run_grid
from .judge import judge_cell
from .record import RunDir
from .report import render
from . import scene as scene_mod


def _env_key(*names):
    """A key from the environment, so it need not be typed on a command line.

    An `--api-key` argument is readable by every user on the machine through
    `ps`, and it stays in shell history afterwards. Accepting the variable
    costs one line and removes the most common way a key escapes.
    """
    for n in names:
        v = os.environ.get(n)
        if v:
            return v.strip()
    return None


def resolve_model(endpoint, api_key):
    """Resolve --model when omitted: use the only model, else show the
    list (and pick interactively if we're on a TTY). Returns a model id,
    or None if it cannot be resolved (caller exits)."""
    from .driver import list_models
    try:
        models = list_models(endpoint, api_key)
    except Exception as e:
        print(f"could not list models from {endpoint} ({e}); "
              f"pass --model explicitly", file=sys.stderr)
        return None
    if not models:
        print(f"{endpoint} exposes no models via /v1/models; "
              f"pass --model explicitly", file=sys.stderr)
        return None
    if len(models) == 1:
        print(f"using the endpoint's only model: {models[0]}")
        return models[0]
    print(f"the endpoint offers {len(models)} models:")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m}")
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            pick = input("pick one (number or name, blank to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):
            pick = ""
        if not pick:
            return None
        if pick.isdigit() and 1 <= int(pick) <= len(models):
            return models[int(pick) - 1]
        if pick in models:
            return pick
        print(f"'{pick}' is not one of the listed models", file=sys.stderr)
        return None
    print("pass --model with one of the above", file=sys.stderr)
    return None


def _warn_if_nothing_measured(run_dir):
    """Say on stderr, in red, that the report just printed measured nothing
    (see report.nothing_measured). The exit code is unchanged."""
    from .report import nothing_measured
    empty = nothing_measured(run_dir.read_cells())
    if empty is None:
        return
    from .color import paint as _paint
    print(_paint(f"NOTHING MEASURED — all {empty[0]} cells invalid; "
                 "see the report for the first reason", "red"), file=sys.stderr)


def _run_arm(run_args, runs_dir, system_file):
    """One `run` as its own process; returns the run dir it wrote."""
    import subprocess
    os.makedirs(runs_dir, exist_ok=True)
    before = set(os.listdir(runs_dir))
    cmd = [sys.executable, "-m", "journeyman", "run", *run_args, "--runs-dir", runs_dir]
    if system_file:
        cmd += ["--system-file", system_file]
    subprocess.run(cmd)   # a failing arm still leaves its cells; compare reads what exists
    new = sorted(set(os.listdir(runs_dir)) - before)
    if not new:
        sys.exit(f"uplift: the run wrote nothing under {runs_dir}")
    return os.path.join(runs_dir, new[-1])


def uncapped_warning(params, timeout):
    """A note when the agent runs with no output cap, else None.

    Uncapped, a runaway generation ends only at the transport timeout, and a
    timeout is retried as a transport fault. On a deterministic local server
    each retry reproduces the same runaway (2026-11-14: one cell 14+ minutes,
    35k tokens). The run is not stopped; the operator is told."""
    caps = [(params or {}).get(k) for k in
            ("max_tokens", "max_completion_tokens")]
    if any(isinstance(c, int) and c > 0 for c in caps):
        return None
    return (f"params: no max_tokens — uncapped. A runaway answer runs to the "
            f"{timeout}s timeout and is re-sent up to 3 times; on a "
            f"deterministic local server every attempt repeats it. Set "
            f"max_tokens in --params-file to bound a cell.")


def main(argv=None):
    # never crash on console encoding (legacy Windows consoles cannot
    # print ✓/✗/box-drawing): degrade characters, keep running
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    from . import __version__
    ap = argparse.ArgumentParser(prog="journeyman")
    ap.add_argument("--version", action="version",
                    version=f"journeyman {__version__}")
    # Not required: bare `journeyman` is a reader asking what this is, not
    # a mistake. It gets the mark and the full help on stdout and exits 0.
    # A wrong command or a missing flag is still an error on stderr.
    sub = ap.add_subparsers(dest="cmd", required=False)

    # Shared by the two commands that take minutes and print chrome while
    # they work. --quiet drops the chrome only: results, warnings and errors
    # are never suppressed, because a quiet flag that can hide a failure is
    # a footgun rather than an option.
    chrome = argparse.ArgumentParser(add_help=False)
    chrome.add_argument("-q", "--quiet", action="store_true",
                        help="no banner, and on `run` no per-cell progress "
                             "either; results, warnings and errors always "
                             "print")

    r = sub.add_parser("run", parents=[chrome],
                       help="run the benchmark against an endpoint")
    r.add_argument("--endpoint", required=True,
                   help="OpenAI-compatible base URL of the agent "
                        "under test; a bare host, a /v1, or a full "
                        "/v1/chat/completions all work")
    r.add_argument("--model", default=None,
                   help="model id; if omitted, the endpoint is asked for its "
                        "models — the only one is used, or you pick from a list")
    r.add_argument("--api-key", default=_env_key("JOURNEYMAN_API_KEY"),
                   help="agent endpoint key; defaults to $JOURNEYMAN_API_KEY. "
                        "Prefer the variable: an argument is visible in `ps` "
                        "to every user on the machine and lands in shell history")
    r.add_argument("--judge", default=None,
                   help="judge endpoint URL (default: the endpoint itself — "
                        "dev mode, scores marked NOT COMPARABLE)")
    r.add_argument("--judge-model", default=None,
                   help="model id on the judge endpoint "
                        "(default: the same id as --model)")
    r.add_argument("--judge-api-key", default=_env_key("JOURNEYMAN_JUDGE_API_KEY"),
                   help="api key for the judge endpoint (it may be a "
                        "different provider than the agent)")
    r.add_argument("--judge-params-file", default=None,
                   help="sampling params JSON for the judge endpoint")
    r.add_argument("--scenes", default=None,
                   help="comma-separated scene names; default = the current "
                        "standard set (non-standard sets are stamped)")
    r.add_argument("--system-file", default=None,
                   help="your agent's own system text (persona/identity), "
                        "prepended before the scene's world rules; part of "
                        "the agent definition — its md5 enters the seal")
    r.add_argument("--params-file", default=None,
                   help="JSON of sampling params (temperature, top_p, "
                        "max_tokens, ...) sent with every request; part of "
                        "the agent definition, published verbatim in the "
                        "seal; cannot override measurement fields")
    r.add_argument("--seeds", default="4242,777,31337",
                   help="comma-separated world seeds; each scene "
                        "is run once per seed, and the set is "
                        "stamped in the seal")
    r.add_argument("--runs-dir", default="runs",
                   help="directory the run is written under "
                        "(default: ./runs)")
    r.add_argument("--concurrency", type=int, default=1, metavar="N",
                   help="run up to N cells at once (default 1, the standard "
                        "sequential run). Cells are independent worlds; a "
                        "parallel run is stamped non-standard. Keep 1 on a "
                        "local server, where concurrent requests perturb the "
                        "numbers")
    r.add_argument("--stop-after-invalid", type=int, default=None,
                   metavar="N",
                   help="stop the grid once N cells have come back invalid. "
                        "Invalid cells often share one cause that will not "
                        "change (most often a sampling cap too small for the "
                        "model to answer at all — a starved turn), so the "
                        "rest of the grid buys nothing. What ran is still "
                        "judged and reported, marked PARTIAL")

    q = sub.add_parser("qualify", parents=[chrome],
                       help="run a judge through the "
                       "qualification exam (labelled calibration set)")
    q.add_argument("--judge", required=True,
                   help="OpenAI-compatible base URL of the judge sitting "
                        "the exam, or cli:claude (Claude Code CLI in "
                        "--safe-mode; badge stamped 'via')")
    q.add_argument("--judge-model", required=True,
                   help="model id on that endpoint — the badge is "
                        "granted to the endpoint+model pair")
    q.add_argument("--api-key",
                   default=_env_key("JOURNEYMAN_JUDGE_API_KEY", "JOURNEYMAN_API_KEY"),
                   help="judge key; defaults to $JOURNEYMAN_JUDGE_API_KEY, then "
                        "$JOURNEYMAN_API_KEY. Prefer the variable — an argument "
                        "is visible in `ps` and in shell history")
    q.add_argument("--params-file", default=None,
                   help="JSON of sampling params for the judge; "
                        "part of what the badge is granted to")
    q.add_argument("--runs-dir", default="runs",
                   help="directory the exam record is written "
                        "under (default: ./runs)")
    q.add_argument("--repeats", type=int, default=3,
                   help="judge draws per case, majority-voted (a badge is a "
                        "decision; one draw is noise). 1 = legacy single-draw.")
    q.add_argument("--early-exit", action="store_true",
                   help="abort as soon as any axis can mathematically no "
                        "longer reach the 0.8 bar (funnel/screening use; "
                        "default off — a full profile is worth keeping for "
                        "reference-judge candidates)")
    q.add_argument("--set", dest="cal_set", default=None,
                   help="path to a labelled calibration set (default: the "
                        "bundled v0 synthetic set — grants only PROVISIONAL)")
    q.add_argument("--concurrency", type=int, default=1,
                   help="judge calls in flight at once (default 1: sequential). "
                        "A case's draws are asked together; cases are still "
                        "scored in order, so the verdict logic does not change. "
                        "Use when the judge serves several slots")
    q.add_argument("--evidence", action="store_true",
                   help="hand the judge deterministic event-counts computed "
                        "from each record (prepared facts; the verdict stays "
                        "the judge's). Grants a separately-labelled "
                        "'QUALIFIED (evidence-fed)' badge — never the bare one.")

    rp = sub.add_parser("report", help="re-render report.md/json from an "
                        "existing run directory (e.g. after re-judging)")
    rp.add_argument("run_dir",
                    help="a finished run directory under runs/ — "
                         "its cell records are re-rendered, "
                         "nothing is re-run")

    up = sub.add_parser("upgrade", help="backfill `kind` into a report.json "
                        "written before the field existed (0.1.0)")
    up.add_argument("report_json",
                    help="a report.json written before 0.1.0; it "
                         "is read, never guessed at, and left "
                         "untouched without --write")
    up.add_argument("--write", action="store_true",
                    help="edit the file in place (default: print to stdout)")

    cp = sub.add_parser("compare", help="read two runs of the same agent as a "
                        "pair — typically without and with --system-file — "
                        "axis by axis: what the instruction opened, what "
                        "stayed low, what it cost")
    cp.add_argument("run_a", help="run dir of the first arm (e.g. no system "
                    "text); several repeats as a comma-separated list")
    cp.add_argument("run_b", help="run dir(s) of the second arm")
    cp.add_argument("--json", action="store_true", help="print the comparison as JSON")
    ul = sub.add_parser("uplift", help="run the same agent without and with a "
                        "system text, then `compare` the two arms. Everything "
                        "after `--` is passed to `run` unchanged for both arms")
    ul.add_argument("--system-file", required=True,
                    help="the instruction under test (arm B's --system-file)")
    ul.add_argument("--repeats", type=int, default=1, metavar="R",
                    help="runs per arm (default 1); with 2 or more, compare "
                         "shows the per-run range and calls a movement inside "
                         "overlapping ranges 'within repeat spread'")
    ul.add_argument("--runs-dir", default="runs",
                    help="arms are written under <runs-dir>/uplift-A and -B")
    ul.add_argument("run_args", nargs=argparse.REMAINDER,
                    help="-- followed by the `run` arguments (endpoint, model, …)")
    sub.add_parser("selftest", help="offline end-to-end pipeline check")

    from . import scenes  # noqa: F401 — official scenes register on import

    # current standard set — grows to v1 when the maze port lands, then seals
    STANDARD = {"scenes": "closed-roads-detour,closed-roads-noway,assayers-bench,"
                          "finished-cart,borrowed-story,unmarked-maze,night-relief,"
                          "night-watch,night-alarm,unsteady-scale",
                "seeds": "4242,777,31337"}

    args = ap.parse_args(argv)
    if args.cmd is None:
        from .banner import banner
        from .color import paint
        print(paint(banner(__version__), "amber"))
        ap.print_help()
        sys.exit(0)
    if args.cmd == "selftest":
        from .selftest import selftest
        sys.exit(selftest())
    if args.cmd == "upgrade":
        import json as _json
        from .report import upgrade_axes
        with open(args.report_json) as fh:
            rep = _json.load(fh)
        rep, unclassified = upgrade_axes(rep)
        text = _json.dumps(rep, indent=1, ensure_ascii=False)
        if args.write:
            with open(args.report_json, "w") as fh:
                fh.write(text + "\n")
            print(f"upgraded {args.report_json}", file=sys.stderr)
        else:
            print(text)
        if unclassified:
            print("could not classify (custom scenes? re-render from the run "
                  "dir instead): " + ", ".join(sorted(unclassified)),
                  file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    if args.cmd == "uplift":
        from .compare import compare, render as render_pair
        rest = [a for a in args.run_args if a != "--"]
        for banned in ("--system-file", "--runs-dir"):
            if banned in rest:
                sys.exit(f"uplift sets {banned} itself; drop it from the run arguments")
        arms = {"A": [], "B": []}
        for r in range(args.repeats):
            for arm in ("A", "B"):   # interleaved: drift over time lands on both arms
                print(f"[uplift] arm {arm} · repeat {r + 1}/{args.repeats}", flush=True)
                arms[arm].append(_run_arm(rest, os.path.join(args.runs_dir, f"uplift-{arm}"),
                                          args.system_file if arm == "B" else None))
        print(render_pair(compare(arms["A"], arms["B"])))
        sys.exit(0)
    if args.cmd == "compare":
        from .compare import compare, render as render_pair
        result = compare(args.run_a.split(","), args.run_b.split(","))
        print(__import__("json").dumps(result, ensure_ascii=False, indent=1) if args.json
              else render_pair(result))
        sys.exit(0)
    if args.cmd == "report":
        rd = RunDir.attach(args.run_dir)
        first = next(iter(rd.read_cells()), None)
        if first is None:
            sys.exit("no cells in run dir")
        seal = first["seal"]
        judged_self = True   # re-render cannot know; stamp conservatively
        print(render(rd, seal, "(re-rendered — judge per cell records)",
                     self_judged=judged_self))
        _warn_if_nothing_measured(rd)
        sys.exit(0)
    if args.cmd == "qualify":
        import json as _json
        from .qualify import main as qmain
        if not args.quiet:
            from .banner import banner
            from .color import paint
            print(paint(banner(__version__), "amber"))
        params = _json.load(open(args.params_file)) if args.params_file else None
        if args.judge.startswith("cli:"):
            from .cli_backend import CliEndpoint
            ep = CliEndpoint(args.judge[4:], args.judge_model)
        else:
            ep = Endpoint(args.judge, args.judge_model, args.api_key,
                          params=params)
        sys.exit(qmain(args, ep))

    seeds = [int(s) for s in args.seeds.split(",")]
    if args.scenes is None:
        args.scenes = STANDARD["scenes"]
    scenes = args.scenes.split(",")
    unknown = [n for n in scenes if n not in scene_mod.REGISTRY]
    if unknown:
        # Checked before the model is resolved, so a typo costs no call.
        print(f"unknown scene: {', '.join(unknown)}\n"
              f"available: {', '.join(sorted(scene_mod.REGISTRY))}",
              file=sys.stderr)
        sys.exit(2)
    import json as _json
    cli_agent = args.endpoint.startswith(("cli:", "cli-agent:"))
    if cli_agent:
        # cli:<kind>       the MODEL through a CLI: journeyman's own driver runs the turns
        # cli-agent:<kind> the CLI as an AGENT with its own loop, scene tools over MCP
        if args.model is None:
            print("--endpoint cli:… needs --model with a full model id "
                  "(an alias can resolve to another version)", file=sys.stderr)
            sys.exit(2)
        if args.params_file:
            print("--params-file has no effect on a CLI agent (it sends no "
                  "sampling parameters); drop it", file=sys.stderr)
            sys.exit(2)
        params = None
        kind = args.endpoint.split(":", 1)[1]
        if args.endpoint.startswith("cli-agent:"):
            from .cli_agent import CliAgent
            endpoint = CliAgent(kind, args.model)
        else:
            from .cli_backend import CliEndpoint
            endpoint = CliEndpoint(kind, args.model)
    else:
        if args.model is None:
            args.model = resolve_model(args.endpoint, args.api_key)
            if args.model is None:
                sys.exit(1)
        params = _json.load(open(args.params_file)) if args.params_file else None
        endpoint = Endpoint(args.endpoint, args.model, args.api_key, params=params)
    self_judged = args.judge is None
    jparams = (_json.load(open(args.judge_params_file))
               if args.judge_params_file else None)

    def _judge(url, model):
        if url.startswith("cli:"):
            from .cli_backend import CliEndpoint
            return CliEndpoint(url[4:], model)
        return Endpoint(url, model, args.judge_api_key, params=jparams)

    if self_judged:
        judge_ep = (_judge("cli:" + args.endpoint.split(":", 1)[1], args.model) if cli_agent else endpoint)
    else:
        judge_ep = _judge(args.judge, args.judge_model or args.model)
    judge_label = "SELF (default)" if self_judged else args.judge

    if not args.quiet:
        from .banner import banner
        from .color import paint
        print(paint(banner(__version__), "amber"))
        print(f"scenes {scenes} · seeds {seeds}")
    if self_judged:
        print("judge: SELF — scores will be marked NOT COMPARABLE; "
              "use --judge for a reference judge")
    warn = None if cli_agent else uncapped_warning(params, endpoint.timeout)   # the CLI caps its own output
    if warn:
        print(warn)
    agent_system = open(args.system_file).read() if args.system_file else None
    run_dir = RunDir(args.runs_dir)
    say = (lambda *a, **k: None) if args.quiet else print
    stopped = None
    try:
        seal = run_grid(endpoint, scenes, seeds, run_dir,
                        log=say, agent_system=agent_system,
                        stop_after_invalid=args.stop_after_invalid,
                        concurrency=args.concurrency)
    except StoppedOnInvalid as e:
        # The cells already written stay, and they are still judged and
        # reported: a partial run that says so beats a full run nobody reads.
        from .color import paint as _paint
        stopped, seal = str(e), e.seal
        print(_paint(f"STOPPED: {stopped}", "red"))

    say("--- judging phase ---")
    judge_meter = {}
    run_dir.event("judging_start", judge=judge_label)
    for cell in list(run_dir.read_cells()):
        if cell["invalid"]:
            continue
        cls = scene_mod.REGISTRY[cell["scene"]]
        cell["verdicts"] = judge_cell(judge_ep, cls(), cell, meter=judge_meter)
        run_dir.write_cell(cell["cell_id"], cell)
        run_dir.event("cell_judged", cell=cell["cell_id"],
                      verdicts={a: v["verdict"]
                                for a, v in cell["verdicts"].items()})
    run_dir.event("judging_end", **judge_meter)
    if judge_meter:
        spent = (f" · charged {judge_meter['cost']}" if "cost" in judge_meter else "")
        print(f"judge: {judge_meter.get('calls', 0)} calls · "
              f"{judge_meter.get('tokens_in', 0)} in / "
              f"{judge_meter.get('tokens_out', 0)} out tok{spent}")
    # NOTE: no composite score yet, deliberately — its weights are not
    # grounded in any measurement; an invented weight is a fabricated
    # number. Composite lands with the reference runs (TODO).

    devs = [f"{key}={getattr(args, key)}" for key, std in STANDARD.items()
            if getattr(args, key) != std]
    if args.concurrency > 1:
        devs.append(f"concurrency={args.concurrency}")
    print(render(run_dir, seal, judge_label, self_judged,
                 nonstandard=", ".join(devs) if devs else None,
                 judge_meter=judge_meter))
    _warn_if_nothing_measured(run_dir)
    if stopped:
        from .color import paint as _paint
        print(_paint(f"PARTIAL RUN — stopped early: {stopped}", "red"))
    print(f"report: {run_dir.path}/report.md")


if __name__ == "__main__":
    main()
