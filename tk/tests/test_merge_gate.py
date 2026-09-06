#!/usr/bin/env python3
"""Doc-conformance proof for two verdicts of `../skills/merge-gate/SKILL.md`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Verdict 5 has a suite of its own (`test_tk_closure.py`, beside the checker that answers it).
What is asked here is the pair no bin can answer, each born of a measured merge:

- **verdict 1 and the tree that actually merges** (T220). The five verdicts asked nothing
  about the branch being PUSHED, and what a forge merges is what its remote holds: a local
  commit ahead of `@{u}` is a tree the forge never sees. On 2026-08-27 that put the text from
  before a round of corrections into `main` (recovered by a second pull request). It is a
  line of verdict 1 rather than a sixth verdict, because verdict 1 is the one that names the
  tree, and because `verdict-5` is an identifier `tk-closure-check` prints: renumbering would
  rename it.

- **the fixer cap and its unit** (T326). *The strict form* required every finding fixed
  "under the fixer cap" and pointed nowhere, against the precedent of the family
  (`wrap-up/SKILL.md` points at `session-finding.md` for its own ladder). A cap with no
  address is read at the reader's convenience, and the convenient reading is per pull
  request — which is the one thing the cap is NOT: it counts per FIRING of the review, so a
  review re-fired by a resumed generation brings its own cycle.

WHAT IS ASSERTED IS THE PROSE. Nothing here runs a gate; a gate is fired by a person, and
the file says so in its own frontmatter (`disable-model-invocation: true`). The vacuity
guard comes first, as in every doc-conformance file in this directory: each check below cuts
a slice out of the file, and a slice that stopped matching would leave the check reading an
empty string.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, os.pardir, "skills", "merge-gate", "SKILL.md")

STRICT_HEADING = re.compile(r"^## The strict form \(unattended\)\s*$", re.M)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return re.sub(r"\s+", " ", text)


def row(text, number):
    """The verdict row of the five-verdict table, by its number.

    The FIRST table only: the accumulated lane restates the five with a Scope column,
    and a rule read off that one would answer for the lane and not for the gate.
    """
    for line in text.splitlines():
        if line.startswith(f"| {number} |") and "**" in line:
            return line
    return ""


def strict_form(text):
    """*The strict form*, up to the next `## ` heading."""
    m = STRICT_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


class MergeGateTest(unittest.TestCase):
    def setUp(self):
        self.text = read(GATE)

    def test_the_slices_every_check_below_cuts_are_still_there(self):
        self.assertTrue(row(self.text, 1),
                        "the gate has no `| 1 | **Tests** |` row — re-anchor this file")
        self.assertTrue(STRICT_HEADING.search(self.text),
                        "the gate has no `## The strict form (unattended)` section")
        self.assertIn("fixer cap", strict_form(self.text),
                      "the strict form no longer names the fixer cap, and the pointer "
                      "check below would be reading nothing")

    # --- T220: what merges is what the remote holds --------------------------

    def test_verdict_one_asks_whether_the_branch_is_pushed(self):
        """The tree the suite ran on and the tree the forge will merge are two
        different objects while a commit sits unpushed."""
        first = row(self.text, 1)
        self.assertIn("@{u}", first,
                      "verdict 1 says the suite ran and not WHERE: a local commit ahead "
                      "of the upstream is merged as the older tree the remote holds, and "
                      "the digest calls that green")
        self.assertIn("HEAD", first,
                      "verdict 1 names the upstream and not the local tip it must equal")

    def test_a_branch_with_no_upstream_is_red_too(self):
        """The comparison has a third answer. A branch nobody pushed has no `@{u}`
        at all, and a check that only compares two shas reads that as nothing to
        report."""
        self.assertRegex(flat(row(self.text, 1)), r"(?i)branch with none|no upstream",
                         "verdict 1 compares two shas and says nothing about a branch "
                         "that has no upstream to compare against")

    def test_a_red_verdict_is_not_offered_as_a_merge(self):
        """Verdict 1's new line only bites through this rule; without it the digest
        reports the red and the menu offers the merge anyway."""
        self.assertIn("the merge is not offered", flat(self.text),
                      "the gate no longer says a red verdict withholds the merge, so "
                      "every verdict above is a report and not a gate")

    # --- T326: the cap has an address and a unit -----------------------------

    def test_the_fixer_cap_points_at_its_definition(self):
        said = flat(strict_form(self.text))
        self.assertIn("The fixer cap", said,
                      "the strict form names the cap without naming the section that "
                      "defines it, against the precedent of the family")
        self.assertIn("kickoff/AFK.md", said,
                      "the pointer names a section and not the file it is in")

    def test_the_pointer_carries_the_unit_the_cap_counts_in(self):
        """A cap with an address and no unit is still read per pull request, which
        is the reading that lets a re-fired review spend a cycle it already spent."""
        said = flat(strict_form(self.text))
        self.assertRegex(said, r"per FIRING of\s+the review|per FIRING of the review",
                         "the cap is pointed at but its unit is left to the reader, and "
                         "the convenient reading is per pull request")
        self.assertRegex(said, r"never per life of this pull request",
                         "the wrong unit is not ruled out, so a reader who already has "
                         "it keeps it")


if __name__ == "__main__":
    unittest.main()
