"""Tests for the CLI judge backend.

The real Claude Code tool is never called.  Instead a small fake
executable (a Python script with a shebang) is written into a
temporary directory and its path is passed as ``exe``.
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from journeyman import scenes  # noqa: F401 — rubric index reads the registry
from journeyman.cli_backend import CliEndpoint
from journeyman import qualify as q

# The fake executable script template.
_FAKE_SCRIPT = '''\
#!/usr/bin/env python{pyver}
import json, os, sys

fake_mode = os.environ.get("FAKE_MODE", "ok")
log_path = os.environ.get("FAKE_LOG", "")
argv = sys.argv[1:]
if argv == ["--version"]:
    print("9.9.9 (Fake Code)")
    sys.exit(0)
cwd = os.getcwd()
if log_path:
    with open(log_path, "w") as lf:
        json.dump({{"argv": argv, "cwd": cwd}}, lf)

if fake_mode == "ok":
    print(json.dumps({{
        "is_error": False,
        "terminal_reason": "completed",
        "result": "VERDICT: pass",
        "modelUsage": {{"claude-haiku-5-5": {{"input_tokens": 100, "output_tokens": 50}}}},
        "total_cost_usd": 0.001
    }}))
elif fake_mode == "error":
    print(json.dumps({{
        "is_error": True,
        "result": "Not logged in"
    }}))
elif fake_mode == "drift":
    print(json.dumps({{
        "is_error": False,
        "terminal_reason": "completed",
        "result": "VERDICT: pass",
        "modelUsage": {{"claude-fable-5-1": {{"input_tokens": 100, "output_tokens": 50}}}},
        "total_cost_usd": 0.001
    }}))
elif fake_mode == "garbage":
    print("no json here")
elif fake_mode == "max_turns":
    print(json.dumps({{
        "is_error": False,
        "terminal_reason": "max_turns",
        "result": "stopped"
    }}))
else:
    print(json.dumps({{
        "is_error": False,
        "terminal_reason": "completed",
        "result": "VERDICT: pass",
        "modelUsage": {{"claude-haiku-5-5": {{"input_tokens": 100, "output_tokens": 50}}}},
        "total_cost_usd": 0.001
    }}))
'''


def _make_fake_exe(tmpdir):
    """Write a fake Claude Code executable and return its path."""
    path = os.path.join(tmpdir, "fake_claude")
    pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
    with open(path, "w") as fh:
        fh.write(_FAKE_SCRIPT.format(pyver=pyver))
    os.chmod(path, 0o755)
    return path


class TestCliEndpoint(unittest.TestCase):
    """Tests (i)-(vi-d) from the task spec."""

    def _run_ok(self, asked_model="claude-haiku-5-5"):
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        log_path = os.path.join(tmpdir, "log.json")
        os.environ["FAKE_MODE"] = "ok"
        os.environ["FAKE_LOG"] = log_path
        ep = CliEndpoint("claude", asked_model, exe=exe)
        msg, meta = ep.chat([{"role": "user", "content": "hello"}], tools=[])
        return msg, meta, log_path

    def test_ok_returns_content_and_meta(self):
        """(i) ok => chat returns content "VERDICT: pass" and meta models
        contains the asked model."""
        msg, meta, log_path = self._run_ok()
        self.assertEqual(msg["content"], "VERDICT: pass")
        self.assertIn("claude-haiku-5-5", meta["models"])

    def test_argv_and_cwd_logged(self):
        """(ii) the logged argv contains, in order of appearance,
        "-p", "--safe-mode", "--model", the model, "--system-prompt",
        "", "--tools", "" and "--output-format", "json"; and the logged
        working directory is not the test's own cwd."""
        _, _, log_path = self._run_ok()
        with open(log_path) as f:
            logged = json.load(f)
        argv = logged["argv"]
        expected = ["-p", "--safe-mode", "--model", "claude-haiku-5-5",
                     "--system-prompt", "", "--tools", "",
                     "--output-format", "json"]
        # Find each expected item after the previous one (handles duplicates)
        prev_idx = -1
        for item in expected:
            idx = argv.index(item, prev_idx + 1)
            self.assertGreater(idx, prev_idx,
                               f"{item!r} not found after position {prev_idx}")
            prev_idx = idx
        self.assertNotEqual(logged["cwd"], os.getcwd())

    def test_error_mode_raises(self):
        """(iii) error => RuntimeError mentioning "Not logged in"."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        os.environ["FAKE_MODE"] = "error"
        ep = CliEndpoint("claude", "claude-haiku-5-5", exe=exe)
        with self.assertRaises(RuntimeError) as ctx:
            ep.chat([{"role": "user", "content": "hello"}], tools=[])
        self.assertIn("Not logged in", str(ctx.exception))

    def test_drift_mode_raises(self):
        """(iv) drift => RuntimeError mentioning "asked for claude-fable-5-2"."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        os.environ["FAKE_MODE"] = "drift"
        ep = CliEndpoint("claude", "claude-fable-5-2", exe=exe)
        with self.assertRaises(RuntimeError) as ctx:
            ep.chat([{"role": "user", "content": "hello"}], tools=[])
        self.assertIn("asked for claude-fable-5-2", str(ctx.exception))

    def test_tools_raises_value_error(self):
        """(v) tools=[{"x": 1}] => ValueError."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        ep = CliEndpoint("claude", "claude-haiku-5-5", exe=exe)
        with self.assertRaises(ValueError) as ctx:
            ep.chat([{"role": "user", "content": "hello"}], tools=[{"x": 1}])
        self.assertIn("tools are not supported", str(ctx.exception))

    def test_bad_kind_raises_value_error(self):
        """(vi) kind "codex" => ValueError."""
        with self.assertRaises(ValueError):
            CliEndpoint("codex", "some-model")

    def test_system_message_raises_value_error(self):
        """(vi-b) a message with role "system" => ValueError."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        ep = CliEndpoint("claude", "claude-haiku-5-5", exe=exe)
        with self.assertRaises(ValueError) as ctx:
            ep.chat([{"role": "system", "content": "hello"}], tools=[])
        self.assertIn("only 'user' messages", str(ctx.exception))

    def test_garbage_output_raises_runtime_error(self):
        """(vi-c) garbage => RuntimeError (not ValueError)."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        os.environ["FAKE_MODE"] = "garbage"
        ep = CliEndpoint("claude", "claude-haiku-5-5", exe=exe)
        with self.assertRaises(RuntimeError) as ctx:
            ep.chat([{"role": "user", "content": "hello"}], tools=[])
        self.assertNotIsInstance(ctx.exception, ValueError)

    def test_max_turns_raises_runtime_error(self):
        """(vi-d) a mode with is_error false but terminal_reason "max_turns"
        => RuntimeError mentioning "cli judge failed"."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        os.environ["FAKE_MODE"] = "max_turns"
        ep = CliEndpoint("claude", "claude-haiku-5-5", exe=exe)
        with self.assertRaises(RuntimeError) as ctx:
            ep.chat([{"role": "user", "content": "hello"}], tools=[])
        self.assertIn("cli judge failed", str(ctx.exception))


