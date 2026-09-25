#!/usr/bin/env python3
"""The throwaway queue that every doc-conformance suite runs its prescriptions against.

`test_afk_audit.py` grew these pieces first; `test_window_wall.py` needs the same seven, and
a second copy would be a second answer to "where does a prescribed command run" — the reason
this repo has one `mutations_tk_contract.run` with a seam rather than eight runners.

What a subclass gets:

- `self.mem`, a queue directory holding nothing but an empty `next-steps.md`;
- `run_tk(argv)`, which runs a prescribed command as an argv list against that directory;
- `run_shell(line)`, which PASTES a line into bash, the only way to exercise the shell
  quoting of a command the tool prints for a human to paste;
- `self.bin`, a `tk-queue` at the FRONT of `PATH` carrying `--dir self.mem`, so a pasted
  line runs THIS tree's script — the machine's own `PATH` may hold an installed plugin bin,
  or no `tk-queue` at all, and the mutation runner works on a copy of `tk/` whose script is
  the one under test;
- `reached()`, the count of lines that got as far as `tk-queue`. A pasted line can die in
  the shell before the script is ever reached, and an exit code alone cannot tell the two
  apart;
- a redirected `HOME`, so no real site file (`~/.claude/tk/env`) changes what the subprocess
  accepts depending on whose machine runs the suite.

No real memory dir is reachable from here: every route into `tk-queue` carries `--dir`, and
the directory it names is made by `tempfile` and removed on cleanup.

THAT SAME `--dir` MASKS THE PROSE, and a subclass that forgets it tests nothing. Appended
after the prescribed arguments, it is the one argparse keeps — so a recipe that lost its own
`--dir "<queue dir>"` still runs green through here. A file running a prescription must
assert the flag on the ARGV the prose produced, before either route is reached; both
subclasses do (`test_afk_audit.py`, `test_window_wall.py`).
"""

import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TK = os.path.join(HERE, os.pardir, "bin", "tk-queue")

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""


def item_fields(body):
    """The `**Field:** value.` segments of the queue's first open item.

    Derived from the item, never a hand-kept list: a printed remedy REWRITES the
    item, and what it left behind is only checkable against what was there.
    """
    line = next((ln for ln in body.splitlines() if ln.startswith("- [ ] ")), "")
    return [seg.strip() for seg in re.findall(r"\*\*[A-Za-z]+:\*\*[^*]*", line)]


class QueueFixture(unittest.TestCase):
    """Base for a suite that RUNS what a skill file prescribes."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tk-doc-conformance-test.")
        self.mem = os.path.join(self.dir, "memory")
        os.makedirs(self.mem)
        self.home = os.path.join(self.dir, "home")
        os.makedirs(self.home)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER)
        self.calls = os.path.join(self.dir, "calls.log")
        self.bin = self.shim()

    def shim(self):
        d = os.path.join(self.dir, "bin")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "tk-queue")
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\necho \"reached\" >> %s\nexec %s %s \"$@\" --dir %s\n"
                    % (shlex.quote(self.calls), shlex.quote(sys.executable),
                       shlex.quote(os.path.abspath(TK)), shlex.quote(self.mem)))
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return d

    def reached(self):
        if not os.path.exists(self.calls):
            return 0
        with open(self.calls, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def env(self):
        return dict(os.environ, HOME=self.home,
                    PATH=self.bin + os.pathsep + os.environ["PATH"])

    def run_tk(self, argv):
        """Run a prescribed command as an argv list (no shell)."""
        return subprocess.run([sys.executable, TK, *argv[1:], "--dir", self.mem],
                              capture_output=True, text=True, cwd=self.dir,
                              env=self.env(), timeout=60)

    def run_shell(self, line):
        """Run a line by PASTING it into a shell, as a human does."""
        return subprocess.run(["bash", "-c", line], capture_output=True, text=True,
                              cwd=self.dir, env=self.env(), timeout=60)

    def body(self):
        with open(os.path.join(self.mem, "next-steps.md"), encoding="utf-8") as f:
            return f.read()
