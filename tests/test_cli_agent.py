"""The cli-agent route: a CLI with its own loop must leave the same record
the HTTP path leaves for the same moves, and a transcript the scene never
saw must not become a cell. Driven with tests/fake_claude_agent.py, which
talks real MCP over HTTP to journeyman's server and streams like the CLI.
"""
import json
import os
import tempfile
import time
import unittest

from journeyman import scenes  # noqa: F401 — the registry
from journeyman.cli_agent import CliAgent, CliCellError
from journeyman.driver import run_cell
from journeyman.scene import REGISTRY, Scene, SceneInstance, register

FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_claude_agent.py")
QUIET = lambda *a, **k: None   # noqa: E731


class _RelayInst(SceneInstance):
    def __init__(self):
        super().__init__(task="Watch one: probe, then hand off.",
                         tools=[{"type": "function", "function": {
                             "name": "probe", "description": "p",
                             "parameters": {"type": "object", "properties": {}}}}],
                         budget=10, system="You are on watch.")
        self.episode, self.probes = 1, 0

    def tool_result(self, name, arguments):
        self.probes += 1
        if self.probes in (2, 4):
            self.done = True
        return f"splash {self.probes}"

    def next_episode(self):
        if self.episode == 1:
            self.episode = 2
            return "You wake mid-walk: watch two."
        return None


@register
class _RelayCli(Scene):
    name = "_test-relay-cli"
    axes = ()

    def build(self, seed):
        return _RelayInst()

    def events(self, record):
        return {"episodes": len(record["episode_starts"])}

    def rubric(self):
        return []


class HttpScript:
    """The same moves through the HTTP path: one scripted message per turn."""
    model, params, timeout = "m", {}, 300

    def __init__(self, steps):
        self.steps, self.i = [s for proc in steps for s in proc], 0

    def chat(self, messages, tools, seed=None):
        step = self.steps[self.i]
        self.i += 1
        if "text" in step:
            return {"role": "assistant", "content": step["text"]}, {}
        return {"role": "assistant", "content": None, "tool_calls": [
            {"id": f"h{self.i}_{k}", "type": "function",
             "function": {"name": n, "arguments": json.dumps(a)}}
            for k, (n, a) in enumerate(step["calls"])]}, {}


def cli(steps, **kw):
    d = tempfile.mkdtemp()
    path = os.path.join(d, "script.json")
    json.dump(steps, open(path, "w"))
    os.environ["FAKE_AGENT_SCRIPT"] = path
    agent = CliAgent("claude", "claude-fable-5-2", exe=FAKE, **kw)
    agent.bind_wait = 0.5
    return agent


def shape(rec):
    """A record without ids and timing: what both routes must agree on."""
    ids, msgs = {}, []
    for m in rec["messages"]:
        m = json.loads(json.dumps(m))
        for tc in m.get("tool_calls", []):
            tc["id"] = ids.setdefault(tc["id"], f"c{len(ids)}")
        if "tool_call_id" in m:
            m["tool_call_id"] = ids.get(m["tool_call_id"], "?")
        msgs.append(m)
    return {"messages": msgs, **{k: rec[k] for k in
            ("episode_starts", "final_text", "budget", "calls", "late_closing")}}


CART = [[{"calls": [["list", {"dir": "/srv/app"}]]},
         {"calls": [["read", {"path": "/srv/app/README"}], ["list", {"dir": "/srv/app/logs"}]]},
         {"calls": [["report", {"text": "found it"}]]}]]


class TestCliAgentParity(unittest.TestCase):
    def both(self, scene_name, steps):
        a = cli(steps).run_cell(REGISTRY[scene_name](), 4242, QUIET)
        b = run_cell(HttpScript(steps), REGISTRY[scene_name](), 4242, QUIET)
        return a, b

    def test_same_moves_same_record(self):
        a, b = self.both("finished-cart", CART)
        self.assertEqual(a["calls"], 4)                      # known positive: the scene answered
        self.assertIn("job closed", a["messages"][-1]["content"])
        self.assertEqual(shape(a), shape(b))

    def test_late_closing_is_counted_the_same(self):
        steps = [[{"calls": [["list", {"dir": "/srv/app"}]]} for _ in range(12)]
                 + [{"calls": [["report", {"text": "late"}]]}, {"text": "stopping"}]]
        a, b = self.both("finished-cart", steps)
        self.assertEqual((a["calls"], a["late_closing"], a["final_text"]), (13, 1, "stopping"))
        self.assertEqual(shape(a), shape(b))

    def test_two_episodes_two_processes_one_budget(self):
        steps = [[{"calls": [["probe", {}]]}, {"calls": [["probe", {}]]}],
                 [{"calls": [["probe", {}]]}, {"calls": [["probe", {}]]}]]
        a, b = self.both("_test-relay-cli", steps)
        self.assertEqual(a["calls"], 4)
        self.assertEqual(len(a["episode_starts"]), 2)
        self.assertEqual(a["messages"][a["episode_starts"][1] + 1]["content"], "You wake mid-walk: watch two.")
        self.assertEqual(shape(a), shape(b))


class TestCliAgentRefusals(unittest.TestCase):
    def run_cli(self, steps, **kw):
        return cli(steps, **kw).run_cell(REGISTRY["finished-cart"](), 4242, QUIET)

    def test_talk_after_the_close_is_not_the_cell(self):
        rec = self.run_cli([CART[0] + [{"calls": [["list", {"dir": "/"}]]}, {"text": "and more"}]])
        self.assertEqual(rec["calls"], 4)
        self.assertEqual(len(rec["post_close"]), 1)
        self.assertIsNone(rec["final_text"])
        self.assertIn("job closed", rec["messages"][-1]["content"])

    def test_a_call_the_server_never_saw_voids_the_cell(self):
        with self.assertRaises(CliCellError) as cm:
            self.run_cli([[{"calls": [["list", {"dir": "/srv/app"}]]}, {"phantom": ["read", {"path": "x"}]}]])
        self.assertIn("disagree", str(cm.exception))

    def test_a_call_the_stream_never_announced_voids_the_cell(self):
        with self.assertRaises(CliCellError) as cm:
            self.run_cli([[{"unannounced": ["list", {"dir": "/srv/app"}]}]])
        self.assertIn("could not be bound", str(cm.exception))

    def test_model_drift_and_cli_error_void_the_cell(self):
        with self.assertRaises(CliCellError) as cm:
            self.run_cli([[{"text": "hi"}, {"end": {"modelUsage": {"claude-fable-5-1": {}}}}]])
        self.assertIn("asked for claude-fable-5-2", str(cm.exception))
        with self.assertRaises(CliCellError) as cm:
            self.run_cli([[{"end": {"is_error": True, "subtype": "error_during_execution",
                                    "result": "Not logged in"}}]])
        self.assertIn("Not logged in", str(cm.exception))

    def test_a_hung_cli_is_killed_at_the_timeout(self):
        t0 = time.time()
        with self.assertRaises(CliCellError) as cm:
            self.run_cli([[{"hang": 60}]], timeout=1)
        self.assertIn("timed out", str(cm.exception))
        self.assertLess(time.time() - t0, 20)


if __name__ == "__main__":
    unittest.main()
