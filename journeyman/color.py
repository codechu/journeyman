"""Terminal colour — on only when it is safe and wanted.

Colour is emitted only when every gate agrees, so it can never turn
into escape-code garbage on a console that would not interpret it:

  * FORCE_COLOR (non-zero) forces it on; NO_COLOR forces it off.
  * stdout must be a real TTY (pipes, CI logs, events.jsonl stay plain).
  * TERM=dumb is honoured.
  * On Windows, ANSI is enabled only if we can turn on the console's
    virtual-terminal processing; if that fails (legacy cmd.exe), colour
    stays off rather than print raw escapes.

Tiny and dependency-free on purpose.
"""
import os
import sys


def _windows_vt_ok():
    """Try to enable ANSI on a Windows console. True on success."""
    try:
        import ctypes
        k = getattr(ctypes, "windll").kernel32   # windll exists on Windows only
        h = k.GetStdHandle(-11)               # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not k.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        return bool(k.SetConsoleMode(h, mode.value | 0x0004))
    except Exception:
        return False


def _enabled():
    force = os.environ.get("FORCE_COLOR")
    if force is not None:
        return force not in ("", "0")
    if os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty() or os.environ.get("TERM") == "dumb":
        return False
    if os.name == "nt":
        return _windows_vt_ok()
    return True


_ON = _enabled()
_CODES = {"green": "32", "red": "31", "amber": "33", "dim": "90"}


def paint(text, colour):
    if not _ON or colour not in _CODES:
        return text
    return f"\033[{_CODES[colour]}m{text}\033[0m"
