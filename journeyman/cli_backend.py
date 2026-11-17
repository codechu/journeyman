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
import os
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
            self._settings = {"cli": version, "flags": " ".join(self._flags()),
                              "effort": "cli default (not set)"}
        return self._settings

    def _flags(self):
        return ["-p", "--safe-mode", "--exclude-dynamic-system-prompt-sections",
                "--model", self.model, "--system-prompt", "", "--tools", "",
                "--no-session-persistence", "--strict-mcp-config",
                "--output-format", "json"]

    def chat(self, messages, tools, seed=None):
        """Ask the judge one question.

        Parameters
        ----------
        messages : list[dict]
            Only ``{"role": "user", "content": ...}`` entries allowed.
        tools : list
            Must be empty (CLI backend is judge-only).
        seed : ignored

        Returns
        -------
        tuple[dict, dict]
            (message_dict, meta_dict) mirroring the HTTP endpoint shape.
        """
        if tools:
            raise ValueError(
                "CLI backend is judge-only: tools are not supported"
            )
        for msg in messages:
            if msg.get("role") != "user":
                raise ValueError(
                    f"CLI backend accepts only 'user' messages, "
                    f"got {msg.get('role')!r}"
                )

        prompt = "\n\n".join(m["content"] for m in messages)

        cmd = [self.exe, *self._flags()]

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

        return (
            {"role": "assistant", "content": d.get("result") or ""},
            {"cost_usd": d.get("total_cost_usd"), "models": used},
        )
