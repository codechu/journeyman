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
