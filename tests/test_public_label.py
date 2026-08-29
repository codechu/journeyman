"""A published seal must name the judge, not the maintainer's machine.

Founding case: 49 files in runs-archive/ shipped with `http://192.168.0.14:4567`
and `/home/onur/journeyman-runs/...` inside the judge string (v0.0.9,
2026-08-24). Those archives stay as they are — they are evidence — and this
gate keeps it from happening again.
"""
import unittest

from journeyman.report import public_label


class PublicLabel(unittest.TestCase):
    def test_private_address_and_home_path_are_folded(self):
        got = public_label(
            "qwen36 @ http://192.168.0.14:4567 "
            "(re-judged from /home/onur/journeyman-runs/leaderboard-1/x/2026-08-23/)")
        self.assertNotIn("192.168", got)
        self.assertNotIn("/home/onur", got)
        self.assertEqual(got, "qwen36 @ self-hosted (re-judged from <path>)")

    def test_loopback_and_windows_path(self):
        self.assertEqual(public_label("qwen36 @ http://127.0.0.1:8080/v1"),
                         "qwen36 @ self-hosted")
        self.assertNotIn("onur", public_label(r"judge at C:\Users\onur\runs\x"))

    def test_public_endpoints_survive_untouched(self):
        for label in ("https://openrouter.ai/api",
                      "https://openrouter.ai/api/v1 (z-ai/glm-5.2)",
                      "SELF (default)"):
            self.assertEqual(public_label(label), label)


if __name__ == "__main__":
    unittest.main()
