#!/usr/bin/env python3
"""Doc-conformance proof that moving the package's handoff re-points what names it.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

THE DEFECT. `../skills/kickoff/AFK.md` step 5 moves the package's briefing off an item before
`tk-queue done` deletes it, onto the item that now closes last. The package pointer
(`~/.claude/state/tk-package.json`, `WINDOW.md`, *Three pieces*) kept its `handoff` field on the
old file, so after the close the compact hook told a compacted orchestrator to read a briefing
that no longer exists. A tick whose prompt carries that path goes stale the same way, and a cron
prompt cannot be edited: it is deleted and armed again.

THE DESIGN PINNED HERE. The move paragraph carries the pointer rewrite in the same move, as a
command that touches the pointer only where its `handoff` names the closing item's file — a
pointer naming another file (a fleet's sibling run) or no pointer at all is left alone. The
tick half is conditional, because `WINDOW.md`, *The tick*, specifies a prompt that names
`tk-quota`, `tk-context` and `WINDOW.md`, not the handoff file.

THE PROSE IS WHAT IS ASSERTED, anchored on content, never on line numbers; the prescribed
command is RUN, against a throwaway HOME, because a command in prose is code.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

STEP_HEADING = re.compile(r"^## 5\. Verify every delivery\s*$", re.M)
MOVE_ANCHOR = "**The package's handoff hangs on the item that closes LAST**"
NEXT_ANCHOR = "A solo item's pull request takes the cold review"
POINTER = "~/.claude/state/tk-package.json"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def move_rule():
    """Step 5's handoff-move rule: from its bold anchor to the solo cold-review paragraph."""
    text = read(AFK)
    m = STEP_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    rest = rest[:nxt.start()] if nxt else rest
    start = rest.find(MOVE_ANCHOR)
    if start == -1:
        return ""
    end = rest.find(NEXT_ANCHOR, start)
    return rest[start:end if end != -1 else len(rest)]


def pointer_command(rule):
    blocks = re.findall(r"^```sh\n(.*?)^```", rule, re.M | re.S)
    hits = [b for b in blocks if POINTER in b]
    return hits[0] if len(hits) == 1 else None


class TheHandoffMoveRePointsWhatNamesIt(unittest.TestCase):
    def setUp(self):
        self.rule = move_rule()
        self.flat = flat(self.rule)

    def test_the_anchors_are_still_there(self):
        self.assertTrue(self.rule, "AFK.md step 5 lost the handoff-move rule")
        self.assertIn("rewrite it on the item that now closes last", self.flat)

    def test_the_move_updates_the_pointer_s_handoff_in_the_same_move(self):
        self.assertRegex(self.flat, r"(?i)in the same move",
                         "the move no longer says the re-pointing happens with it")
        self.assertRegex(self.flat, r"pointer's `handoff`",
                         "the move leaves the package pointer's `handoff` on the file "
                         "`done` deletes")

    def test_the_move_re_arms_a_tick_that_names_the_file(self):
        self.assertRegex(self.flat, r"(?i)where the tick's prompt names",
                         "the move says nothing of a tick whose prompt carries the path")
        self.assertIn("`CronDelete`", self.flat,
                      "a cron prompt cannot be edited; the rule must delete and re-arm")


class ThePrescribedCommandRuns(unittest.TestCase):
    """The block is run as written, its two placeholders filled, under a throwaway HOME."""

    def setUp(self):
        self.cmd = pointer_command(move_rule())
        self.assertIsNotNone(self.cmd, "the move rule carries no single `sh` block that "
                                       "rewrites the package pointer")
        self.assertEqual(len(re.findall(r'"<[^">]+>"', self.cmd)), 2,
                         "the command no longer takes exactly the old and the new file")
        self.home = tempfile.mkdtemp(prefix="tk-handoff-move.")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.queue = os.path.join(self.home, "queue")
        os.makedirs(self.queue)
        self.old = os.path.join(self.queue, "handoff-T1.md")
        self.new = os.path.join(self.queue, "handoff-T2.md")
        for path in (self.old, self.new):
            with open(path, "w", encoding="utf-8") as f:
                f.write("briefing\n")
        self.pointer = os.path.join(self.home, ".claude", "state", "tk-package.json")

    def write_pointer(self, handoff):
        os.makedirs(os.path.dirname(self.pointer), exist_ok=True)
        body = {"package": "p", "ledger": "l", "handoff": handoff, "session": "s"}
        with open(self.pointer, "w", encoding="utf-8") as f:
            json.dump(body, f)
        return body

    def run_cmd(self):
        args = iter([self.old, self.new])
        filled = re.sub(r'"<[^">]+>"', lambda _: '"%s"' % next(args), self.cmd)
        run = subprocess.run(["sh", "-c", filled], capture_output=True, text=True,
                             timeout=60, env=dict(os.environ, HOME=self.home))
        self.assertEqual(run.returncode, 0, run.stderr)

    def pointer_now(self):
        with open(self.pointer, encoding="utf-8") as f:
            return json.load(f)

    def test_a_pointer_naming_the_closing_file_moves_to_the_new_one(self):
        before = self.write_pointer(self.old)
        self.run_cmd()
        after = self.pointer_now()
        self.assertEqual(os.path.realpath(after["handoff"]), os.path.realpath(self.new))
        self.assertEqual({k: v for k, v in after.items() if k != "handoff"},
                         {k: v for k, v in before.items() if k != "handoff"},
                         "the rewrite lost the pointer's other fields")

    def test_a_pointer_naming_another_file_is_left_alone(self):
        other = os.path.join(self.queue, "handoff-T9.md")
        before = self.write_pointer(other)
        self.run_cmd()
        self.assertEqual(self.pointer_now(), before,
                         "the rewrite took a pointer that named another briefing")

    def test_no_pointer_writes_none(self):
        self.run_cmd()
        self.assertFalse(os.path.exists(self.pointer),
                         "the rewrite created a pointer where the package had none")


if __name__ == "__main__":
    unittest.main()
