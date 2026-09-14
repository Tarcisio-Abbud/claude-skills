#!/usr/bin/env python3
"""Regression lock: `second-opinion` no longer asks the `Agent` tool for `effort`.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

Measured 2026-09-14 (T401): the `Agent` tool has no `effort` parameter, so a
dispatched subagent inherits the DISPATCHING SESSION's effort regardless of what
a subagent definition's frontmatter says. `tk/skills/second-opinion/SKILL.md`
asserted the opposite twice — step 2 said the dispatch "pins... `effort: high`",
and the deviation line closed with the unearned "effort high" — and the
subagent's own definition, `tk/agents/second-opinion.md`, carried a matching
`effort: high` frontmatter key that the dispatcher never honours either.

This is a narrow prose lock, not a re-run of `docs/prune/second-opinion-report.md`'s
open note: that note is history, keyed to a prior commit, and stays as written.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
SKILL = os.path.join(PLUGIN, "skills", "second-opinion", "SKILL.md")
AGENT = os.path.join(PLUGIN, "agents", "second-opinion.md")

# A claim that the dispatch fixes effort at `high` — the false claim T401 removed.
PINNED_EFFORT = re.compile(r"effort[:\s]+`?high`?", re.IGNORECASE)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestSkillDoesNotClaimPinnedEffort(unittest.TestCase):
    def setUp(self):
        self.body = read(SKILL)

    def test_step_2_does_not_say_effort_is_pinned(self):
        """Step 2 names what `Agent` actually pins (`model`) and says effort is
        inherited — not a second `effort: high` claimed alongside it."""
        step2 = re.search(r"2\. \*\*Dispatch\*\*.*?(?=\n\n3\.)", self.body, re.DOTALL)
        self.assertIsNotNone(step2, "step 2 heading moved — update this test's anchor")
        self.assertNotRegex(step2.group(0), PINNED_EFFORT,
                             "step 2 still claims the Agent dispatch pins effort at "
                             "high; it has no effort parameter (T401)")
        self.assertIn("no `effort` field", step2.group(0),
                       "step 2 should say the Agent tool has no effort field")

    def test_deviation_line_does_not_assert_an_unfixed_effort(self):
        """The example deviation line is copy-pasted verbatim by every run, so a
        false 'effort high' there ships in every report the skill produces."""
        line = re.search(r"`second-opinion: none.*?/tk:second-opinion`", self.body)
        self.assertIsNotNone(line, "the deviation-line example moved or was reworded")
        self.assertNotRegex(line.group(0), PINNED_EFFORT,
                             "the deviation line still asserts an unfixed 'effort high'")


class TestAgentDefinitionDoesNotPinEffort(unittest.TestCase):
    def test_frontmatter_carries_no_effort_key(self):
        """The `Agent` tool ignores this key on dispatch (T401); keeping it invites
        the next reader to believe it takes effect."""
        frontmatter = read(AGENT).split("---")[1]
        self.assertNotIn("effort", frontmatter,
                          "tk/agents/second-opinion.md frontmatter still declares "
                          "`effort`, which the Agent tool does not honour")


if __name__ == "__main__":
    unittest.main()
