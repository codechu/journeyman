"""Claude Code CLI as judge.

The Claude Code command-line tool can sit the qualification exam in its
barest mode.  This module wraps that invocation so it looks like an
Endpoint to the rest of journeyman, while stamping the result so a CLI
badge is never read as an API badge.

The barest working call is::

    claude -p --safe-mode --exclude-dynamic-system-prompt-sections \
        --model <model> --system-prompt "" --tools "" \
        --no-session-persistence --strict-mcp-config \
        --output-format json

with the prompt on stdin.  It prints one JSON object on stdout (a
warning line may appear on stderr).
"""
import json
import subprocess
import tempfile


SUPPORTED_KINDS = ("claude",)


class CliEndpoint:
    """Wrap the Claude Code CLI as a judge endpoint.

    Parameters
    ----------
    kind : str
        Must be "claude" (otherwise ``ValueError``).
    model : str
        The full model id to ask for (e.g. ``claude-fable-5-2``).
        Aliases are not accepted because they may resolve to a
        different version that does not appear among the
        ``modelUsage`` keys.
    exe : str or None
        The executable to run; defaults to ``"claude"``.
    timeout : int
        Per-call timeout in seconds (default 600).
    """

    def __init__(self, kind, model, exe=None, timeout=600):
        if kind not in SUPPORTED_KINDS:
            raise ValueError(
                f"unsupported kind {kind!r}; supported: {SUPPORTED_KINDS}"
            )
        self.kind = kind
        self.model = model
        self.exe = exe or "claude"
        self.timeout = timeout
        self.url = None
        self.api_key = None
        self.via = "cli:claude --safe-mode"
        self._settings = None

    @property
    def settings(self):
        """What the judge ran under, for the record and the registry row.

        A badge is granted to a configuration, not to a model name: the CLI
        version and the flags are part of what sat the exam, and effort is
        left at the CLI's own default on purpose (measured as shipped, not
        tuned)."""
        if self._settings is None:
            try:
                out = subprocess.run([self.exe, "--version"], text=True,
                                     capture_output=True, timeout=30)
                version = (out.stdout.strip().splitlines() or ["unknown"])[0]
            except (OSError, subprocess.SubprocessError):
                version = "unknown"
            import hashlib
            self._settings = {"cli": version, "flags": " ".join(self._flags()),
                              "effort": "cli default (not set)", "seed": "not sent",
                              "tool_protocol_md5": hashlib.md5(TOOL_PROTOCOL.encode()).hexdigest()[:12]}
        return self._settings

    def _flags(self, system=""):
        return ["-p", "--safe-mode", "--exclude-dynamic-system-prompt-sections",
                "--model", self.model, "--system-prompt", system, "--tools", "",
                "--no-session-persistence", "--strict-mcp-config",
                "--output-format", "json"]

    def chat(self, messages, tools, seed=None):
        """One model turn through the CLI.

        A judge question (user messages only, no tools) goes in verbatim, as
        it always did. An agent turn (a system message, earlier turns, or
        tools) is rendered as text: the CLI is given no tools of its own, so
        each call is exactly one model turn, and journeyman's own driver runs
        the loop — the model is scored like any API model, through the same
        budget rules. Tool calls come back as trailing `CALL <name> <json>`
        lines (TOOL_PROTOCOL), parsed into the HTTP path's tool_calls shape.
        `seed` is not sent: the CLI takes no sampling seed.
        """
        agent_turn = bool(tools) or any(m.get("role") != "user" for m in messages)
        if not agent_turn:
            system, prompt = "", "\n\n".join(m["content"] for m in messages)
        else:
            system = "\n\n".join(m["content"] for m in messages
                                  if m.get("role") == "system" and m.get("content"))
            prompt = render_turn(messages, tools)
        d, used = self._run(system, prompt)
        if not agent_turn:
            return (
                {"role": "assistant", "content": d.get("result") or ""},
                {"cost_usd": d.get("total_cost_usd"), "models": used},
            )
        msg = parse_reply(d.get("result") or "", f"cli_{len(messages)}")
        if d.get("stop_reason") == "max_tokens":
            msg["finish_reason"] = "length"
        u = d.get("usage") or {}
        return msg, {"prompt_tokens": (u.get("input_tokens") or 0)
                     + (u.get("cache_read_input_tokens") or 0)
                     + (u.get("cache_creation_input_tokens") or 0),
                     "completion_tokens": u.get("output_tokens") or 0,
                     "cost_usd": d.get("total_cost_usd"), "models": used}

    def _run(self, system, prompt):
        cmd = [self.exe, *self._flags(system)]

        tmpdir = tempfile.mkdtemp()
        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"cli judge timed out after {self.timeout}s "
                f"(stderr: {(exc.stderr or '')[-300:]})"
            ) from exc
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

        stdout = proc.stdout
        i = stdout.find("{")
        if i < 0:
            raise RuntimeError(
                f"cli judge produced no JSON (return code "
                f"{proc.returncode}, stderr: {proc.stderr[-300:]})"
            )
        try:
            d = json.loads(stdout[i:])
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"cli judge output is not valid JSON "
                f"(return code {proc.returncode}, stderr: "
                f"{proc.stderr[-300:]})"
            ) from exc

        if d.get("is_error") or d.get("terminal_reason") != "completed":
            raise RuntimeError(
                "cli judge failed: " + str(d.get("result", ""))
            )

        used = list(d.get("modelUsage", {}).keys())
        if self.model not in used:
            raise RuntimeError(
                f"cli judge ran {used}, asked for {self.model} "
                f"(--judge-model must be a full model id such as "
                f"claude-fable-5-2, not an alias, because an alias "
                f"never appears among the modelUsage keys)"
            )

        return d, used


