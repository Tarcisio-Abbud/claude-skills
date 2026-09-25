"""Records which lines of the watched source files a Python process runs.

This file is never imported under this name. `mutations_tk_contract.reach_env`
copies it into a throwaway directory as `sitecustomize.py` and puts that
directory on PYTHONPATH, because `sitecustomize` is the one module the
interpreter imports before `__main__` in EVERY child process, and PYTHONPATH
carries it down nested ones. That is what these suites are: unittest spawns the
bin under test, and the bin spawns processes of its own.

Two environment variables drive it, both set by `reach_env`:

- `TK_REACH_FILES` — the path suffixes to watch, `os.pathsep`-separated, each
  already starting with a separator (`/bin/tk-hygiene`), so that a mutated copy
  of the tree under `/tmp` matches the same source.
- `TK_REACH_DIR` — where to leave the records. One file PER PROCESS, named by
  `mkstemp`: a suite runs many processes at once and appends to a shared file
  would interleave mid-line.

Neither variable set, it installs nothing and costs nothing, which is what
every process outside a measured baseline sees.
"""

import atexit
import os
import sys
import tempfile
import threading

_WATCH = tuple(s for s in os.environ.get("TK_REACH_FILES", "").split(os.pathsep) if s)
_OUT = os.environ.get("TK_REACH_DIR", "")
_HIT = {}


def _line(frame, event, arg):
    """The LOCAL trace, installed only on frames of a watched file."""
    if event == "line":
        _HIT[frame.f_code.co_filename].add(frame.f_lineno)
    return _line


def _call(frame, event, arg):
    """The GLOBAL trace, called once per frame entered.

    Returning None for a frame is what keeps the probe cheap: the interpreter
    then stops calling back for every line executed in it, and the suite pays
    one predicate per call rather than one per line.
    """
    name = frame.f_code.co_filename
    if name.endswith(_WATCH):
        _HIT.setdefault(name, set()).add(frame.f_lineno)
        return _line
    return None


def _dump():
    """One line per watched file: the path, then the line numbers it ran."""
    if not _HIT:
        return
    fd, _ = tempfile.mkstemp(dir=_OUT, suffix=".reach")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        for name, lines in _HIT.items():
            handle.write("%s %s\n" % (name, " ".join(str(n) for n in sorted(lines))))


if _WATCH and _OUT:
    atexit.register(_dump)
    sys.settrace(_call)
    threading.settrace(_call)
