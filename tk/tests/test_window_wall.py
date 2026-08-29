#!/usr/bin/env python3
"""Doc-conformance proof for step 2 of `../skills/kickoff/WINDOW.md`'s wall.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

What it proves: the `tk-queue handoff` the wall PRESCRIBES is lifted out of that step and
made to run against a throwaway queue, on an ORDINARY item — `--class AUTONOMOUS`, no
`--deferred` — and the remedy the tool prints leaves that item pointing at its briefing.

Why an ordinary item is the case worth a fixture. `test_afk_audit.py` already runs a
briefing recipe end to end, but its item is a REGRILL: a `DECISION` whose link rides in
`--deferred "afk — [[handoff-T00N]]"`, written by a command the recipe spells out. Every
other site that prescribes a handoff — the wall here, this file's planning seam, `AFK.md`'s
close and its oversized item, `wrap-up/SKILL.md` — writes no such field, so the link can
only come from the `tk-queue edit --text` the tool prints on stderr. That is the path this
file executes, and until it existed nothing did.

The warning is the reason the step needs the instruction at all: it goes to **stderr at exit
0**, so a run that ignores it succeeds, and the wall is the moment nobody is reading that
stream. A briefing no item names is one the next generation never finds.

What it does NOT prove: that an orchestrator meeting the wall reaches step 2 at all. Nothing
here can see a session. It also asserts nothing about the OTHER five steps of the wall.

The only edits made to the prescribed command before running it: the metavariables the step
writes as `"<id>"` and `"..."`, filled with the id the fixture's `add` printed and with real
field text, and `--dir <throwaway>`, so no real memory dir is touched.
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
WINDOW = os.path.join(HERE, os.pardir, "skills", "kickoff", "WINDOW.md")
VERIFY = os.path.join(HERE, os.pardir, "skills", "verify", "SKILL.md")

HEADER = """---
name: next-steps
description: fixture
metadata:
  type: project
---

# Next steps

