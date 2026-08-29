"""The product mark the tool prints before a long run.

The box used to be four hand-written string literals. They drifted: the
content line was one character wider than its borders, so the right edge
did not line up, and it had been that way in every release — nobody had
looked at the first thing a user sees. Building it from its content means
the shape cannot drift, and a test can hold it to that.
"""
NAME = "JOURNEYMAN"
RIGHT = "process-quality bench"
TAGLINE = "measures how agents work — and how they fail"
PAD = 2


def banner(version):
    """The four box lines, all of equal display width."""
    left = f"{NAME}  v{version}"
    width = max(len(left) + 1 + len(RIGHT), len(TAGLINE))
    inner = width + 2 * PAD
    gap = width - len(left) - len(RIGHT)
    space = " " * PAD
    return "\n".join([
        "┌" + "─" * inner + "┐",
        "│" + space + left + " " * gap + RIGHT + space + "│",
        "│" + space + TAGLINE + " " * (width - len(TAGLINE)) + space + "│",
        "└" + "─" * inner + "┘",
    ])
