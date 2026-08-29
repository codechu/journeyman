#!/usr/bin/env python3
"""The CLI surface: the mark, the flags, and help that cannot rot.

Each of these is here because the thing it checks was wrong or missing in
a shipped release: the banner box was one character wider than its border
in every version, `--version` did not exist at all, there was no way to
turn the chrome off, and four flags carried no help text.
"""
import contextlib
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from journeyman.banner import banner  # noqa: E402
from journeyman.__main__ import main  # noqa: E402


class TestBanner(unittest.TestCase):
    def test_box_is_square_at_any_version(self):
        for v in ("0.2.0", "0.10.12", "1.0.0-rc1", "12.34.56"):
            lines = banner(v).split("\n")
            widths = {len(l) for l in lines}
            self.assertEqual(len(widths), 1,
                             f"banner box is ragged at v{v}: {sorted(widths)}")

    def test_it_carries_the_version_it_was_given(self):
        self.assertIn("v9.9.9", banner("9.9.9"))


class TestFlags(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as e:
                main(argv)
        return e.exception.code, out.getvalue() + err.getvalue()

    def test_version_flag_answers_without_a_subcommand(self):
        code, text = self._run(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("journeyman", text)

    def test_quiet_is_accepted_by_the_long_commands(self):
        for cmd in ("run", "qualify"):
            code, text = self._run([cmd, "--help"])
            self.assertEqual(code, 0)
            self.assertIn("--quiet", text, f"{cmd} has no --quiet")


class TestHelpDoesNotRot(unittest.TestCase):
    """Every optional flag explains itself.

    A flag with no help is a flag only its author can use, and argparse
    prints the blank line without complaint — nothing fails when someone
    adds one. This is what fails.
    """

    def test_every_flag_has_help(self):
        import argparse
        parsers = []

        real = argparse.ArgumentParser.parse_args

        def capture(self, *a, **k):
            parsers.append(self)
            raise SystemExit(0)

        argparse.ArgumentParser.parse_args = capture
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.suppress(SystemExit):
                    main(["--version"])
        finally:
            argparse.ArgumentParser.parse_args = real

        self.assertTrue(parsers, "could not reach the parser")
        naked = []
        for p in parsers:
            for act in p._actions:
                if isinstance(act, argparse._SubParsersAction):
                    for name, sp in act.choices.items():
                        for sact in sp._actions:
                            if sact.dest in ("help", "version"):
                                continue
                            if not sact.help:
                                naked.append(f"{name} {sact.dest}")
                elif act.dest not in ("help", "version") and not act.help:
                    naked.append(act.dest)
        self.assertEqual(naked, [], f"flags with no help: {naked}")


if __name__ == "__main__":
    unittest.main()
