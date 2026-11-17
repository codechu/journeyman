"""A CLI agent (Claude Code) as the agent of a cell, with its OWN agent loop.

The HTTP path drives a model turn by turn. A CLI agent runs its own loop, so
journeyman only gives it the scene: the CLI is started per episode in its
barest mode (no settings files, no built-in tools, empty system prompt of its
own), and the scene's tools reach it over MCP from an in-process server
(mcp_server.py). Every tool call goes through the same per-call rules as the
HTTP path (driver.Ledger), so budget, refusal and late closing mean the same
thing on both routes. The unit under measurement is the model *through that
CLI*: the seal and the report say so.

The cell record is rebuilt from the CLI's stream-json in the HTTP path's
shape (OpenAI-style messages), and checked against what the server actually
answered: every tool call in the stream must be one the server answered, in
the same order with the same text, or the cell is invalid. That check is the
route's own known positive — a transcript the scene never saw is not a cell.

Measured with claude 2.1.301 (2026-11-17): `--setting-sources ""` loads no
user CLAUDE.md (hidden context ~739 tokens) and still allows MCP, while
`--safe-mode` disables MCP; each MCP request carries the tool-use id
(`_meta.claudecode/toolUseId`); the calls of one message are executed one at
a time; the `tool_use` event is streamed before its call reaches the server.
"""
import json
import os
import signal
import subprocess
import tempfile
import threading
import time

from .driver import Ledger, HEARTBEAT_S
from .mcp_server import McpServer

PREFIX = "mcp__scene__"
CELL_CLOSED = "cell closed: no further calls are answered"
SUPPORTED = ("claude",)


class CliCellError(RuntimeError):
    """A cell the CLI route could not measure; the message names why."""


class CliAgent:
    """Duck-types the HTTP Endpoint for run_grid: model, params, run_cell()."""

    def __init__(self, kind, model, exe=None, timeout=1800, grace=30):
        if kind not in SUPPORTED:
            raise ValueError(f"unsupported CLI agent {kind!r}; supported: {SUPPORTED}")
        self.kind, self.model = kind, model
        self.exe = exe or "claude"
        self.timeout, self.grace = timeout, grace
        self.params = {}            # sampling is the CLI's; nothing is sent
        self.via = f"cli:{kind}"
        self._settings = None

    @property
    def settings(self):
        """What sat the exam: the CLI's version and flags; effort and seed are not set."""
        if self._settings is None:
            try:
                out = subprocess.run([self.exe, "--version"], text=True,
                                     capture_output=True, timeout=30)
                version = (out.stdout.strip().splitlines() or ["unknown"])[0]
            except (OSError, subprocess.SubprocessError):
                version = "unknown"
            self._settings = {"route": self.via, "cli": version,
                              "flags": " ".join(self._flags("<system>", "<mcp>", ["<tools>"])),
                              "effort": "cli default (not set)", "seed": "not sent"}
        return self._settings

    def _flags(self, system, mcp_url, tool_names):
        cfg = json.dumps({"mcpServers": {"scene": {"type": "http", "url": mcp_url}}})
        return ["-p", "--setting-sources", "", "--exclude-dynamic-system-prompt-sections",
                "--model", self.model, "--system-prompt", system, "--tools", "",
                "--mcp-config", cfg, "--strict-mcp-config",
                "--allowedTools", ",".join(PREFIX + n for n in tool_names),
                "--no-session-persistence", "--output-format", "stream-json", "--verbose"]

    def run_cell(self, scene, seed, log, agent_system=None):
        t0 = time.time()
        inst = scene.build(seed)
        system = "\n\n".join(t for t in (agent_system, inst.system) if t)
        ledger = Ledger(inst)
        names = [t["function"]["name"] for t in inst.tools]
        messages, episode_starts = [], [0]
        totals = {"in": 0, "out": 0, "seen": False}
        post_close = []
        opening = inst.task + f"\n\nTool budget: {inst.budget} calls."
        server = McpServer()
        try:
            while True:
                ep = _Episode(self, server, inst, ledger, system, opening, names,
                              scene.name, seed, log, t0)
                ep.run()
                messages += ep.messages
                post_close += ep.post_close
                totals["in"] += ep.tokens_in
                totals["out"] += ep.tokens_out
                totals["seen"] = totals["seen"] or ep.usage_seen
                final_text = ep.final_text
                if inst.done and not ledger.runaway:
                    nxt = (inst.next_episode() if hasattr(inst, "next_episode") else None)
                    if nxt:
                        inst.done = False
                        episode_starts.append(len(messages))
                        opening = nxt
                        continue
                break
        finally:
            server.close()
        rec = {"messages": messages, "episode_starts": episode_starts,
               "final_text": final_text, "budget": inst.budget,
               "calls": ledger.calls, "tokens_in": totals["in"], "tokens_out": totals["out"],
               "late_closing": ledger.late_closing, "usage_reported": totals["seen"],
               "seconds": round(time.time() - t0, 1)}
        if post_close:
            rec["post_close"] = post_close
        return rec


