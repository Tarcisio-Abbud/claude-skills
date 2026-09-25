#!/usr/bin/env python3
"""The consolidation step of `../skills/wrap-up/SKILL.md`, and the order it prescribes.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHY THE STEP EXISTS. An unattended package triages every session finding on its own, at the
moment of discovery, and the unattended ladder's middle rung writes ONE item for it
(`../reference/session-finding.md`). Nothing then looked at the SET. Overlap is invisible
finding by finding and obvious in the pile: on 2026-09-02 a package of five slices queued
eleven items, four of which were the same work said twice. The counterpart runs where the
user is back in the room, before the report goes out.

THE ORDER IS THE HALF THAT GETS LOST. Folding two items is `edit --text` on the survivor and
`cancel --why` on the source, and only in that order: the block ceiling is measured on the
whole item, so the union's text is refused once the source it came from is gone and there is
nothing left to paste. That refusal was met three times in one sitting.

WHAT IS ASSERTED IS THE PROSE. Nothing here runs a wrap-up; what a session did with the
step is what its own report says. The vacuity guard comes first, as in every
doc-conformance file here: each check cuts a slice, and a slice that stopped matching would
leave the check reading an empty string.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
WRAP_UP = os.path.join(HERE, os.pardir, "skills", "wrap-up", "SKILL.md")

QUEUE_STEP = re.compile(r"^## 2\..*$", re.M)
REPORT_STEP = re.compile(r"^## 6\..*$", re.M)
CONSOLIDATE = "Consolidate"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return re.sub(r"\s+", " ", text)


def step(text, heading):
    m = heading.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


class ConsolidationTest(unittest.TestCase):
    def setUp(self):
        self.text = read(WRAP_UP)
        self.step2 = flat(step(self.text, QUEUE_STEP))

    def test_the_slices_this_file_cuts_are_still_there(self):
        self.assertTrue(QUEUE_STEP.search(self.text),
                        "wrap-up/SKILL.md has no `## 2.` step — re-anchor this file")
        self.assertTrue(REPORT_STEP.search(self.text),
                        "wrap-up/SKILL.md has no `## 6.` step, so `before the report` "
                        "names no place")
        self.assertTrue(self.step2.strip(), "step 2 is empty")

    def test_the_wrap_up_orders_a_consolidation(self):
        self.assertIn(CONSOLIDATE, self.step2,
                      "the wrap-up never asks for the set to be read together, so a "
                      "package's findings reach the user as one item each — which is how "
                      "eleven items came out of five slices")

    def test_the_consolidation_comes_before_the_report(self):
        """Its whole value is the moment: consolidated after the report, the user
        has already read the list it was meant to shorten."""
        self.assertIn("before the report", self.step2,
                      "the consolidation is prescribed without saying when, and the step "
                      "that owns the report is the one it has to precede")
        self.assertLess(self.text.index(CONSOLIDATE), REPORT_STEP.search(self.text).start(),
                        "the consolidation is written after the report step, so the "
                        "ordering it claims contradicts where it stands")

    def test_both_tests_of_a_fusion_are_named(self):
        """One test alone leaves half the overlap standing: two items in one file
        are not always one item, and two halves of one rule are rarely in one file."""
        said = self.step2
        self.assertRegex(said, r"same FILE",
                         "the first fusion test is missing: two items whose change lands "
                         "in one file are the pair a reader sees and folds")
        self.assertRegex(said, r"two halves of one RULE",
                         "the second fusion test is missing, and it is the one no file "
                         "listing finds: two items each doing half of one rule")

    def test_the_order_of_the_two_commands_is_named(self):
        """`cancel` first destroys the text the union is built from, and the block
        ceiling then refuses the `edit` that would have carried it.

        Read off the fold's own SENTENCE, not the step. Asked of the step, the
        emphasis check passed a text with the word removed: step 2 already says
        "the item records the FIRST in the order above" about the survival gates,
        and a search unit that wide answers about somebody else's sentence.
        """
        fold = next((s for s in re.split(r"(?<=\.)\s+", self.step2)
                     if "edit --text" in s), "")
        self.assertTrue(fold, "the fold does not name `edit --text`")
        self.assertIn("cancel --why", fold,
                      "the two commands are prescribed in different sentences, so their "
                      "order is not stated anywhere a reader must read")
        self.assertLess(fold.find("edit --text"), fold.find("cancel --why"),
                        "`cancel` is prescribed before `edit`: the source's text is gone "
                        "before the union is written, and the ceiling refuses what is left")
        self.assertIn("FIRST", fold,
                      "the two commands are named in order and the order is not called "
                      "out, so a reader reorders them without noticing")

    def test_the_steps_done_when_counts_the_consolidation(self):
        """A step nobody checks is a step an unattended reading skips."""
        done = self.step2[self.step2.index("**Done when:**"):]
        self.assertIn("consolidated", done,
                      "step 2's completeness check does not mention the consolidation, "
                      "so the step can be skipped with the check still green")


if __name__ == "__main__":
    unittest.main()
