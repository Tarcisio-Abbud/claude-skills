#!/usr/bin/env python3
"""Doc-conformance proof for the audit step of `../skills/kickoff/AFK.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

What it proves, and only this: the `tk-queue` commands that step PRESCRIBES for a REGRILL
are lifted out of AFK.md itself, run against a throwaway queue, and land a `DECISION` item
carrying its **Deferred:** gate — while the same command with `--deferred` removed is
refused with nothing entering the queue. The prescribed lines are code, so they are run
rather than read; the list of them is derived from the file, so a recipe rewritten without
the gate is caught rather than a hand-kept copy of it.

What it does NOT prove: that an orchestrator running a package reaches the step at all, or
that a REGRILL it decided on was really queued. Nothing here can see a session — that is
what the line the step owes step 6 is for.

The only edit made to a prescribed command before running it is `--dir <throwaway>`, so a
real memory dir is never touched, plus the `<id>` of the handoff line, which is the id the
`add` before it printed.
"""

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TK = os.path.join(HERE, os.pardir, "bin", "tk-queue")
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""

AUDIT_HEADING = re.compile(r"^## \d+\. Audit\b", re.M)


def afk_text():
    with open(AFK, encoding="utf-8") as f:
        return f.read()


def prescribed_commands():
    """Every `tk-queue` command AFK.md prescribes, in file order, as argv lists.

    Reads the ```sh fences, joins backslash continuations, and keeps the logical
    lines that invoke tk-queue. Derived, never hand-kept: the completeness checks
    below sit beside this list, and a list typed by hand is the next hole.
    """
    text = afk_text()
    cmds = []
    for block in re.findall(r"^```sh\n(.*?)^```", text, re.M | re.S):
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            line = line.strip()
            if line.startswith("tk-queue "):
                cmds.append(shlex.split(line))
    return cmds


def with_class(cmds, sub, klass):
    """The prescribed `sub` commands that set --class to `klass`."""
    out = []
    for argv in cmds:
        if len(argv) > 1 and argv[1] == sub and "--class" in argv:
            if argv[argv.index("--class") + 1] == klass:
                out.append(argv)
    return out


def without_flag(argv, flag):
    """argv with `flag` and the value after it removed."""
    i = argv.index(flag)
    return argv[:i] + argv[i + 2:]


class AfkAuditTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tk-afk-audit-test.")
        self.mem = os.path.join(self.dir, "memory")
        os.makedirs(self.mem)
        # HOME is redirected so no real site file (~/.claude/tk/env) can change
        # what the subprocess accepts depending on whose machine runs the suite.
        self.home = os.path.join(self.dir, "home")
        os.makedirs(self.home)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER)
        self.cmds = prescribed_commands()

    def run_tk(self, argv):
        env = dict(os.environ, HOME=self.home)
        return subprocess.run([sys.executable, TK, *argv[1:], "--dir", self.mem],
                              capture_output=True, text=True, cwd=self.dir,
                              env=env, timeout=60)

    def body(self):
        with open(os.path.join(self.mem, "next-steps.md"), encoding="utf-8") as f:
            return f.read()

    # --- the checks that stop the ones below from passing over nothing -------

    def test_the_audit_step_and_its_regrill_recipe_are_still_there(self):
        """Every check below iterates a list derived from AFK.md, and an empty list
        would make each of them pass while the recipe was gone."""
        text = afk_text()
        self.assertRegex(text, AUDIT_HEADING, "AFK.md has no numbered Audit step")
        self.assertTrue(with_class(self.cmds, "add", "DECISION"),
                        "AFK.md prescribes no `tk-queue add --class DECISION` — "
                        "the REGRILL recipe is gone, and every gate check below is vacuous")
        self.assertTrue([c for c in self.cmds if len(c) > 1 and c[1] == "handoff"],
                        "the REGRILL recipe prescribes no handoff")

    # --- the gate ------------------------------------------------------------

    def test_every_prescribed_decision_add_carries_the_deferral(self):
        for argv in with_class(self.cmds, "add", "DECISION"):
            with self.subTest(cmd=shlex.join(argv)):
                self.assertIn("--deferred", argv,
                              "a DECISION prescribed with no --deferred: the recipe "
                              "asks the orchestrator to run a command tk-queue refuses")

    def test_the_prescribed_regrill_runs_and_lands_a_gated_decision(self):
        """The recipe is code. Run it — both lines, in order — in a throwaway dir."""
        ran = 0
        for argv in self.cmds:
            if len(argv) > 1 and argv[1] == "add":
                r = self.run_tk(argv)
                self.assertEqual(r.returncode, 0, f"{shlex.join(argv)}\n{r.stderr}")
                iid = r.stdout.split()[1].rstrip(":")
                ran += 1
            elif len(argv) > 1 and argv[1] == "handoff":
                self.assertTrue(ran, "a handoff is prescribed before any add")
                r = self.run_tk([a if a != "<id>" else iid for a in argv])
                self.assertEqual(r.returncode, 0, f"{shlex.join(argv)}\n{r.stderr}")
                self.assertTrue(os.path.exists(r.stdout.split(maxsplit=1)[1].strip()),
                                "handoff reported a file it did not write")
        self.assertTrue(ran, "no prescribed add was run")
        self.assertIn("**Class:** DECISION.", self.body())
        self.assertIn("**Deferred:**", self.body())

    def test_the_same_regrill_without_the_gate_is_refused(self):
        """Checked backwards: the presence check above passes on a flag the script
        might no longer enforce, so the gate is watched firing."""
        for argv in with_class(self.cmds, "add", "DECISION"):
            with self.subTest(cmd=shlex.join(argv)):
                r = self.run_tk(without_flag(argv, "--deferred"))
                self.assertNotEqual(r.returncode, 0,
                                    "a REGRILL entered the queue with no gate")
                self.assertIn("--deferred", r.stderr)
                self.assertEqual(self.body().count("- [ ] "), 0,
                                 "the refusal wrote the item anyway")


if __name__ == "__main__":
    unittest.main()
