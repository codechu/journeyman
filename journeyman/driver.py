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
import urllib.error
import urllib.request

from . import __version__
from .color import paint
from .record import BUDGET_REFUSED, RunDir, make_seal
from .scene import REGISTRY

HEARTBEAT_S = 60


def chat_url(url):
    """The chat/completions URL for a base that may already carry a suffix.

    `list_models` has always accepted a bare host, a `/v1`, or a full
    `/v1/chat/completions`; this did not, and appended blindly. An endpoint
    given as `.../v1` therefore passed the model listing and 404'd on every
    actual call — a run that completes, reports nothing, and looks like a
    model that said nothing rather than a URL that was never reached.
    """
    base = url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def reasoning_text(msg):
    """The thinking a provider exposes on one message, however it names it.

    Three spellings in the wild: `reasoning_content` (vLLM, DeepSeek-style),
    `reasoning` (OpenRouter), and `reasoning_details` (OpenRouter's
    structured form). The starved-turn guard read only the first, so on
    every OpenRouter run it never fired: five cells of a 2026-08-31
    calibration run closed with an empty turn after 77-256 characters of
    visible reasoning and were scored as silent agents. The unit test
    could not catch it — its fake agent emitted the one field the code
    already read.
    """
    for key in ("reasoning_content", "reasoning"):
        val = msg.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    details = msg.get("reasoning_details")
    if isinstance(details, list):
        parts = [d.get("text", "") for d in details if isinstance(d, dict)]
        joined = "\n".join(p for p in parts if p)
        if joined.strip():
            return joined.strip()
    return ""


class Starved(Exception):
    """A turn that produced no move because it had no room to.

    Distinguished from silence deliberately: silence is behaviour and is
    scored; starvation is a measurement fault and voids the cell, exactly
    as a timeout does.
    """


