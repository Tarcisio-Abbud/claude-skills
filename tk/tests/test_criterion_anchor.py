#!/usr/bin/env python3
"""One rule, read at the three sites that need it — the criterion's ANCHOR.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

`../skills/verify/SKILL.md`, *The anchor outlives the tree*, says a criterion anchors on
content and never on a line number or an absolute count. The rule was written where the
criterion is VERIFIED and nowhere near where it is WRITTEN, which left it half a rule
(T325 delivered the first half; this file holds what T329 finished):

- the outcome table's `Rotten criterion` had two shapes, and an anchor on a moving target
  was neither of them — it executes, and it proves the tree's shape rather than the
  promise, so a verifier reading the two shapes had nowhere to put it;
- no command reached the rule from where the wording is still cheap to change. `AFK.md`'s
  audit step reads every ticket's criterion before a line of code is written, and
  `../reference/queue.md` is what a session reads about the field — neither pointed at it.

WHAT IS ASSERTED IS THE PROSE, in three files, and the checks are deliberately about the
POINTER and not about a paraphrase: a site that restates the rule is a second copy of it,
and the next edit moves one of the two. Each file's slice is guarded against vacuity first,
because a heading that moved would leave the check that cuts on it reading an empty string.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFY = os.path.join(HERE, os.pardir, "skills", "verify", "SKILL.md")
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")
QUEUE = os.path.join(HERE, os.pardir, "reference", "queue.md")

# The section every site must reach, spelled as the sites spell it.
SECTION = "The anchor outlives the tree"
ROTTEN = re.compile(r"^## A rotten criterion has (\w+) shapes\s*$", re.M)
AUDIT_STEP = re.compile(r"^## \d+\. Audit\b.*$", re.M)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(text, heading):
    """From `heading` to the next `## `, flattened."""
    m = heading.search(text) if hasattr(heading, "search") else None
    if m is None:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return flat(rest[:nxt.start()] if nxt else rest)


def sentence_with(text, needle):
    return [s for s in re.split(r"(?<=\.)\s+", flat(text)) if needle in s]


class TheRuleItself(unittest.TestCase):
    """`verify/SKILL.md` — where the anchor rule and the outcome both live."""

    def setUp(self):
        self.text = read(VERIFY)

    def test_the_two_slices_this_class_cuts_are_still_there(self):
        self.assertIn(f"## {SECTION}", self.text,
                      f"verify/SKILL.md has no `## {SECTION}` — every pointer asserted in "
                      "this file names a section that is gone")
        self.assertTrue(ROTTEN.search(self.text),
                        "verify/SKILL.md has no `## A rotten criterion has N shapes`")

    def test_the_rotten_criterion_has_three_shapes(self):
        """The heading counts, so it is read: a third bullet under a heading that
        still says two is a list whose own summary contradicts it."""
        self.assertEqual(ROTTEN.search(self.text).group(1), "three",
                         "the heading names a number of shapes the section does not carry")

    def test_the_third_shape_is_the_criterion_anchored_on_a_moving_target(self):
        said = section(self.text, ROTTEN)
        self.assertTrue(said, "the rotten-criterion section is empty")
        self.assertIn("moving target", said,
                      "the rotten shapes do not include the anchor on a moving target, so "
                      "a criterion that measures the tree's shape has no outcome to take "
                      "and is reported as a pass or a failure of the delivery")
        self.assertIn(SECTION, said,
                      "the third shape names no rule, so what counts as a moving target is "
                      "the verifier's guess")


class TheSitesThatReachIt(unittest.TestCase):
    """The two places a criterion is WRITTEN, and neither could reach the rule."""

    def test_the_audit_step_points_at_the_rule(self):
        text = read(AFK)
        self.assertTrue(AUDIT_STEP.search(text),
                        "AFK.md has no numbered Audit step — re-anchor this check")
        said = section(text, AUDIT_STEP)
        self.assertIn("--criterion", said,
                      "the audit step never names the criterion, so the lens that reads "
                      "every ticket before a line of code is written has no rule to read "
                      "it against")
        self.assertIn(SECTION, said,
                      f"the audit step does not point at *{SECTION}*: the one moment the "
                      "wording is still cheap to change is the one moment nobody checks "
                      "the anchor")

    def test_the_queue_contract_points_at_the_rule(self):
        said = sentence_with(read(QUEUE), "--criterion")
        self.assertTrue(said, "queue.md never names `--criterion` — re-anchor this check")
        self.assertIn(SECTION, " ".join(said),
                      f"no sentence naming `--criterion` reaches *{SECTION}*. The file "
                      "carries what the `--help` texts do not confess, and what a "
                      "criterion may anchor on is exactly that")

    def test_neither_site_restates_the_rule(self):
        """A pointer, not a copy. Two copies of one rule drift on the first edit,
        and `slice-rules.md` names that as the defect to derive away."""
        for name, path in (("AFK.md", AFK), ("queue.md", QUEUE)):
            with self.subTest(file=name):
                self.assertNotIn("anchors on content", flat(read(path)),
                                 "the site restates the anchor rule instead of pointing "
                                 "at it, so verify/SKILL.md is no longer its one source")


if __name__ == "__main__":
    unittest.main()
