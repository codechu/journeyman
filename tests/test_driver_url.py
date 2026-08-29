"""An endpoint given with a suffix must reach the same place.

Written as unittest.TestCase on purpose: CI runs `python -m unittest discover`,
which collects TestCase classes only — as plain functions these four tests were
present in the tree and executed by nothing, and one of them had been broken by
a rename (`journeyman.scenes.REGISTRY` -> `journeyman.scene.REGISTRY`) and a
retired scene without anyone noticing.
"""
import unittest

from journeyman.driver import chat_url
import journeyman.scenes  # noqa: F401 — scenes register themselves on import
from journeyman.judge import judge_cell
from journeyman.scene import REGISTRY


class ChatUrl(unittest.TestCase):
    def test_bare_host_gets_the_full_path(self):
        self.assertEqual(chat_url("http://h:4567"), "http://h:4567/v1/chat/completions")
        self.assertEqual(chat_url("http://h:4567/"), "http://h:4567/v1/chat/completions")

    def test_v1_suffix_is_not_doubled(self):
        """The silent failure: /v1 passed the model listing and 404'd every call,
        so the run completed and reported nothing."""
        self.assertEqual(chat_url("https://openrouter.ai/api/v1"),
                         "https://openrouter.ai/api/v1/chat/completions")

    def test_full_path_is_left_alone(self):
        self.assertEqual(chat_url("http://h/v1/chat/completions"),
                         "http://h/v1/chat/completions")


class JudgeMetering(unittest.TestCase):
    """The agent side was always counted and the paid side was not, which is
    backwards: the agent may be free and local, the judge is what is charged."""

    def test_judging_is_metered(self):
        name = "finished-cart"
        scene = REGISTRY[name]()

        class FakeJudge:
            def chat(self, messages, tools, seed=None):
                return ({"content": "VERDICT: noticed"},
                        {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0004})

        meter = {}
        # shape: journeyman/driver.py run_grid() — a cell record carries cell_id
        record = {"cell_id": f"{name}_s4242", "scene": name,
                  "messages": [{"role": "assistant", "content": "x"}]}
        judge_cell(FakeJudge(), scene, record, log=lambda *a: None, meter=meter)
        self.assertGreaterEqual(meter["calls"], 1)
        self.assertGreaterEqual(meter["tokens_in"], 100)
        self.assertGreaterEqual(meter["tokens_out"], 20)
        self.assertGreater(meter["cost"], 0)


if __name__ == "__main__":
    unittest.main()
