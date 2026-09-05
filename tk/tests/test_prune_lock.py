#!/usr/bin/env python3
"""The regression lock over the pruning track's result (spec #184).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

The track cut the plugin's skill prose by about half over nine slices, and
nothing held the result: `TestTheShippedSkills` in `test_tk_prune_measure.py`
asks only that a shipped file measure at all, so every word could come back and
the suite would stay green. Erosion is not hypothetical here — `wrap-up/SKILL.md`
gained 737 body words, +16%, in the four days between the first baseline and its
own pruning pass.

WHAT IS LOCKED, and why those two numbers. `tk/tests/prune-lock.json` carries,
per file, the `lines` and `body_words` the bin measured on the pruned tree, plus
the ceilings that file was already over. The bin caps neither lines nor words —
its six targets are all shape, and a file can double in length while passing every
one of them — so the size the track bought is held here or nowhere. The marks ride
along because a growing file that stays under its slack can still smuggle back the
40-word sentences the passes cut.

WHAT COUNTS AS A REGRESSION: growth past the locked number plus ten per cent, or a
ceiling mark the file did not carry when the lock was written. Shrinking is never a
failure and neither is losing a mark — a later pruning keeps the suite green
without touching the lock.

THE FOURTEEN OF THE TICKET ARE FIFTEEN. The ticket counts seven pruned skills and
seven MOVE destinations; the `kickoff` pass rewrote two files of one skill
(`SKILL.md` and `AFK.md`), so the pruned side is eight files. `docs/prune/lock.py`
carries the table and the provenance of every row.

PROVED BY INFLATION, not by a mutations file — the defect this suite guards
against lives in the skill files, not in a bin. Growing `verify/SKILL.md` by 15%
must redden `test_no_locked_file_grew_past_its_slack`, and by 8% must leave it
green. The two runs are in the pull request that added this file.
"""

import glob
import json
import math
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BIN = os.path.join(ROOT, "tk", "bin", "tk-prune-measure")
LOCK = os.path.join(HERE, "prune-lock.json")
REPORTS = os.path.join(ROOT, "docs", "prune")

REGENERATE = ("when the growth is earned, re-run "
              "`python3 docs/prune/lock.py <date> > tk/tests/prune-lock.json` "
              "and say so in the commit message")


def load_lock():
    with open(LOCK, encoding="utf-8") as f:
        return json.load(f)


class LockTest(unittest.TestCase):
    """Every file measured once, by the bin, for the whole class.

    The lock reads fifteen real files and three tests ask about each of them;
    measuring per test would run the bin forty-five times to learn the same
    numbers.
    """

    @classmethod
    def setUpClass(cls):
        cls.lock = load_lock()
        cls.measured = {}
        for path in cls.lock["files"]:
            absolute = os.path.join(ROOT, path)
            if not os.path.isfile(absolute):
                continue
            out = subprocess.run([sys.executable, BIN, absolute, "--json", "--targets"],
                                 capture_output=True, text=True)
            assert out.returncode == 0, f"{path}: {out.stdout}{out.stderr}"
            cls.measured[path] = json.loads(out.stdout)


