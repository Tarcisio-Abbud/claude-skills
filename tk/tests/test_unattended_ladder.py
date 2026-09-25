#!/usr/bin/env python3
"""Doc-conformance proof for the rung an unattended session has left when the
WIP cap refuses its `tk-queue add`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHY THIS FILE EXISTS. `add` is the ONE rung the unattended ladder has: the other
two — discard and resolve-now — are judgements reserved to the user. The cap
refuses that command on a full machine, and the two documents that prescribe it
did not know it could: an unattended session was left with a `Done when` nothing
could satisfy, and the remedy the refusal prints (`done`, `cancel`) is exactly
the pair those documents reserve to the user. So each document must name what
stays open — `edit --text` and `handoff`, which write no new item — and the
commands they name must RUN at the cap.

WHAT IS PROVED: that both documents name the rung in the paragraph that names the
cap, and that the two commands work against a queue whose machine is at its cap.
WHAT IS NOT: that an unattended session reaches the paragraph. Nothing here can
see a session, and the close's own block is what carries that.

WHY THE SECOND DOCUMENT MOVED (ambiente#260). The prescription this file holds
is the one that survives an unattended package, and it left AFK.md: that file now
points at `skills/kickoff/FINDINGS.md`, which carries the park rung and is the only
document of the package still prescribing an `add`. The assertion is unchanged and
follows its subject; that AFK.md prescribes no unattended `add` of its own any more
is held from the other side, by `test_findings_destinations.py`.

VACUITY GUARD. The sentence is found by the cap's key, so deleting it from either
document empties the search and the first test fails loudly — which is how this
file was proved: each sentence was removed in turn, and the run went red, before
the pull request that added it. Searching the PARAGRAPH is what this guard has to
refuse: rung 3 names a handoff of its own, and the `handoff` assertion passed over
it with the sink gone.
"""

import os
import re
import unittest

from queue_fixture import QueueFixture, HEADER

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = {
    "reference/session-finding.md": os.path.join(HERE, os.pardir, "reference",
                                                 "session-finding.md"),
    "skills/kickoff/FINDINGS.md": os.path.join(HERE, os.pardir, "skills", "kickoff",
                                               "FINDINGS.md"),
}
WIP_KEY = "max-open-items"

ITEM = ("- [ ] **T001** — um achado anterior **Class:** AUTONOMOUS. **Effort:** S. "
        "**Criterion:** A: x. **Source:** 2026-09-04\n")


def rung_sentence(path):
    """The SENTENCE that names the cap, read across the file's line wrapping.

    NOT the paragraph. The three rungs are one Markdown paragraph, and rung 3
    writes a handoff of its own — so `assertIn("handoff", ...)` over the
    paragraph passed with the sink sentence deleted from either document, and
    proved nothing about the rung. Measured, both ways, in the pull request."""
    with open(path, encoding="utf-8") as f:
        flat = " ".join(f.read().split())
    return next((s for s in re.split(r"(?<=\.)\s+", flat) if WIP_KEY in s), "")


class TestTheDocumentsNameTheRung(unittest.TestCase):

    def test_both_documents_name_the_rung_the_cap_leaves_open(self):
        for label, path in DOCS.items():
            with self.subTest(document=label):
                para = rung_sentence(path)
                self.assertTrue(para, f"{label} never names `{WIP_KEY}`, so a session "
                                      "reading it does not know `add` can refuse")
                self.assertIn("edit", para)
                self.assertIn("--text", para)
                self.assertIn("handoff", para)


class TestTheRungRunsAtTheCap(QueueFixture):
    """The prescription is code: a rung named in prose and refused by the script
    would leave the unattended ladder with nothing at all."""

    ADD = ["tk-queue", "add", "um achado novo", "--class", "AUTONOMOUS",
           "--effort", "S", "--criterion", "A: x"]

    def setUp(self):
        super().setUp()
        d = os.path.join(self.home, ".claude", "tk")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "env"), "w", encoding="utf-8") as f:
            f.write(f"identity = alpha\nenvironments = alpha\n{WIP_KEY} = 1\n")
        with open(os.path.join(self.mem, "next-steps.md"), "w", encoding="utf-8") as f:
            f.write(HEADER + ITEM)

    def test_the_add_is_refused_and_the_named_rung_still_runs(self):
        refused = self.run_tk(self.ADD)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("against a cap of 1", refused.stderr)
        folded = self.run_tk(["tk-queue", "edit", "T001", "--text",
                              "um achado anterior, mais o achado novo"])
        self.assertEqual(folded.returncode, 0, folded.stderr)
        self.assertIn("mais o achado novo", self.body())
        briefed = self.run_tk(["tk-queue", "handoff", "T001", "--objective",
                               "fechar o achado", "--state", "nada feito",
                               "--blockers", "none"])
        self.assertEqual(briefed.returncode, 0, briefed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
