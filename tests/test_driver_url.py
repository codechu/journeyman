"""An endpoint given with a suffix must reach the same place."""
from journeyman.driver import chat_url


def test_bare_host_gets_the_full_path():
    assert chat_url("http://h:4567") == "http://h:4567/v1/chat/completions"
    assert chat_url("http://h:4567/") == "http://h:4567/v1/chat/completions"


def test_v1_suffix_is_not_doubled():
    """The silent failure: /v1 passed the model listing and 404'd every call,
    so the run completed and reported nothing."""
    assert chat_url("https://openrouter.ai/api/v1") == \
        "https://openrouter.ai/api/v1/chat/completions"


def test_full_path_is_left_alone():
    assert chat_url("http://h/v1/chat/completions") == "http://h/v1/chat/completions"


def test_judging_is_metered():
    """The agent side was always counted and the paid side was not, which is
    backwards: the agent may be free and local, the judge is what is charged."""
    from journeyman.judge import judge_cell
    from journeyman.scenes import REGISTRY

    class FakeJudge:
        def chat(self, messages, tools, seed=None):
            return ({"content": "VERDICT: noticed"},
                    {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0004})

    meter = {}
    cell = {"messages": [{"role": "assistant", "content": "x"}], "scene": "echo-well"}
    judge_cell(FakeJudge(), REGISTRY["echo-well"](), cell, log=lambda *a: None,
               meter=meter)
    assert meter["calls"] >= 1
    assert meter["tokens_in"] >= 100 and meter["tokens_out"] >= 20
    assert meter["cost"] > 0
