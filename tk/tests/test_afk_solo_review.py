#!/usr/bin/env python3
"""Doc-conformance proof that an afk package's SOLO item takes the cold review.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

THE DEFECT. `../skills/kickoff/AFK.md` step 5 closed an approved solo item on verify alone:
`tk-queue done` sat in the paragraph that proves the item over its merge with `origin/main`,
and the cold review of `REVIEW-CONTRACT.md` was scoped to a lane holding its own pull request.
So a solo pull request reached the close with no two-axis review (Standards + Spec), which the
site's project rules require of every delivered code change. One package shipped four of them.

THE DESIGN PINNED HERE. The solo path dispatches the `cold-reviewer` role it already had for
lanes, after verify approves and before `done`, and the reviewer's comment on the pull request
is what lets the item leave the queue. The merge gate's strict form reads that comment as
verdict 2, so a solo pull request without it cannot merge unattended. A "review, then merge"
close-menu option was the alternative; the unattended close runs with no menu, so that option
would defer the merge without ever producing the review.

THE PROSE IS WHAT IS ASSERTED, anchored on content — headings, the words of the rule — never
on line numbers, because these files reflow under the pruning lock.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
AFK = os.path.join(ROOT, "skills", "kickoff", "AFK.md")
REVIEW = os.path.join(ROOT, "skills", "kickoff", "REVIEW-CONTRACT.md")
GATE = os.path.join(ROOT, "skills", "merge-gate", "SKILL.md")
POLICY = os.path.join(ROOT, "reference", "subagent-policy.md")
CONTRACT = os.path.join(ROOT, "bin", "tk-contract")

STEP_HEADING = re.compile(r"^## 5\. Verify every delivery\s*$", re.M)
TAIL_HEADING = re.compile(r"^### The lane's tail\s*$", re.M)
SOLO_CLOSE = "tk-queue done"
FINAL_TREE = re.compile(r"(?i)final tree is (?:the MERGE|its tip merged)")
SOLO_REVIEW = re.compile(r"(?i)solo item's cold review runs after verify approves it "
                         r"and before its `done`")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(text):
    return [flat(p) for p in re.split(r"\n\s*\n", text) if p.strip()]


def step5_head():
    """Step 5 up to the lane's tail: the part that governs solo items."""
    text = read(AFK)
    m = STEP_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    rest = rest[:nxt.start()] if nxt else rest
    tail = TAIL_HEADING.search(rest)
    return rest[:tail.start()] if tail else rest


def step5_done_when():
    text = read(AFK)
    m = STEP_HEADING.search(text)
    rest = text[m.end():] if m else ""
    nxt = re.search(r"^## ", rest, re.M)
    rest = rest[:nxt.start()] if nxt else rest
    return " ".join(p for p in paragraphs(rest) if p.startswith("**Done when:**"))


class TheSoloPathTakesTheColdReview(unittest.TestCase):
    def setUp(self):
        self.head = step5_head()
        self.flat = flat(self.head)

    def test_the_anchors_are_still_there(self):
        self.assertTrue(self.head.strip(), "AFK.md lost `## 5. Verify every delivery`")
        self.assertRegex(self.flat, FINAL_TREE,
                         "step 5 lost the solo final-tree rule this file places the "
                         "review against")

    def test_a_solo_pull_request_takes_the_review_contract(self):
        self.assertRegex(
            self.flat,
            r"(?i)solo item's pull request takes the cold review of `REVIEW-CONTRACT\.md`",
            "step 5 scopes the cold review to lanes again — a solo pull request reaches "
            "the close with no two-axis review")

    def test_the_proof_paragraph_no_longer_closes_the_item(self):
        """The defect's own shape: `done` beside the verify proof, before any review."""
        proof = [p for p in paragraphs(self.head) if FINAL_TREE.search(p)]
        self.assertTrue(proof, "no paragraph carries the final-tree rule")
        self.assertNotIn(SOLO_CLOSE, proof[0],
                         "the verify paragraph closes the solo item again, before its "
                         "cold review runs")

    def test_the_review_comes_before_the_solo_close(self):
        review = SOLO_REVIEW.search(self.flat)
        self.assertTrue(review, "step 5 no longer orders the solo cold review between "
                                "verify and `done`")
        close = self.flat.find(SOLO_CLOSE, review.end())
        self.assertNotEqual(close, -1, "no `tk-queue done` follows the solo review rule")
        self.assertEqual(self.flat.find(SOLO_CLOSE), close,
                         "a `tk-queue done` for the solo item precedes its cold review")

    def test_the_close_waits_on_the_reviewer_s_comment(self):
        para = [p for p in paragraphs(self.head) if SOLO_REVIEW.search(p)]
        self.assertTrue(para, "the solo review paragraph is gone")
        said = para[0]
        self.assertRegex(said, r"(?i)reviewer's comment",
                         "the close no longer names the comment it waits on")
        self.assertRegex(said, r"(?i)no comment, the item stays open as a DECISION",
                         "a solo item with no review comment has no outcome named")
        self.assertRegex(said, r"(?i)whole suite.*merged with `origin/main`",
                         "a reviewer's fix ships without the criterion and the suite "
                         "re-run over the merge")

    def test_done_when_asks_for_the_review(self):
        self.assertRegex(step5_done_when(), r"(?i)cold reviewer's comment",
                         "step 5's `Done when` closes a solo item without its review")


class TheSiblingsAgree(unittest.TestCase):
    def test_the_review_contract_admits_a_solo_pull_request(self):
        opening = flat(read(REVIEW).split("## Inputs")[0])
        self.assertRegex(opening, r"(?i)solo item's pull request",
                         "REVIEW-CONTRACT.md still reaches only lanes")

    def test_the_gate_reads_the_comment_as_verdict_2(self):
        gate = flat(read(GATE))
        self.assertRegex(
            gate, r"(?i)solo pull request, the review flow is the cold reviewer's comment"
                  r".*no such comment, verdict 2 is red",
            "the strict form can merge a solo pull request no reviewer read")

    def test_the_role_row_and_its_generated_contract_name_the_solo_item(self):
        row = [line for line in read(POLICY).splitlines()
               if line.startswith("| cold-reviewer |")]
        self.assertEqual(len(row), 1, "subagent-policy.md has no single cold-reviewer row")
        self.assertIn("solo item", row[0])
        # A throwaway HOME with a fixture site file: the real `~/.claude/tk/env` would make
        # the answer depend on whose machine runs the suite.
        home = tempfile.mkdtemp(prefix="tk-solo-review.")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        os.makedirs(os.path.join(home, ".claude", "tk"))
        with open(os.path.join(home, ".claude", "tk", "env"), "w", encoding="utf-8") as f:
            f.write("identity = alpha\nenvironments = alpha\nmax-local-subagents = 3\n"
                    "max-local-opus = 2\nmax-cloud-subagents = 2\n")
        run = subprocess.run([sys.executable, CONTRACT, "--role", "cold-reviewer",
                              "--policy", POLICY],
                             capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, HOME=home))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("solo item", run.stdout,
                      "the generated contract block does not carry the solo scope")


if __name__ == "__main__":
    unittest.main()
