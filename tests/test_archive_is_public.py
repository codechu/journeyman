"""Nothing new under runs-archive/ may name the maintainer's machine.

The report gate (test_public_label.py) folds the judge label where a report
is written. It did not cover exam records: on 2026-11-12 three of them
shipped a LAN address. This test reads the archive itself — every file,
compressed cell records included — for a private host or a home path.

The files in FOUNDING shipped before this gate. They stay as they are (they
are evidence, and history is not rewritten); the list may only shrink.
"""
import os
import re
import subprocess
import unittest

from journeyman.report import PRIVATE_HOST

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(ROOT, "runs-archive")
HOME_PATH = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/")
FOUNDING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive_founding.txt")


def _text(path):
    if path.endswith(".zst"):
        return subprocess.run(["zstd", "-dc", path], capture_output=True, check=True).stdout.decode("utf-8", "replace")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def leaking():
    out = []
    for d, _, files in os.walk(ARCHIVE):
        for name in files:
            p = os.path.join(d, name)
            t = _text(p)
            if PRIVATE_HOST.search(t) or HOME_PATH.search(t):
                out.append(os.path.relpath(p, ROOT))
    return sorted(out)


class ArchiveIsPublic(unittest.TestCase):
    def test_no_new_file_names_a_private_host_or_home_path(self):
        founding = set(open(FOUNDING).read().split())
        new = [p for p in leaking() if p not in founding]
        self.assertEqual(new, [], "fold these with report.public_label / tools/archive_cells.py")

    def test_founding_list_only_names_files_that_still_leak(self):
        # a file that was fixed or removed must leave the list: it may only shrink
        founding = set(open(FOUNDING).read().split())
        self.assertEqual(sorted(founding - set(leaking())), [])

    def test_the_gate_sees_a_leak(self):
        self.assertTrue(PRIVATE_HOST.search('"judge_endpoint": "http://192.168.0.14:4567/v1"'))
        self.assertTrue(HOME_PATH.search("re-judged from /home/someone/runs/x"))
        self.assertFalse(PRIVATE_HOST.search("https://openrouter.ai/api/v1"))


if __name__ == "__main__":
    unittest.main()
