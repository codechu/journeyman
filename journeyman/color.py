"""Terminal colour — on only when it is safe and wanted.

Colour is emitted only when stdout is a real TTY and NO_COLOR is unset
(the honoured convention). Piped output, CI logs and events.jsonl stay
plain, so nothing downstream ever parses escape codes. Kept tiny and
dependency-free on purpose.
"""
import os
import sys

_ON = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None \
    and os.environ.get("TERM") != "dumb"

_CODES = {"green": "32", "red": "31", "amber": "33", "dim": "90"}


def paint(text, colour):
    if not _ON or colour not in _CODES:
        return text
    return f"\033[{_CODES[colour]}m{text}\033[0m"
