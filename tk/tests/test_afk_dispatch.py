#!/usr/bin/env python3
"""Doc-conformance proof for the DISPATCH step of `../skills/kickoff/AFK.md` (step 3).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

What is asked of that step here is one prescription of it, born of a defect measured on a real
package:

- **the single exploration** (T176). Every implementer of a lane re-read the same base tree,
  because the prompt carried the item's distilled contract and nothing about the code around
  it. The step now explores ONCE, before the first ticket goes out, and hands every run the
  path of the notes. Two properties: the notes live OUTSIDE the repository — a path inside a
  worktree is committed by the lane and reviewed by the tail — and the exploration stands
  BEFORE the dispatch, which is the whole of its value.

WHAT IS ASSERTED IS THE PROSE, not a run. Nothing here can see an orchestrator, so what this
file can hold is the text the orchestrator executes — the recipe carrying its flag, the
sentence standing in the right place. The runs themselves are held by the package's own
report block, as `AUDIT.md`'s is.

VACUITY GUARDS. Every check below reads a slice of step 3, and a step that lost its heading
or its dispatch paragraph would leave each of them iterating nothing. The first test asserts
the anchors the others cut against, and it fails loudly rather than passing over an empty
string.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")

STEP_HEADING = re.compile(r"^## 3\. Claim, then dispatch\s*$", re.M)
# where the lane stops preparing and starts dispatching tickets
DISPATCH_ANCHOR = "The lane is serial"
NOTES = "<notes dir>"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def step3(text=None):
    """AFK.md's step 3, up to the next `## ` heading.

    Scoped for the reason every doc-conformance file in this directory scopes its
    extraction: a sentence under another step must not answer for this one.
    """
    text = read(AFK) if text is None else text
    m = STEP_HEADING.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def flat(text):
    """The step with its wrapping folded, so a sentence split across lines reads
    as the one sentence a reader acts on."""
    return re.sub(r"\s+", " ", text)


def sentences_with(text, needle):
    return [s for s in re.split(r"(?<=\.)\s+", flat(text)) if needle in s]


class Step3Test(unittest.TestCase):
    def setUp(self):
        self.text = step3()

    def test_the_step_and_its_dispatch_paragraph_are_still_there(self):
        """The anchors every check below cuts against."""
        self.assertTrue(STEP_HEADING.search(read(AFK)),
                        "AFK.md has no `## 3. Claim, then dispatch` — re-anchor this file")
        self.assertTrue(self.text.strip(), "step 3 is empty")
        self.assertIn(DISPATCH_ANCHOR, self.text,
                      f"step 3 no longer says `{DISPATCH_ANCHOR}` — the ordering check "
                      "below would have nothing to place the exploration against")

    # --- T176: one exploration, before the first ticket ----------------------

    def test_the_step_prescribes_one_exploration_and_hands_its_notes_to_every_run(self):
        said = sentences_with(self.text, NOTES)
        self.assertTrue(said,
                        f"step 3 never names `{NOTES}` — nothing tells the orchestrator "
                        "where the exploration's notes go, and every implementer of the "
                        "lane re-reads the same base tree at its own cost")
        self.assertGreaterEqual(
            len(said), 2,
            f"`{NOTES}` is named once. It has two jobs — the exploration WRITES it and "
            f"every run's prompt CARRIES it — and one mention leaves the notes either "
            f"unwritten or undelivered: {said}")

    def test_the_notes_are_written_outside_the_repository(self):
        """A path inside a worktree is committed by the lane and reviewed by the
        tail: the notes are the session's, not the pull request's."""
        said = " ".join(sentences_with(self.text, NOTES))
        self.assertRegex(said, r"(?i)outside the repositor",
                         "step 3 does not say the exploration's notes live outside the "
                         "repository — inside one they are committed by the lane and "
                         "read by the tail's review as part of the diff")

    def test_the_exploration_stands_before_the_first_ticket_goes_out(self):
        """Its whole value is the ORDER: notes written after the first dispatch
        reach nobody, and the run that would have used them has already read the
        tree itself."""
        first_note = flat(self.text).index(NOTES)
        dispatch = flat(self.text).index(DISPATCH_ANCHOR)
        self.assertLess(first_note, dispatch,
                        "the exploration is prescribed after the lane starts dispatching "
                        "tickets — the first implementer explores the base anyway, which "
                        "is the defect the step was written against")


if __name__ == "__main__":
    unittest.main()
