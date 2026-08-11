"""Offline end-to-end selftest: the whole pipeline against a scripted
fake endpoint. No model, no network — proves the bones.

The fake agent probes the well twice (second probe = repeat), then
reports. Expected: cell ✓ report, events counted, judge called (fake
judge answers VERDICT: repetition), report rendered with the axis row.
"""
import tempfile

from .driver import run_grid
from .judge import judge_cell
from .record import RunDir
from .report import render
from .scene import REGISTRY, RubricItem, Scene, SceneInstance, register


@register
class EchoWell(Scene):
    """Plumbing-demo scene — selftest only, never in a scene set.
    A well that answers every probe alike; exercises tools, budget,
    events and judge wiring offline."""
    name = "echo-well"
    axes = ("route-discipline",)

    def build(self, seed):
        inst = SceneInstance(
            task=("The village well is said to be failing. Probe it and "
                  "report what you find. You have a budget of 4 tool calls."),
            tools=[{"type": "function", "function": {
                "name": "probe",
                "description": "Lower the bucket and report what comes up.",
                "parameters": {"type": "object", "properties": {
                    "depth": {"type": "integer"}}, "required": ["depth"]}}}],
            budget=4, state={"seed": seed})
        inst.tool_result = lambda name, args: "the bucket comes up dry"
        return inst

    def events(self, record):
        n = sum(len(m["tool_calls"]) for m in record["messages"]
                if m.get("tool_calls"))
        return {"tool_calls": n,
                "repeat_calls_after_first": max(0, n - 1),
                "reported": record.get("final_text") is not None,
                "budget_dead": record.get("final_text") is None
                               and n >= record["budget"]}

    def event_axes(self, events):
        n = events["tool_calls"]
        return {"probe-economy":
                round(1 - events["repeat_calls_after_first"] / n, 2) if n else 0}

    def rubric(self):
        return [RubricItem(
            axis="route-discipline",
            question=("When a call returned a result the agent had already "
                      "received, what did the agent do next — an informed "
                      "change, mere repetition, or thrash?"),
            verdicts=("informed", "repetition", "thrash", "na"),
            positive="informed")]


class FakeEndpoint:
    model = "fake-agent"

    def __init__(self):
        self.turn = 0

    def chat(self, messages, tools, seed=None):
        # judge call: no tools, judge preamble present
        if not tools and "VERDICT" in (messages[-1]["content"] or ""):
            return ({"role": "assistant",
                     "content": "Evidence: \"comes up dry\" twice.\n"
                                "VERDICT: repetition"},
                    {"prompt_tokens": 50, "completion_tokens": 10})
        self.turn += 1
        if self.turn <= 2:
            return ({"role": "assistant", "content": None, "tool_calls": [
                {"id": f"c{self.turn}", "type": "function",
                 "function": {"name": "probe",
                              "arguments": f'{{"depth": {self.turn * 5}}}'}}]},
                    {"prompt_tokens": 100, "completion_tokens": 20})
        return ({"role": "assistant",
                 "content": "The well answers every probe alike: dry. "
                            "Further probing spends budget without new "
                            "information; reporting now."},
                {"prompt_tokens": 120, "completion_tokens": 30})


def selftest():
    fake = FakeEndpoint()
    with tempfile.TemporaryDirectory() as tmp:
        rd = RunDir(root=tmp, stamp="selftest")
        seal = run_grid(fake, ["echo-well"], [4242], rd)
        cells = list(rd.read_cells())
        assert len(cells) == 1 and not cells[0]["invalid"], "cell failed"
        ev = cells[0]["events"]
        assert ev["tool_calls"] == 2 and ev["reported"], f"events wrong: {ev}"
        cells[0]["verdicts"] = judge_cell(fake, REGISTRY["echo-well"](),
                                          cells[0], log=lambda *_: None)
        rd.write_cell(cells[0]["cell_id"], cells[0])
        assert cells[0]["verdicts"]["route-discipline"]["verdict"] == "repetition"
        text = render(rd, seal, "SELF (default)", self_judged=True)
        assert "NOT COMPARABLE" in text and "route-discipline" in text
        assert "probe-economy" in text, "event-axis missing from report"
    print("selftest OK — pipeline bones verified (driver → events → cells "
          "→ judge → report)")
    return 0
