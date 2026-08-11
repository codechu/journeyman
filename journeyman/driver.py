"""Grid driver: scene × seed, sequential, crash-safe, honestly noisy.

Sequential by design: parallel batching perturbs local-model numerics
(measured in the house, 2026-08-11 — cache/batch effects break bit-level
reproducibility). Flexibility is allowed but stamped; comparability only
from the standard run.

Progress rules (release requirements, not polish):
  * every line meaningful, line-buffered, timestamped in events.jsonl
  * ETA only from MEASURED cell times, never before the first cell
  * a failing cell is named INVALID with its reason, live — no silent retry
  * silence is never "still working": heartbeat every 60s inside a cell
"""
import json
import time
import urllib.request

from .record import RunDir, make_seal
from .scene import REGISTRY

HEARTBEAT_S = 60


class Endpoint:
    """Minimal OpenAI-compatible chat/completions client (stdlib only).

    We send messages, tools, model — and seed when given. Sampling stays
    the agent's business: the measured unit is everything behind the URL.
    """

    def __init__(self, url, model, api_key=None, timeout=300, params=None):
        self.url = url.rstrip("/") + "/v1/chat/completions"
        self.model, self.api_key, self.timeout = model, api_key, timeout
        # sampling params are part of the AGENT definition (temperature,
        # top_p, max_tokens, ...). They merge into the body but can NEVER
        # override the measurement fields; published verbatim in the seal.
        self.params = params or {}

    def chat(self, messages, tools, seed=None):
        body = dict(self.params)
        body.update({"model": self.model, "messages": messages, "tools": tools})
        if seed is not None:
            body["seed"] = seed
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(self.url, json.dumps(body).encode(), headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.load(r)
        msg = data["choices"][0]["message"]
        usage = data.get("usage", {})
        return msg, usage


def run_cell(endpoint, scene, seed, log, agent_system=None):
    """One cell: drive the tool loop until report, budget death, or error.

    agent_system: the submitter's own system text (their agent's persona/
    identity) — part of the AGENT definition, hashed into the seal. It is
    prepended; the scene's own system (world rules) always follows and
    cannot be overridden."""
    inst = scene.build(seed)
    system = "\n\n".join(t for t in (agent_system, inst.system) if t)

    def fresh_conversation(opening):
        return ([{"role": "system", "content": system}] if system else []) + \
            [{"role": "user", "content": opening}]

    # `convo` is what the endpoint SEES (current episode only — a new
    # watch remembers nothing); `archive` keeps every prior episode for
    # the record. Together they are the full cell transcript.
    convo = fresh_conversation(inst.task
                               + f"\n\nTool budget: {inst.budget} calls.")
    archive = []
    episode_starts = [0]
    calls = tin = tout = 0
    usage_seen = False
    t0 = last_beat = time.time()
    final_text = None
    while True:
        msg, usage = endpoint.chat(convo, inst.tools, seed=seed)
        usage_seen = usage_seen or bool(usage)
        tin += usage.get("prompt_tokens", 0)
        tout += usage.get("completion_tokens", 0)
        convo.append({k: v for k, v in msg.items() if v is not None})
        if time.time() - last_beat > HEARTBEAT_S:
            log(f"    still working · {calls} calls · {int(time.time()-t0)}s")
            last_beat = time.time()
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            final_text = (msg.get("content") or "").strip() or None
            break
        for tc in tool_calls:
            calls += 1
            fn = tc["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                args = {"_unparsed": fn.get("arguments")}
            result = (inst.tool_result(fn["name"], args)
                      if calls <= inst.budget else
                      "budget exhausted: no further calls are answered")
            convo.append({"role": "tool", "tool_call_id": tc["id"],
                          "content": result})
        if inst.done:
            # multi-episode scenes (e.g. Night Relief): the world persists,
            # the conversation does not — the next watch wakes with only
            # what the scene hands it (a page, a bell, a task).
            opening = (inst.next_episode()
                       if hasattr(inst, "next_episode") else None)
            if opening:
                inst.done = False
                archive += convo
                episode_starts.append(len(archive))
                convo = fresh_conversation(opening)
                continue
            break
        if calls > inst.budget + 2:   # hard stop: runaway loop guard
            break
    return {"messages": archive + convo, "episode_starts": episode_starts,
            "final_text": final_text, "budget": inst.budget,
            "calls": calls, "tokens_in": tin, "tokens_out": tout,
            "usage_reported": usage_seen,   # 0 tokens != unknown tokens
            "seconds": round(time.time() - t0, 1)}


def run_grid(endpoint, scene_names, seeds, run_dir: RunDir, log=print,
             scene_set="dev", bench_version="0.0.1-skeleton",
             agent_system=None):
    scenes = {n: REGISTRY[n] for n in scene_names}
    seal = make_seal(bench_version, scene_set, scenes, seeds, endpoint.model,
                     agent_system=agent_system,
                     agent_params=getattr(endpoint, "params", None) or None)
    run_dir.event("run_start", seal=seal)
    cells = [(n, s) for n in scene_names for s in seeds]
    done_s = []
    for i, (name, seed) in enumerate(cells, 1):
        cell_id = f"{name}_s{seed}"
        if run_dir.cell_done(cell_id):
            log(f"[{i:>2}/{len(cells)}] {cell_id} — already done (resume), skipped")
            continue
        scene = scenes[name]()
        run_dir.event("cell_start", cell=cell_id)
        try:
            rec = run_cell(endpoint, scene, seed, log,
                           agent_system=agent_system)
            invalid, reason = False, None
        except Exception as e:
            rec = {"messages": [], "final_text": None, "budget": 0, "calls": 0,
                   "tokens_in": 0, "tokens_out": 0, "seconds": 0.0}
            invalid, reason = True, repr(e)
        # the record is assembled FIRST; events are computed FROM it —
        # replay-based scenes need the seed, which lives on the record
        record = {"cell_id": cell_id, "scene": name, "seed": seed, "seal": seal,
                  "invalid": invalid, "invalid_reason": reason,
                  "events": None, "event_axes": None, "verdicts": None, **rec}
        if not invalid:
            record["events"] = scene.events(record)
            record["event_axes"] = scene.event_axes(record["events"])
        run_dir.write_cell(cell_id, record)
        run_dir.event("cell_end", cell=cell_id, invalid=invalid, reason=reason,
                      calls=rec["calls"], seconds=rec["seconds"])
        if invalid:
            log(f"[{i:>2}/{len(cells)}] {cell_id} → INVALID ({reason}); "
                f"see cells/{cell_id}.json")
        else:
            done_s.append(rec["seconds"])
            mark = "✓ report" if rec["final_text"] else "✗ no report"
            log(f"[{i:>2}/{len(cells)}] {cell_id}  {rec['calls']} calls · "
                f"{rec['seconds']}s · {mark}")
            if done_s:
                eta = int(sum(done_s) / len(done_s) * (len(cells) - i))
                log(f"        cells {i}/{len(cells)} · ETA ~{eta}s (measured avg)")
    run_dir.event("run_end")
    return seal
