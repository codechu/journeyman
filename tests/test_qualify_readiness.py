"""A judge that is still loading is absent, not broken.

2026-09-01: a 27B judge was still mmap-ing its weights when the exam
opened. Three attempts inside fifteen seconds spent themselves on case 1
of 82, and an eighty-two-case exam died with a stack trace on a server
that was working correctly ninety seconds later.
"""
import unittest
from unittest import mock

from journeyman import qualify as q


class Endpoint:
    url = "http://localhost:4567/v1"
    api_key = None

    def chat(self, messages, tools, seed=None):
        return {"content": "VERDICT: na"}, {}


class TestReadiness(unittest.TestCase):
    def test_waits_out_a_loading_server_then_proceeds(self):
        calls = {"n": 0}

        def flaky(*a, **k):
            calls["n"] += 1
            if calls["n"] < 3:
                raise OSError("[Errno 111] Connection refused")
            return ["a-model"]

        with mock.patch("journeyman.driver.list_models", flaky), \
             mock.patch("time.sleep"):
            self.assertTrue(q.await_judge(Endpoint(), log=lambda *a: None))
        self.assertEqual(calls["n"], 3)   # it kept knocking, then went in

    def test_an_absent_endpoint_still_fails_but_with_a_sentence(self):
        def refused(*a, **k):
            raise OSError("[Errno 111] Connection refused")

        with mock.patch("journeyman.driver.list_models", refused), \
             mock.patch("time.sleep"), \
             mock.patch("time.time", side_effect=[0, 0, 1, 999, 999, 999]):
            with self.assertRaises(RuntimeError) as e:
                q.await_judge(Endpoint(), log=lambda *a: None, timeout=300)
        self.assertIn("unusable", str(e.exception))

    def test_a_broken_endpoint_is_not_waited_out(self):
        """Only not-ready is patient. A 401 is answered at once — waiting
        five minutes for a wrong key helps nobody."""
        def unauthorized(*a, **k):
            raise OSError("HTTP Error 401: Unauthorized")

        with mock.patch("journeyman.driver.list_models", unauthorized), \
             mock.patch("time.sleep"):
            with self.assertRaises(RuntimeError):
                q.await_judge(Endpoint(), log=lambda *a: None)

    def test_an_in_process_judge_has_nothing_to_knock_on(self):
        class NoUrl:
            def chat(self, *a, **k):
                return {"content": ""}, {}
        self.assertTrue(q.await_judge(NoUrl(), log=lambda *a: None))


if __name__ == "__main__":
    unittest.main()