class Endpoint:
    """Minimal OpenAI-compatible chat/completions client (stdlib only).

    We send messages, tools, model — and seed when given. Sampling stays
    the agent's business: the measured unit is everything behind the URL.
    """

    def __init__(self, url, model, api_key=None, timeout=300, params=None):
        self.url = chat_url(url)
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
        payload = json.dumps(body).encode()
        # Transport faults are not agent behaviour: a 429, a timeout, or a
        # body that is not JSON produced no move, so re-asking the same
        # question measures nothing twice. Three attempts with backoff;
        # then the cell is INVALID, loudly. (2026-08-23: a truncated body
        # and a 429 storm each voided finished-looking cells on the first
        # leaderboard cohort.) A 4xx other than 429 is our fault, not a
        # transient — it raises at once.
        for attempt in range(3):
            try:
                req = urllib.request.Request(self.url, payload, headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.load(r)
                if "choices" not in data:
                    raise KeyError(f"choices (body: {str(data)[:200]})")
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 and e.code < 500:
                    raise
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
            except (urllib.error.URLError, TimeoutError, ValueError,
                    KeyError, OSError):
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
        choice = data["choices"][0]
        msg = choice["message"]
        # Kept because it is the only thing that separates an agent which
        # stopped from one that was cut off mid-word. Discarding it made the
        # two indistinguishable in the record.
        if choice.get("finish_reason"):
            msg = dict(msg, finish_reason=choice["finish_reason"])
        usage = data.get("usage", {})
        return msg, usage


def list_models(url, api_key=None, timeout=15):
    """GET {base}/v1/models — the OpenAI-compatible model list. Returns
    the ids, or [] if the endpoint doesn't expose one."""
    base = url.rstrip("/")
    if base.endswith("/v1/chat/completions"):
        base = base[: -len("/chat/completions")]
    elif not base.endswith("/v1"):
        base = base + "/v1"
    req = urllib.request.Request(base + "/models")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    return [m.get("id") for m in data.get("data", []) if m.get("id")]


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
            # An empty completion is not a silent agent. A reasoning model
            # spends a fixed budget thinking before it writes, and when the
            # budget runs out first the body comes back empty — the model
            # produced no move, which is the same category as a timeout and
            # is already handled that way above. Scored as behaviour it
            # zeroes every axis that reads the closing report, and the
            # profile then describes the token budget rather than the agent.
            if final_text is None:
                thought = reasoning_text(msg)
                starved = (msg.get("finish_reason") == "length"
                           or len(thought) > 200)
                if starved:
                    raise Starved(
                        f"the closing turn came back empty after "
                        f"{len(thought)} "
                        f"characters of reasoning"
                        + (" (finish_reason: length)"
                           if msg.get("finish_reason") == "length" else "")
                        + " — raise max_tokens in --params-file; this is a "
                          "starved turn, not a silent agent")
            break
        for tc in tool_calls:
            calls += 1
            fn = tc["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                args = {"_unparsed": fn.get("arguments")}
            result = (inst.tool_result(fn["name"], args)
                      if calls <= inst.budget else BUDGET_REFUSED)
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


class StoppedOnInvalid(RuntimeError):
    """Raised when invalid cells cross the operator's declared limit.

    A cell can come back invalid for reasons that will repeat on every
    remaining cell — most often a sampling cap below what the model needs
    to answer at all (a starved turn). Left alone, the grid spends the
    whole budget producing cells nobody will read. Measured 2026-08-31: a
    reasoning model starved 5 of 30 cells against a 4000-token cap, and
    the run took two and a half hours to say what its first starved cell
    already said. Money was not the loss; time was.

    Carries the seal so the caller can still judge and report what ran.
    """

    def __init__(self, message, seal=None):
        super().__init__(message)
        self.seal = seal


def run_grid(endpoint, scene_names, seeds, run_dir: RunDir, log=print,
             scene_set="dev", bench_version=__version__,
             agent_system=None, stop_after_invalid=None):
    scenes = {n: REGISTRY[n] for n in scene_names}
    seal = make_seal(bench_version, scene_set, scenes, seeds, endpoint.model,
                     agent_system=agent_system,
                     agent_params=getattr(endpoint, "params", None) or None)
    run_dir.event("run_start", seal=seal)
    cells = [(n, s) for n in scene_names for s in seeds]
    done_s = []
    invalid_n = 0
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
            log(f"[{i:>2}/{len(cells)}] {cell_id} → "
                f"{paint(f'INVALID ({reason})', 'red')}; "
                f"see cells/{cell_id}.json")
            invalid_n += 1
            if stop_after_invalid and invalid_n >= stop_after_invalid:
                run_dir.event("run_stopped", invalid=invalid_n,
                              limit=stop_after_invalid, done=i,
                              of=len(cells))
                raise StoppedOnInvalid(
                    f"{invalid_n} invalid cells (limit {stop_after_invalid}) "
                    f"after {i}/{len(cells)} — stopping rather than spending "
                    f"the rest of the grid on cells that will read the same. "
                    f"Last reason: {reason}", seal=seal)
        else:
            done_s.append(rec["seconds"])
            # The scene says which event means "closed"; prose is the fallback
            # only for scenes that declare none (the selftest well). Reading
            # final_text here called every cell a failure when the agent ended
            # on the closing tool call and wrote nothing after it.
            ce = getattr(scene, "closing_event", None)
            filed = (bool((record["events"] or {}).get(ce)) if ce
                     else bool(rec["final_text"]))
            mark = (paint("✓ closed", "green") if filed
                    else paint("✗ never closed", "red"))
            log(f"[{i:>2}/{len(cells)}] {cell_id}  {rec['calls']} calls · "
                f"{rec['seconds']}s · {mark}")
            if done_s:
                eta = int(sum(done_s) / len(done_s) * (len(cells) - i))
                log(f"        cells {i}/{len(cells)} · ETA ~{eta}s (measured avg)")
    run_dir.event("run_end")
    return seal
