#!/usr/bin/env python3
"""Doc-conformance proof for the VERIFY step of `../skills/kickoff/AFK.md` (step 5).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

THE DEFECT (T433). A package verified every solo item on the TIP its implementer pushed, and
closed each one green. One of those pull requests was `CONFLICTING` the moment it was opened:
a sibling session had landed a commit in the same file while the run worked, and the tip the
verify approved was a tree the forge would never merge. The proof answered a question nobody
asks of a pull request — does the branch pass alone — instead of the one the merge button asks.
So the step now fixes what a solo item's FINAL TREE is: its tip merged with the fetched
`origin/main`, with the criterion and the whole suite run there.

WHY THE MERGE IS A THROWAWAY. A merge commit pushed to the item's branch to satisfy a proof
would be a tree nobody reviewed, and `../skills/merge-gate/SKILL.md`'s first verdict asks that
HEAD equal `@{u}`. The proof therefore runs in a tree nothing pushes, and a conflict found
there is REPORTED — resolving it silently is how the merge commit gets written anyway.

WHY THE LANE IS NOT HERE. A lane item's cycle merges into the lane's branch, not into `main`;
the lane's contact with `main` is its tail, which merges `origin/main` and then re-runs the
whole suite and every lane criterion on that tree. The last test below holds that half in
place: it is what makes the solo-only scope a decision rather than a gap.

THE PROSE IS WHAT IS ASSERTED. Nothing here can see an orchestrator, so what is checked is the
text the orchestrator executes, and every check ANCHORS ON CONTENT — the step's heading, its
own paragraph, the words of the rule — never on a line number, because `AFK.md` reflows under
the pruning lock at every pass.

VACUITY GUARDS. Every check below reads a slice of step 5, and a step that lost its heading or
its opening paragraph would leave each of them asserting nothing. The first test asserts the
anchors the others cut against, and it fails loudly rather than passing over an empty string.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

STEP_HEADING = re.compile(r"^## 5\. Verify every delivery\s*$", re.M)
TAIL_HEADING = re.compile(r"^### The lane's tail\s*$", re.M)
BASE = "origin/main"
SOLO_CLOSE = "tk-queue done"
# The rule itself, not the paragraph carrying it: the rule and the close share one
# paragraph, so anything anchored on the paragraph's opening places the wrong text.
RULE = re.compile(r"(?i)final tree is (?:the MERGE|its tip merged)")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def step5(text=None):
    """AFK.md's step 5, up to the next `## ` heading.

    Scoped as every doc-conformance file in this directory scopes its extraction: a
    sentence under another step must not answer for this one. The `### ` subsections —
    the lane's tail, the sweep — stay inside, since `^## ` does not match them.
    """
    text = read(AFK) if text is None else text
    m = STEP_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def tail(text=None):
    """The lane's tail, from its own heading to the next heading of any level."""
    text = step5() if text is None else text
    m = TAIL_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^#{2,3} ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def flat(text):
    """The text with its wrapping folded, so a rule split across lines reads as the
    one sentence a reader acts on."""
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(text):
    return [flat(p) for p in re.split(r"\n\s*\n", text) if p.strip()]


def merge_paragraph(text=None):
    """The paragraph of step 5 that prescribes the proof over the merge.

    Found by what it says — the base branch and the word `merge` — and cut at the
    lane's tail, whose own step 1 merges the same branch for a different tree. A
    paragraph is the unit because the rule and the conflict outcome are one thought:
    pinning them to separate anchors would let a reflow split them apart unnoticed.
    """
    text = step5() if text is None else text
    head = text[:TAIL_HEADING.search(text).start()] if TAIL_HEADING.search(text) else text
    found = [p for p in paragraphs(head)
             if BASE in p and re.search(r"(?i)\bmerge", p) and "final tree" in p]
    return found[0] if found else ""