class _Episode:
    """One CLI process: one conversation, the scene's state shared with the cell."""

    def __init__(self, agent, server, inst, ledger, system, opening, names,
                 scene_name, seed, log, t0):
        self.a, self.server, self.inst, self.ledger = agent, server, inst, ledger
        self.system, self.opening, self.names = system, opening, names
        self.log, self.t0 = log, t0
        self.key = f"{scene_name}_s{seed}"
        self.lock = threading.Lock()
        self.tid_msg = {}          # tool-use id → assistant message id (from the stream)
        self.answered = []         # (tool-use id, name, args, result) the server counted
        self.post_close = []
        self.closing_msg = None    # message id whose calls closed the cell
        self.closed_at = None
        self.messages = ([{"role": "system", "content": system}] if system else []) + \
            [{"role": "user", "content": opening}]
        self.final_text = None
        self.tokens_in = self.tokens_out = 0
        self.usage_seen = False
        self._usage = {}
        self._errors = []

    # --- server side -----------------------------------------------------
    def answer(self, name, args, meta):
        tid = meta.get("claudecode/toolUseId")
        deadline = time.time() + 5
        while tid not in self.tid_msg and time.time() < deadline:
            time.sleep(0.02)   # the stream announces the call first (measured)
        with self.lock:
            msg_id = self.tid_msg.get(tid)
            if tid is None or msg_id is None:
                self._errors.append(f"call {name} could not be bound to the stream (id {tid!r})")
                return CELL_CLOSED
            if self.closing_msg is not None and msg_id != self.closing_msg:
                self.post_close.append({"id": tid, "name": name, "arguments": args})
                return CELL_CLOSED
            result = self.ledger.answer(name, args)
            self.answered.append((tid, name, args, result))
            if (self.inst.done or self.ledger.runaway) and self.closing_msg is None:
                self.closing_msg, self.closed_at = msg_id, time.time()
            return result

    # --- process + stream ------------------------------------------------
    def run(self):
        url = self.server.register(self.key, self.inst.tools, self.answer)
        cmd = [self.a.exe] + self.a._flags(self.system, url, self.names)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, cwd=tempfile.mkdtemp(),
                                start_new_session=True)
        proc.stdin.write(self.opening)
        proc.stdin.close()
        reader = threading.Thread(target=self._read, args=(proc,), daemon=True)
        reader.start()
        last_beat = time.time()
        killed = None
        while proc.poll() is None:
            now = time.time()
            if now - self.t0 > self.a.timeout:
                killed = "timeout"
            elif self.closed_at and now - self.closed_at > self.a.grace:
                killed = "closed"
            if killed:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                break
            if now - last_beat > HEARTBEAT_S:
                self.log(f"    still working · {self.ledger.calls} calls · {int(now - self.t0)}s")
                last_beat = now
            time.sleep(0.2)
        reader.join(15)
        violations = self.server.violations(url)
        self.server.unregister(url)
        if killed == "timeout":
            raise CliCellError(f"cli agent timed out after {self.a.timeout}s")
        if violations:
            raise CliCellError("mcp violations: " + "; ".join(violations))
        if self._errors:
            raise CliCellError("; ".join(self._errors))
        if killed != "closed":
            r = self._result
            if r is None:
                raise CliCellError(f"cli agent ended without a result (exit {proc.returncode})")
            if r.get("is_error") or r.get("subtype") != "success":
                raise CliCellError(f"cli agent failed: {r.get('subtype')}: {str(r.get('result'))[:300]}")
            used = list((r.get("modelUsage") or {}).keys())
            if self.a.model not in used:
                raise CliCellError(f"cli ran {used}, asked for {self.a.model} (use a full model id)")
        self._check_parity()

    _result = None

    def _read(self, proc):
        cur = None     # the assistant message being assembled
        for line in proc.stdout:
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            ty = ev.get("type")
            if ty == "system" and ev.get("subtype") == "compact_boundary":
                self._errors.append("the CLI compacted its history mid-cell")
            elif ty == "assistant":
                m = ev["message"]
                mid = m.get("id")
                u = m.get("usage") or {}
                if u:
                    self._usage[mid] = u
                if cur is None or cur["_id"] != mid:
                    if self._past_close():
                        cur = None
                        continue
                    cur = {"_id": mid, "role": "assistant", "_text": [], "tool_calls": []}
                    self.messages.append(cur)
                for b in m.get("content", []):
                    if b.get("type") == "text":
                        cur["_text"].append(b.get("text", ""))
                    elif b.get("type") == "thinking":
                        cur.setdefault("_think", []).append(b.get("thinking", ""))
                    elif b.get("type") == "tool_use":
                        name = b.get("name", "")
                        if not name.startswith(PREFIX):
                            self._errors.append(f"call to a tool outside the scene: {name}")
                        with self.lock:
                            self.tid_msg[b["id"]] = mid
                        cur["tool_calls"].append({"id": b["id"], "type": "function", "function": {
                            "name": name[len(PREFIX):], "arguments": json.dumps(b.get("input", {}))}})
            elif ty == "user":
                for b in ev.get("message", {}).get("content", []) or []:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        if any(p["id"] == b.get("tool_use_id") for p in self.post_close):
                            continue   # post-close answers stay out of the record
                        c = b.get("content")
                        text = c if isinstance(c, str) else "".join(x.get("text", "") for x in (c or []) if isinstance(x, dict))
                        self.messages.append({"role": "tool", "tool_call_id": b.get("tool_use_id"), "content": text})
            elif ty == "result":
                self._result = ev
        self._finish_messages()

    def _past_close(self):
        return self.closing_msg is not None

    def _finish_messages(self):
        out = []
        for m in self.messages:
            if m.get("role") != "assistant" or "_id" not in m:
                out.append(m)
                continue
            msg = {"role": "assistant"}
            text = "".join(m["_text"])
            if text:
                msg["content"] = text
            if m.get("_think"):
                msg["reasoning_content"] = "".join(m["_think"])
            if m["tool_calls"]:
                msg["tool_calls"] = m["tool_calls"]
            out.append(msg)
        self.messages = out
        last = out[-1] if out else {}
        if last.get("role") == "assistant" and not last.get("tool_calls") and self.closing_msg is None:
            self.final_text = (last.get("content") or "").strip() or None
        for u in self._usage.values():
            self.usage_seen = True
            self.tokens_in += (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) \
                + (u.get("cache_creation_input_tokens") or 0)
            self.tokens_out += u.get("output_tokens") or 0

    def _check_parity(self):
        stream_calls = [tc["id"] for m in self.messages for tc in m.get("tool_calls", [])]
        server_calls = [a[0] for a in self.answered]
        if stream_calls != server_calls:
            raise CliCellError(f"stream and server disagree on the calls: stream {len(stream_calls)}, "
                               f"server {len(server_calls)}")
        results = {m["tool_call_id"]: m["content"] for m in self.messages if m.get("role") == "tool"}
        for tid, _name, _args, result in self.answered:
            if results.get(tid) != result:
                raise CliCellError(f"tool result for {tid} differs between stream and server")
