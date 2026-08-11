"""CLI: journeyman run --endpoint <url> --model <name> [--judge <url>]

Skeleton commands:
  run       drive the grid, judge, report
  selftest  run the whole pipeline offline against a scripted fake
            endpoint — proves the bones without any model

TODO(muscle): qualify (judge qualification exam) · report (re-render).
"""
import argparse
import sys

from .driver import Endpoint, run_grid
from .judge import judge_cell
from .record import RunDir
from .report import render
from . import scene as scene_mod


def main(argv=None):
    # never crash on console encoding (legacy Windows consoles cannot
    # print ✓/✗/box-drawing): degrade characters, keep running
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(prog="journeyman")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run the benchmark against an endpoint")
    r.add_argument("--endpoint", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--api-key", default=None)
    r.add_argument("--judge", default=None,
                   help="judge endpoint URL (default: the endpoint itself — "
                        "dev mode, scores marked NOT COMPARABLE)")
    r.add_argument("--judge-model", default=None)
    r.add_argument("--judge-api-key", default=None,
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
    r.add_argument("--seeds", default="4242,777,31337")
    r.add_argument("--runs-dir", default="runs")

    q = sub.add_parser("qualify", help="run a judge through the "
                       "qualification exam (labelled calibration set)")
    q.add_argument("--judge", required=True)
    q.add_argument("--judge-model", required=True)
    q.add_argument("--api-key", default=None)
    q.add_argument("--params-file", default=None)
    q.add_argument("--runs-dir", default="runs")

    rp = sub.add_parser("report", help="re-render report.md/json from an "
                        "existing run directory (e.g. after re-judging)")
    rp.add_argument("run_dir")

    sub.add_parser("selftest", help="offline end-to-end pipeline check")

    from . import scenes  # noqa: F401 — official scenes register on import

    # current standard set — grows to v1 when the maze port lands, then seals
    STANDARD = {"scenes": "closed-roads-detour,closed-roads-noway,assayers-bench,"
                          "finished-cart,borrowed-story,unmarked-maze,night-relief",
                "seeds": "4242,777,31337"}

    args = ap.parse_args(argv)
    if args.cmd == "selftest":
        from .selftest import selftest
        sys.exit(selftest())
    if args.cmd == "report":
        rd = RunDir.attach(args.run_dir)
        first = next(iter(rd.read_cells()), None)
        if first is None:
            sys.exit("no cells in run dir")
        seal = first["seal"]
        judged_self = True   # re-render cannot know; stamp conservatively
        print(render(rd, seal, "(re-rendered — judge per cell records)",
                     self_judged=judged_self))
        sys.exit(0)
    if args.cmd == "qualify":
        import json as _json
        from .qualify import main as qmain
        params = _json.load(open(args.params_file)) if args.params_file else None
        ep = Endpoint(args.judge, args.judge_model, args.api_key, params=params)
        sys.exit(qmain(args, ep))

    seeds = [int(s) for s in args.seeds.split(",")]
    if args.scenes is None:
        args.scenes = STANDARD["scenes"]
    scenes = args.scenes.split(",")
    import json as _json
    params = _json.load(open(args.params_file)) if args.params_file else None
    endpoint = Endpoint(args.endpoint, args.model, args.api_key, params=params)
    self_judged = args.judge is None
    jparams = (_json.load(open(args.judge_params_file))
               if args.judge_params_file else None)
    judge_ep = (endpoint if self_judged else
                Endpoint(args.judge, args.judge_model or args.model,
                         args.judge_api_key, params=jparams))
    judge_label = "SELF (default)" if self_judged else args.judge

    from . import __version__
    print(f"""\
┌─────────────────────────────────────────────────────────┐
│  JOURNEYMAN  v{__version__:<20} process-quality bench │
│  measures how agents work — and how they fail           │
└─────────────────────────────────────────────────────────┘""")
    print(f"scenes {scenes} · seeds {seeds}")
    if self_judged:
        print("judge: SELF — scores will be marked NOT COMPARABLE; "
              "use --judge for a reference judge")
    agent_system = open(args.system_file).read() if args.system_file else None
    run_dir = RunDir(args.runs_dir)
    seal = run_grid(endpoint, scenes, seeds, run_dir,
                    agent_system=agent_system)

    print("--- judging phase ---")
    run_dir.event("judging_start", judge=judge_label)
    for cell in list(run_dir.read_cells()):
        if cell["invalid"]:
            continue
        cls = scene_mod.REGISTRY[cell["scene"]]
        cell["verdicts"] = judge_cell(judge_ep, cls(), cell)
        run_dir.write_cell(cell["cell_id"], cell)
        run_dir.event("cell_judged", cell=cell["cell_id"],
                      verdicts={a: v["verdict"]
                                for a, v in cell["verdicts"].items()})
    run_dir.event("judging_end")
    # NOTE: no composite score yet, deliberately — its weights are not
    # grounded in any measurement; an invented weight is a fabricated
    # number. Composite lands with the reference runs (TODO(muscle)).

    devs = [f"{key}={getattr(args, key)}" for key, std in STANDARD.items()
            if getattr(args, key) != std]
    print(render(run_dir, seal, judge_label, self_judged,
                 nonstandard=", ".join(devs) if devs else None))
    print(f"report: {run_dir.path}/report.md")


if __name__ == "__main__":
    main()
