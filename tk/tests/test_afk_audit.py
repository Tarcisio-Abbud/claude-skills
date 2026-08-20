#!/usr/bin/env python3
"""Doc-conformance proof for the audit step of `../skills/kickoff/AFK.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

What it proves: the `tk-queue` recipe that step PRESCRIBES for a REGRILL is lifted out of
the audit SECTION of AFK.md and made to run — as an argv list and, separately, in a real
shell — landing a `DECISION` item that carries its **Deferred:** gate and, after the remedy
the tool prints, points at its briefing. Every prescribed command that sets
`--class DECISION`, whatever its subcommand, must carry `--deferred`; and the `add` with
`--deferred` removed must be refused with nothing entering the queue.

Four properties are deliberate, each having been a hole once:

- the extraction is scoped to the audit section, so a ```sh example added under any OTHER
  step is neither folded into "the recipe" nor executed here;
- the gate sweep asks `--class DECISION` of every subcommand, not only of `add`: an ungated
  `edit --class DECISION` beside the real recipe once sat under a green suite;
- the recipe is run through a shell as well as through argv, because `shlex.split` plus
  `subprocess.run(list)` never meets a shell;
- and one shell run is made with the metavariables left ALONE. Substituting them first is
  what a reader is told to do, and it is also what hides an unquoted `<id>`: substituted, it
  is an ordinary word either way. Left alone it is the shell's own metacharacter, and the
  line dies at `bash: id: No such file or directory` before `tk-queue` is reached. So that
  run asserts the weaker, real property — the shell HANDS the line to `tk-queue` — measured
  through a shim that records every invocation.

What it does NOT prove: that an orchestrator running a package reaches the step at all, or
that a REGRILL it decided on was really queued. Nothing here can see a session — that is
what the block the step owes step 6 is for. It also does not execute prescribed subcommands
other than `add` and `handoff`: those are swept for the gate, not run, since giving each one
a fixture is work of its own.

The only edits made to a prescribed command before running it: `--dir <throwaway>`, applied
by the shim so no real memory dir is touched, and `<id>`, which becomes the id the `add`
printed.
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
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""

AUDIT_HEADING = re.compile(r"^## \d+\. Audit\b.*$", re.M)


def afk_text():
    with open(AFK, encoding="utf-8") as f:
        return f.read()


def audit_section(text=None):
    """AFK.md from the audit heading to the next `## ` heading.

    Scoped on purpose: this used to regex the whole file, so a legitimate ```sh
    example under any other step was folded into the recipe and executed here —
    the test's own target moving with no signal.
    """
    text = afk_text() if text is None else text
    m = AUDIT_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def logical_lines(section):
    """The `tk-queue` lines of the section's ```sh fences, backslash-joined."""
    out = []
    for block in re.findall(r"^```sh\n(.*?)^```", section, re.M | re.S):
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            line = line.strip()
            if line.startswith("tk-queue "):
                out.append(line)
    return out


def prescribed_commands():
    """The prescribed lines as (text, argv) pairs, in file order."""
    return [(line, shlex.split(line)) for line in logical_lines(audit_section())]


def sets_decision(argv):
    """Whether this command sets --class DECISION — for ANY subcommand.

    `add` is not the only route: `edit --class DECISION` reaches the same state and
    tk-queue gates it the same way. Asking only about `add` let an ungated
    `edit --class DECISION` sit beside the real recipe with the suite green.
    """
    return "--class" in argv and argv[argv.index("--class") + 1] == "DECISION"


def subcommand(argv):
    return argv[1] if len(argv) > 1 else ""


def without_flag(argv, flag):
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
        self.calls = os.path.join(self.dir, "calls.log")
        self.bin = self.shim()

    def shim(self):
        """A `tk-queue` on PATH, so a prescribed line runs in a shell as written.

        It records one line per invocation: that log is how a shell run proves the
        line REACHED tk-queue, rather than dying in the shell first.
        """
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
        """Run a prescribed command by PASTING it into a shell, as a human would."""
        return subprocess.run(["bash", "-c", line], capture_output=True, text=True,
                              cwd=self.dir, env=self.env(), timeout=60)

    def body(self):
        with open(os.path.join(self.mem, "next-steps.md"), encoding="utf-8") as f:
            return f.read()

    def runnable(self):
        """The prescribed lines this file executes, in order."""
        return [(line, argv) for line, argv in self.cmds
                if subcommand(argv) in ("add", "handoff")]

    # --- the guards that stop every check below from passing over nothing ----

    def test_the_audit_step_and_its_regrill_recipe_are_still_there(self):
        """Each check below iterates a list derived from AFK.md; an empty list
        would let all of them pass while the recipe was gone."""
        text = afk_text()
        # assertTrue, not assertRegex: the latter prints the whole file on failure.
        self.assertTrue(AUDIT_HEADING.search(text), "AFK.md has no numbered Audit step")
        self.assertTrue(audit_section(text).strip(), "the Audit section is empty")
        self.assertTrue([a for _, a in self.cmds if sets_decision(a)],
                        "the audit section prescribes no `--class DECISION` command — "
                        "the REGRILL recipe is gone, and every gate check below is vacuous")
        self.assertTrue([a for _, a in self.cmds if subcommand(a) == "handoff"],
                        "the REGRILL recipe prescribes no handoff")

    def test_the_extraction_is_scoped_to_the_audit_section(self):
        """A ```sh example under another step must not be folded into the recipe."""
        text = afk_text()
        intruder = ('\n```sh\ntk-queue add "not the recipe" --class AUTONOMOUS '
                    '--effort S --criterion "A: x"\n```\n')
        m = re.search(r"^## \d+\. Verify\b.*$", text, re.M)
        self.assertTrue(m, "the step after the audit was renamed; re-anchor this test")
        # AFTER that heading, so the intruder really sits in the next step: inserted
        # before it, it lands inside the audit section, which runs up to that heading.
        spiked = text[:m.end()] + intruder + text[m.end():]
        self.assertIn("not the recipe", spiked)
        self.assertEqual(logical_lines(audit_section(spiked)),
                         logical_lines(audit_section(text)),
                         "a command from another step was folded into the recipe")

    # --- the gate ------------------------------------------------------------

    def test_every_prescribed_decision_command_carries_the_deferral(self):
        for line, argv in self.cmds:
            if sets_decision(argv):
                with self.subTest(cmd=line):
                    self.assertIn("--deferred", argv,
                                  "a DECISION prescribed with no --deferred: the recipe asks "
                                  "the orchestrator to run a command tk-queue refuses")

    def test_the_prescribed_regrill_runs_and_lands_a_gated_decision(self):
        """The recipe is code. Run it, in order, in a throwaway dir."""
        iid, ran = None, 0
        for line, argv in self.runnable():
            if subcommand(argv) == "add":
                r = self.run_tk(argv)
                self.assertEqual(r.returncode, 0, f"{line}\n{r.stderr}")
                iid = r.stdout.split()[1].rstrip(":")
                ran += 1
            else:
                self.assertTrue(iid, "a handoff is prescribed before any add")
                r = self.run_tk([a if a != "<id>" else iid for a in argv])
                self.assertEqual(r.returncode, 0, f"{line}\n{r.stderr}")
                self.assertTrue(os.path.exists(r.stdout.split(maxsplit=1)[1].strip()),
                                "handoff reported a file it did not write")
        self.assertTrue(ran, "no prescribed add was run")
        self.assertIn("**Class:** DECISION.", self.body())
        self.assertIn("**Deferred:**", self.body())

    def test_the_recipe_runs_in_a_shell_once_its_metavariables_are_filled(self):
        """The reader is told to substitute `<id>` and run. Do exactly that."""
        iid = None
        for line, argv in self.runnable():
            with self.subTest(cmd=line):
                r = self.run_shell(line if iid is None else line.replace("<id>", iid))
                self.assertEqual(r.returncode, 0,
                                 f"the prescribed line does not survive a shell:\n"
                                 f"$ {line}\n{r.stderr}")
                if subcommand(argv) == "add":
                    iid = r.stdout.split()[1].rstrip(":")
        self.assertTrue(iid, "no prescribed add reached the shell")

    def test_a_raw_paste_reaches_tk_queue_instead_of_dying_in_the_shell(self):
        """The metavariables are left ALONE here, which is the only way an unquoted
        one is visible: substituted, `<id>` is an ordinary word either way.

        The property asserted is deliberately weak, and it is the true one — the
        shell HANDS the line to tk-queue. What tk-queue then says about a literal
        `<id>` is its own business (it refuses it, which is correct). Unquoted, the
        line never gets that far: bash reads `<id>` as a redirect and dies.
        """
        lines = self.runnable()
        self.assertTrue(lines, "no prescribed line to paste")
        for line, _ in lines:
            with self.subTest(cmd=line):
                before = self.reached()
                r = self.run_shell(line)
                self.assertEqual(self.reached(), before + 1,
                                 f"the shell never reached tk-queue — a metavariable is "
                                 f"unquoted and the shell ate the line:\n$ {line}\n{r.stderr}")

    def test_the_briefing_is_reachable_from_the_item_after_the_printed_edit(self):
        """The handoff warns (exit 0) that the item does not point at its briefing
        and prints the `edit` that repairs it. The recipe says to run it — so run
        it here, as printed, and check the link is really there afterwards."""
        iid, warned = None, None
        for line, argv in self.runnable():
            if subcommand(argv) == "add":
                r = self.run_tk(argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                iid = r.stdout.split()[1].rstrip(":")
            else:
                r = self.run_tk([a if a != "<id>" else iid for a in argv])
                self.assertEqual(r.returncode, 0, r.stderr)
                warned = r.stderr
        self.assertTrue(iid and warned is not None, "the recipe lost its add or its handoff")
        self.assertNotIn(f"[[handoff-{iid}]]", self.body(),
                         "the item already points at the briefing — this test proves nothing")
        m = re.search(r"`(tk-queue edit [^`]+)`", warned)
        self.assertTrue(m, f"the handoff printed no remedy to run:\n{warned}")
        r = self.run_shell(m.group(1))
        self.assertEqual(r.returncode, 0, f"the printed remedy does not run:\n{r.stderr}")
        self.assertIn(f"[[handoff-{iid}]]", self.body(),
                      "the remedy ran and the item still does not point at its briefing")

    def test_the_same_regrill_without_the_gate_is_refused(self):
        """Checked backwards: the presence check above passes on a flag the script
        might no longer enforce, so the gate is watched firing."""
        for line, argv in self.cmds:
            if sets_decision(argv) and "--deferred" in argv:
                with self.subTest(cmd=line):
                    r = self.run_tk(without_flag(argv, "--deferred"))
                    self.assertNotEqual(r.returncode, 0,
                                        "a REGRILL entered the queue with no gate")
                    self.assertIn("--deferred", r.stderr)
                    self.assertEqual(self.body().count("- [ ] "), 0,
                                     "the refusal wrote the item anyway")


if __name__ == "__main__":
    unittest.main()