class Step5Test(unittest.TestCase):
    def setUp(self):
        self.text = step5()
        self.said = merge_paragraph(self.text)

    def test_the_step_and_its_merge_paragraph_are_still_there(self):
        """The anchors every check below cuts against."""
        self.assertTrue(STEP_HEADING.search(read(AFK)),
                        "AFK.md has no `## 5. Verify every delivery` — re-anchor this file")
        self.assertTrue(self.text.strip(), "step 5 is empty")
        self.assertTrue(
            self.said,
            "no paragraph of step 5 names `origin/main`, a merge and the final tree "
            "together — the solo proof has gone back to the tip, and a pull request "
            "conflicting with `main` closes green again")

    def test_the_solo_final_tree_is_the_merge_with_the_base(self):
        """The rule proper. The tip alone is not what the forge merges, and a proof
        run on it answers a question nobody asks of a pull request."""
        self.assertRegex(
            self.said, RULE,
            f"step 5 no longer fixes a solo item's final tree as the merge with "
            f"`{BASE}`: {self.said}")
        self.assertRegex(
            self.said, r"(?i)never the tip alone|not the tip alone",
            "step 5 states the merge without ruling the tip out — a caller that reads "
            "it as one more option keeps proving the tip")

    def test_both_the_criterion_and_the_whole_suite_run_on_that_tree(self):
        """A clean merge is not a green one: the conflict git reports is the cheap
        half, and what the merge breaks silently is caught by the suite or by
        nothing."""
        for needle, why in (("criterion", "the item's own promise goes unproved there"),
                            ("suite", "a merge that breaks a sibling's test ships green")):
            with self.subTest(needle=needle):
                self.assertRegex(
                    self.said, rf"(?i)\b{needle}",
                    f"step 5's merge paragraph never names the {needle} — {why}: "
                    f"{self.said}")
        self.assertRegex(
            self.said, r"(?i)whole suite",
            "the paragraph names a suite without asking for the WHOLE one, and a "
            "partial run is what a conflicting merge slips through")

    def test_the_merge_is_a_throwaway_that_is_never_pushed(self):
        """A merge commit pushed to satisfy a proof is a tree nobody reviewed, and
        `merge-gate`'s first verdict asks that HEAD equal `@{u}`."""
        self.assertRegex(
            self.said, r"(?i)throwaway|scratch|discard",
            f"step 5 asks for the merge without saying the tree is a throwaway — the "
            f"proof then writes a merge commit into the item's branch: {self.said}")
        self.assertRegex(
            self.said, r"(?i)nothing pushes|never pushed|not pushed|pushes nothing",
            "step 5 does not say the merge is never pushed, which is the whole "
            "difference between a proof and a second merge of `main`")

    def test_a_conflict_there_is_reported_and_not_resolved(self):
        """Resolving it inside the verify is how the unreviewed merge commit gets
        written anyway, and it hides from the report the one fact the item owes."""
        self.assertRegex(
            self.said, r"(?i)not a merge to resolve|never a merge to resolve",
            f"step 5 does not forbid resolving the conflict it finds: {self.said}")
        self.assertIn(
            "DECISION", self.said,
            "step 5 finds the conflict and names no outcome for the item — a finding "
            "with no rung leaves the package silent about it")

    def test_the_proof_stands_before_the_item_closes(self):
        """Its whole value is the ORDER: a merge proved after `done` proves nothing
        the queue can still act on.

        Placed by the RULE and never by the paragraph that carries it. The rule and
        the close live in ONE paragraph of step 5, so a comparison anchored on that
        paragraph's first characters measures where the paragraph starts — true
        whatever the order inside it, and the check asserts nothing.
        """
        head = flat(self.text)
        rule = RULE.search(head)
        self.assertTrue(rule, "step 5 no longer carries the rule — see the anchor test "
                              "above; without this guard the comparison below has no "
                              "position to place")
        self.assertIn(SOLO_CLOSE, head,
                      f"step 5 no longer closes an item with `{SOLO_CLOSE}` — the "
                      "ordering check below has nothing to place the proof against")
        self.assertLess(
            rule.start(), head.index(SOLO_CLOSE),
            "the merge proof is prescribed after the close — the item leaves the queue "
            "before anything asks whether its tree merges")

    def test_the_step_s_done_when_asks_for_the_merge_proof(self):
        """A rule absent from the step's own checklist is a rule the orchestrator
        reports `Done` without."""
        done = [p for p in paragraphs(self.text) if p.startswith("**Done when:**")]
        self.assertTrue(done, "step 5 has no `**Done when:**` paragraph")
        self.assertRegex(
            " ".join(done), rf"(?i)merge with `{re.escape(BASE)}`|merged with `{re.escape(BASE)}`",
            f"step 5's `Done when` never names the merge with `{BASE}`: {done}")

    def test_the_lane_keeps_its_own_merge_of_the_base_at_the_tail(self):
        """What makes the rule above SOLO-only rather than a hole. A lane item merges
        into the lane's branch; the lane meets `main` once, at its tail. Lose that,
        and no lane item is ever proved against the branch it ships into."""
        lane = tail()
        self.assertTrue(lane, "AFK.md has no `### The lane's tail` — the solo-only "
                              "scope of the rule above rests on this section existing")
        self.assertRegex(
            lane, rf"(?i)merge `{re.escape(BASE)}`|merge the fetched `{re.escape(BASE)}`",
            f"the lane's tail no longer merges `{BASE}` — the lane now reaches its "
            f"pull request without ever meeting the branch it merges into")
        self.assertRegex(
            flat(lane), r"(?i)whole suite and every lane criterion",
            "the tail merges the base and no longer re-runs the whole suite and every "
            "lane criterion on that tree — the lane's half of this rule is gone")


if __name__ == "__main__":
    unittest.main()
