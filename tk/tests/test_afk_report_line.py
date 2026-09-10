#!/usr/bin/env python3
"""Doc-conformance proof that the afk report declares whether the wrap-up ran (T391).

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Born from a real skip: step 7 of `../skills/kickoff/AFK.md` ("Chain the afk wrap-up") ran
silently missing on 2026-09-10, and nobody noticed until the user asked
(`afk-gen6-workflow-medido` in auto-memory). `../skills/kickoff/AFK.md` prescribes the line
and `../skills/wrap-up/REPORT.md` prescribes writing it into the closing report; both must
carry the literal `wrap-up afk:` line so a cold reader of the report can tell a legitimate
skip (a concurrent guard, the quota wall) from an outright one.

Anchored on content, per `../skills/verify/SKILL.md` "The anchor outlives the tree": a grep
of the sentence, not a line number or a count.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AFK = os.path.join(HERE, os.pardir, "skills", "kickoff", "AFK.md")
REPORT = os.path.join(HERE, os.pardir, "skills", "wrap-up", "REPORT.md")

LINE = "wrap-up afk:"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def flat(text):
    """Whitespace-normalised, so a wrapped line does not split a phrase this
    grep looks for — the anchor is the sentence, never how the file reflows it."""
    return re.sub(r"\s+", " ", text)


class AfkReportLineTest(unittest.TestCase):
    def test_afk_prescribes_the_line(self):
        text = read(AFK)
        self.assertIn("## 7. Chain the afk wrap-up", text,
                      "AFK.md lost step 7 — re-anchor this test")
        self.assertIn(LINE, flat(text),
                      "AFK.md's step 7 no longer prescribes the `wrap-up afk:` line, so "
                      "a skipped wrap-up can again go unreported")

    def test_report_prescribes_the_line(self):
        text = read(REPORT)
        self.assertIn(LINE, flat(text),
                      "REPORT.md no longer prescribes the `wrap-up afk:` line in the "
                      "closing report — a cold reader has no way to tell a legitimate "
                      "skip from an outright one")

    def test_both_shapes_are_named(self):
        """Both outcomes, not just the positive one — a doc that only prescribes
        `rodou` says nothing about the legitimate-skip half this item was born for."""
        for path, name in ((AFK, "AFK.md"), (REPORT, "REPORT.md")):
            text = flat(read(path))
            with self.subTest(file=name):
                self.assertIn("rodou", text, f"{name} never prescribes the ran outcome")
                self.assertIn("nao rodou", text,
                              f"{name} never prescribes the skipped outcome with its reason")


if __name__ == "__main__":
    unittest.main()