class TestViaStamping(unittest.TestCase):
    """Test (vii): qualify with via-stamped endpoint."""

    def test_with_via_stamps_badge_and_result(self):
        """with via => result["qualified"] is True, badge ends with
        "(via cli:claude --safe-mode)", judge_via == "cli:claude --safe-mode"."""
        cal = {"set": "t", "cases": [
            {"axis": "empty-measure",
             "true_label": "noticed",
             "record": "test record for calibration"}
        ]}

        class FakeEndpoint:
            url = None
            api_key = None
            via = "cli:claude --safe-mode"

            def chat(self, messages, tools, seed=None):
                return {"role": "assistant",
                        "content": "VERDICT: noticed"}, {}

        fake = FakeEndpoint()
        with mock.patch("journeyman.driver.list_models",
                        lambda *a, **k: ["claude-haiku-5-5"]):
            result = q.qualify(fake, cal=cal, log=lambda *a: None,
                               repeats=1)
        self.assertTrue(result["qualified"])
        self.assertEqual(result["badge"],
                         "QUALIFIED (via cli:claude --safe-mode)")
        self.assertEqual(result["judge_via"],
                         "cli:claude --safe-mode")

    def test_without_via_no_stamp(self):
        """without via => "judge_via" not in result, badge == "QUALIFIED"."""
        cal = {"set": "t", "cases": [
            {"axis": "empty-measure",
             "true_label": "noticed",
             "record": "test record for calibration"}
        ]}

        class FakeEndpoint:
            url = None
            api_key = None
            # no "via" attribute

            def chat(self, messages, tools, seed=None):
                return {"role": "assistant",
                        "content": "VERDICT: noticed"}, {}

        fake = FakeEndpoint()
        with mock.patch("journeyman.driver.list_models",
                        lambda *a, **k: ["m"]):
            result = q.qualify(fake, cal=cal, log=lambda *a: None,
                               repeats=1)
        self.assertTrue(result["qualified"])
        self.assertEqual(result["badge"], "QUALIFIED")
        self.assertNotIn("judge_via", result)


class TestMainWiring(unittest.TestCase):
    """Test (viii): __main__ wiring."""

    def test_cli_judge_builds_cli_endpoint(self):
        """--judge cli:claude --judge-model m => endpoint is CliEndpoint
        with model "m"."""
        from journeyman import __main__ as main_mod
        from journeyman.cli_backend import CliEndpoint
        from journeyman import qualify as qmod

        with mock.patch.object(qmod, "main") as mock_main:
            mock_main.return_value = 0
            with self.assertRaises(SystemExit):
                main_mod.main(["qualify", "--judge", "cli:claude",
                               "--judge-model", "m", "-q"])
        call_args = mock_main.call_args
        endpoint = call_args[0][1]
        self.assertIsInstance(endpoint, CliEndpoint)
        self.assertEqual(endpoint.model, "m")

    def test_http_judge_builds_http_endpoint(self):
        """--judge http://localhost:1/v1 => endpoint is not CliEndpoint."""
        from journeyman import __main__ as main_mod
        from journeyman.cli_backend import CliEndpoint
        from journeyman import qualify as qmod

        with mock.patch.object(qmod, "main") as mock_main:
            mock_main.return_value = 0
            with self.assertRaises(SystemExit):
                main_mod.main(["qualify", "--judge",
                               "http://localhost:1/v1",
                               "--judge-model", "m", "-q"])
        call_args = mock_main.call_args
        endpoint = call_args[0][1]
        self.assertNotIsInstance(endpoint, CliEndpoint)


if __name__ == "__main__":
    unittest.main()


class TestCliSettings(unittest.TestCase):
    def test_settings_name_version_flags_and_default_effort(self):
        """The record says what sat the exam: CLI version, flags, effort left
        at the CLI default."""
        tmpdir = tempfile.mkdtemp()
        exe = _make_fake_exe(tmpdir)
        st = CliEndpoint("claude", "m", exe=exe).settings
        self.assertEqual(st["cli"], "9.9.9 (Fake Code)")
        self.assertIn("--safe-mode", st["flags"])
        self.assertEqual(st["effort"], "cli default (not set)")