class TestTheLockIsWellFormed(LockTest):
    def test_every_locked_file_is_still_on_disk(self):
        """A locked file that was renamed or deleted leaves the lock claiming
        coverage it no longer has, and every later assertion skips it in
        silence."""
        missing = [path for path in self.lock["files"]
                   if not os.path.isfile(os.path.join(ROOT, path))]
        self.assertEqual(missing, [], f"locked but not on disk: {missing} — "
                                      f"a rename updates `docs/prune/lock.py` too")

    def test_every_pruned_skill_has_its_file_locked(self):
        """Derived from the reports rather than from a second list here: a pass
        that ran left `docs/prune/<skill>-report.md` behind, and a skill whose
        report exists while its `SKILL.md` sits outside the lock is a hole."""
        reported = sorted(os.path.basename(p)[:-len("-report.md")]
                          for p in glob.glob(os.path.join(REPORTS, "*-report.md")))
        self.assertTrue(reported, f"no pruning report found under {REPORTS}")
        for skill in reported:
            with self.subTest(skill=skill):
                path = f"tk/skills/{skill}/SKILL.md"
                self.assertIn(path, self.lock["files"],
                              f"{skill} was pruned ({skill}-report.md) and its "
                              f"SKILL.md is not locked")

    def test_the_bin_still_carries_the_ceilings_the_lock_was_written_against(self):
        """`over` is a verdict, and a verdict means nothing without the numbers
        it was read against. A ceiling moved after the lock was written would
        make every mark comparison below compare two different questions."""
        report = next(iter(self.measured.values()))
        current = {m["metric"]: m["target"] for m in report["targets"]}
        self.assertEqual(current, self.lock["ceilings"],
                         f"the bin's ceilings moved since the lock — {REGENERATE}")

    def test_the_locked_numbers_are_the_committed_baseline_s(self):
        """The baseline document is the human-readable half of this lock, and a
        JSON that has drifted from it makes the committed table a decoration.
        Only the skill files are compared: `baseline.py` walks `tk/skills`, so
        the two `tk/reference` destinations are absent from its table by
        construction."""
        baseline = os.path.join(ROOT, self.lock["baseline"])
        with open(baseline, encoding="utf-8") as f:
            text = f.read()
        rows = re.findall(r"^\| `([^`]+\.md)` \| \**(\d+)\** \| \**(\d+)\** \|",
                          text, re.MULTILINE)
        self.assertTrue(rows, f"no measured rows read out of {self.lock['baseline']}")
        table = {f"tk/skills/{name}": (int(lines), int(words))
                 for name, lines, words in rows}
        compared = 0
        for path, locked in self.lock["files"].items():
            # A file the tree renamed after the lock was written keeps, in `baseline`,
            # the name the pruning pass measured it under — so the rename does not
            # quietly drop it out of this comparison. The numbers are the same numbers.
            name = locked.get("baseline")
            path = f"tk/skills/{name}" if name else path
            if path not in table:
                continue
            compared += 1
            with self.subTest(file=path):
                self.assertEqual(table[path], (locked["lines"], locked["body_words"]),
                                 f"{path}: the lock and {self.lock['baseline']} "
                                 f"disagree — {REGENERATE}")
        self.assertGreaterEqual(compared, 13, "the baseline table stopped covering "
                                              "the locked skill files")


class TestNothingGrewBack(LockTest):
    def slack_ceiling(self, locked):
        return math.floor(locked * (1 + self.lock["slack"]))

    def test_no_locked_file_grew_past_its_slack(self):
        """The lock proper. `lines` and `body_words` are the two numbers the bin
        reports and never caps, so they are the two the track's result hangs on."""
        for path, locked in self.lock["files"].items():
            if path not in self.measured:
                continue        # absent from disk: its own test says so
            metrics = self.measured[path]["metrics"]
            for key in ("lines", "body_words"):
                ceiling = self.slack_ceiling(locked[key])
                with self.subTest(file=path, metric=key):
                    self.assertLessEqual(
                        metrics[key], ceiling,
                        f"{path}: {key} {metrics[key]} over the locked "
                        f"{locked[key]} + {int(self.lock['slack'] * 100)}% "
                        f"= {ceiling}. Prune it back, or {REGENERATE}")

    def test_no_locked_file_gained_a_ceiling_mark(self):
        """Slack alone lets a file trade many short sentences for one long one.
        A mark the file did not carry at lock time is that trade, made visible."""
        for path, locked in self.lock["files"].items():
            if path not in self.measured:
                continue        # absent from disk: its own test says so
            over = {m["metric"] for m in self.measured[path]["targets"]
                    if m["status"] == "over"}
            with self.subTest(file=path):
                gained = sorted(over - set(locked["over"]))
                self.assertEqual(gained, [],
                                 f"{path}: newly over {gained}. Read the marked "
                                 f"lines with `tk/bin/tk-prune-measure {path} "
                                 f"--targets`, or {REGENERATE}")


if __name__ == "__main__":
    unittest.main()