"""

WALL_HEADING = re.compile(r"^## The wall\s*$", re.M)

# The three `"..."` of the prescribed handoff, in the order the step writes them:
# --objective, --state, --blockers. Real text, because the briefing's gate refuses
# a mandatory field that carries none.
FIELDS = ("resume the package where the wall stopped it",
          "T001 pushed to branch t001; the window resets at 14:20",
          "none — the claims are held")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def wall_section(text=None):
    """WINDOW.md from `## The wall` to the next `## ` heading.

    Scoped, for the reason `test_afk_audit.py` scopes its own extraction: a
    `tk-queue` line prescribed under any OTHER section of this file must not be
    folded into the wall's recipe and executed here.
    """
    text = read(WINDOW) if text is None else text
    m = WALL_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def numbered_step(section, n):
    """Step `n` of the section's numbered list, its continuation lines joined.

    The step's prose is wrapped, and the prescribed command is an inline code span
    broken across two lines by that wrapping. Joining first is what lets the span be
    read as the one line a reader pastes.
    """
    m = re.search(r"^%d\. (.*?)(?=^\d+\. |\Z)" % n, section, re.M | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def inline_commands(step):
    """The `tk-queue …` inline code spans of a step, whitespace collapsed."""
    return [re.sub(r"\s+", " ", s).strip()
            for s in re.findall(r"`(tk-queue [^`]*)`", step)]


def fill(line, iid, fields=FIELDS):
    """The prescribed line with its metavariables substituted, as a reader fills them."""
    out = line.replace('"<id>"', shlex.quote(iid))
    for value in fields:
        out = out.replace('"..."', shlex.quote(value), 1)
    return out


def item_fields(body):
    """The `**Field:** value.` segments of the queue's first open item.

    Derived from the item, never a hand-kept list — the same reason the sibling
    suite derives it: the printed remedy REWRITES the item, and what it leaves
    behind is only checkable against what was there.
    """
    line = next((ln for ln in body.splitlines() if ln.startswith("- [ ] ")), "")
    return [seg.strip() for seg in re.findall(r"\*\*[A-Za-z]+:\*\*[^*]*", line)]


class WallStep2Test(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tk-window-wall-test.")
        self.mem = os.path.join(self.dir, "memory")
        os.makedirs(self.mem)
        # HOME is redirected so no real site file (~/.claude/tk/env) can change what
        # the subprocess accepts depending on whose machine runs the suite.
        self.home = os.path.join(self.dir, "home")
        os.makedirs(self.home)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER)
        self.step2 = numbered_step(wall_section(), 2)
        self.bin = self.shim()

    def shim(self):
        """A `tk-queue` at the FRONT of PATH, so a pasted line runs THIS tree's script.

        Without it the shell resolves `tk-queue` from the machine's own PATH — this
        site installs the plugin's bin there — and the pasted remedy runs the live
        clone while the suite believes it ran the tree under test. Measured here: the
        run went green against `/root/.claude/skills/tk/bin/tk-queue`, which is also
        what would make the mutation harness score a bin mutant as surviving.

        It bakes in `--dir <throwaway>`, so the line is pasted exactly as printed and
        still cannot reach a real memory dir.
        """
        d = os.path.join(self.dir, "bin")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "tk-queue")
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\nexec %s %s \"$@\" --dir %s\n"
                    % (shlex.quote(sys.executable), shlex.quote(os.path.abspath(TK)),
                       shlex.quote(self.mem)))
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return d

    def env(self):
        return dict(os.environ, HOME=self.home,
                    PATH=self.bin + os.pathsep + os.environ["PATH"])

    def run_tk(self, argv):
        """Run a command as an argv list (no shell)."""
        return subprocess.run([sys.executable, TK, *argv[1:], "--dir", self.mem],
                              capture_output=True, text=True, cwd=self.dir,
                              env=self.env(), timeout=60)

    def run_shell(self, line):
        """Run a line by PASTING it into a shell, as the reader of the warning does."""
        return subprocess.run(["bash", "-c", line], capture_output=True, text=True,
                              cwd=self.dir, env=self.env(), timeout=60)

    def body(self):
        return read(os.path.join(self.mem, "next-steps.md"))

    def add_ordinary_item(self):
        """The item the wall finds in flight: AUTONOMOUS, and carrying no Deferred."""
        r = self.run_tk(["tk-queue", "add", "empacotar a fatia em curso",
                         "--class", "AUTONOMOUS", "--effort", "M (~30min)",
                         "--criterion", "A: a suite passa"])
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split()[1].rstrip(":")

    # --- the guards on the prose ---------------------------------------------

    def test_the_wall_step_prescribes_the_handoff_and_the_edit_it_prints(self):
        """The first half of the item's criterion, and the guard that stops the run
        below from proving the tool while the instruction is gone from the prose."""
        self.assertTrue(wall_section().strip(), "WINDOW.md has no `## The wall` section")
        cmds = inline_commands(self.step2)
        self.assertTrue([c for c in cmds if c.startswith("tk-queue handoff")],
                        "the wall's step 2 prescribes no `tk-queue handoff` — the run "
                        "below has nothing to lift, and every check in it is vacuous")
        self.assertRegex(self.step2, r"run the `edit` it\s+prints",
                         "the wall's step 2 writes the briefing and never says to run the "
                         "`edit` the command prints — the item is left with no pointer at "
                         "it, and the briefing is one nothing leads to")

    def test_the_file_the_wall_sends_the_reader_to_carries_the_rule(self):
        """A pointer aimed at a file that says nothing sends the reader to silence."""
        self.assertIn("../verify/SKILL.md", self.step2,
                      "the wall's step 2 names no owner for the handoff's form")
        owner = read(VERIFY)
        self.assertIn("[[handoff-T00N]]", owner)
        self.assertIn("Run it as printed", owner,
                      "`verify/SKILL.md` is pointed at for the rule and does not state it")

    # --- the fixture ----------------------------------------------------------

    def test_an_ordinary_item_points_at_its_briefing_after_the_printed_edit(self):
        """Lift the wall's handoff, run it on a non-DECISION item, run the remedy it
        prints, and ask the queue what is actually there afterwards."""
        cmds = [c for c in inline_commands(self.step2) if c.startswith("tk-queue handoff")]
        self.assertTrue(cmds, "the wall's step 2 prescribes no handoff to run")
        iid = self.add_ordinary_item()
        line = fill(cmds[0], iid)
        self.assertNotIn('"..."', line, "a metavariable the filler does not know was added "
                                        "to the prescribed command")
        self.assertNotRegex(line, r"<[^>]+>", "an unfilled metavariable survived the filler")

        r = self.run_tk(shlex.split(line))
        self.assertEqual(r.returncode, 0,
                         f"the prescribed handoff does not run:\n$ {line}\n{r.stderr}")
        self.assertNotIn("[[handoff-", r.stdout,
                         "the warning reached stdout — the step's reason for naming it is "
                         "that it goes to the stream nobody reads")
        self.assertNotIn(f"[[handoff-{iid}]]", self.body(),
                         "the item points at the briefing before the remedy ran — this "
                         "test proves nothing")

        m = re.search(r"`(tk-queue edit [^`]+)`", r.stderr)
        self.assertTrue(m, f"the handoff printed no remedy to run:\n{r.stderr}")
        fields_before = item_fields(self.body())
        self.assertIn("**Class:** AUTONOMOUS.", fields_before,
                      "the item under test is not the ordinary one — the DECISION path is "
                      "the one `test_afk_audit.py` already covers")

        # PASTED into a shell, exactly as printed: the remedy's quoting is half of
        # what makes it runnable, and `shlex.split` plus an argv list never meets a shell.
        remedy = self.run_shell(m.group(1))
        self.assertEqual(remedy.returncode, 0,
                         f"the printed remedy does not run:\n$ {m.group(1)}\n{remedy.stderr}")

        body = self.body()
        self.assertIn(f"[[handoff-{iid}]]", body,
                      "the remedy ran and the item still does not point at its briefing")
        self.assertNotIn("**Class:** DECISION.", body)
        self.assertNotIn("**Deferred:**", body,
                         "the item acquired a Deferred field — the link under test is the "
                         "one the printed `--text` writes, not the one `--deferred` carries")
        for seg in fields_before:
            self.assertIn(seg, body, f"the printed remedy dropped {seg!r} from the item")

        again = self.run_tk(shlex.split(line))
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertNotIn("does not point at", again.stderr,
                         "the linked item is still warned about — the remedy wrote a "
                         "pointer the command does not read back")


if __name__ == "__main__":
    unittest.main()