TOOL_PROTOCOL = """You act through tools. To call tools, end your reply with one or more lines, each exactly:
CALL <tool name> <arguments as a one-line JSON object>
Nothing may follow those lines. Each CALL line is one tool call; the results come back in the next message. To stop calling tools, reply without any CALL line.

Available tools:
"""


def render_turn(messages, tools):
    """The conversation so far + the tool protocol, as one prompt (stamped in the seal)."""
    lines = [TOOL_PROTOCOL.rstrip("\n")]
    for t in tools:
        fn = t["function"]
        lines.append(f"- {fn['name']}: {fn.get('description', '')}")
        lines.append(f"  arguments schema: {json.dumps(fn.get('parameters') or {}, sort_keys=True)}")
    lines.append("")
    lines.append("CONVERSATION SO FAR (oldest first):")
    names = {}
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role == "user":
            lines.append(f"[user] {m.get('content') or ''}")
        elif role == "assistant":
            if m.get("content"):
                lines.append(f"[assistant] {m['content']}")
            for tc in m.get("tool_calls") or []:
                fn = tc["function"]
                names[tc["id"]] = fn["name"]
                lines.append(f"[assistant called] {fn['name']} {fn.get('arguments') or '{}'}")
        elif role == "tool":
            lines.append(f"[result of {names.get(m.get('tool_call_id'), 'tool')}] {m.get('content') or ''}")
    lines.append("")
    lines.append("Write your next reply.")
    return "\n".join(lines)


def parse_reply(text, id_prefix):
    """Trailing `CALL <name> <json>` lines → tool_calls; the rest is the content.

    Arguments are passed on as the raw text the model wrote: malformed JSON
    reaches the scene the way it does on the HTTP path (driver.Ledger turns
    it into {"_unparsed": ...})."""
    lines = text.rstrip().split("\n")
    calls = []
    while lines and lines[-1].strip().startswith("CALL "):
        calls.insert(0, lines.pop().strip()[5:].strip())
    msg = {"role": "assistant"}
    content = "\n".join(lines).strip()
    msg["content"] = content or None
    if calls:
        msg["tool_calls"] = []
        for k, c in enumerate(calls):
            name, _, raw = c.partition(" ")
            msg["tool_calls"].append({"id": f"{id_prefix}_{k}", "type": "function",
                                      "function": {"name": name, "arguments": raw.strip() or "{}"}})
    return msg
