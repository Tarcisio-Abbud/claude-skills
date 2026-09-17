#!/usr/bin/env python3
"""Regression lock: `second-opinion` pins `effort: high` in its FRONTMATTER.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHAT IS LOCKED. Two files have to agree, or the skill promises a fresh verdict at an
effort nothing sets:

- `tk/agents/second-opinion.md` carries `effort: high` in its frontmatter — the only
  place that setting has an effect;
- `tk/skills/second-opinion/SKILL.md` step 2 attributes the pin to that DEFINITION, and
  the deviation line it prescribes says `effort high` because the run really was.

WHY THE LOCK EXISTS. T401 (2026-09-14) read the absent `effort` parameter on the `Agent`
tool as "effort cannot be pinned", deleted the frontmatter key, rewrote step 2 to say the
subagent inherits the session's effort, and landed a test asserting that absence. The
premise was wrong. The official subagent documentation
(https://code.claude.com/docs/en/sub-agents, frontmatter table) reads, verbatim:

    | `effort` | No | Effort level when this subagent is active. Overrides the session
    effort level. Default: inherits from session. Options: `low`, `medium`, `high`,
    `xhigh`, `max`; available levels depend on the model |

So the field is honoured, and it overrides the session; what does not exist is a per-call
`effort` argument on the dispatch. PR claude-skills#115 was closed without merging and the
T401 change never reached `main`, which is why this module asserts the pin rather than
inverting an existing file. `test_step_2_does_not_repeat_the_T401_claim` is the tombstone:
it fails if the retracted wording comes back.

VACUITY GUARD. Every check cuts a slice — the frontmatter block, step 2, the deviation
line — and a slice whose anchor moved would be an empty string that passes every
assertion. Each helper asserts its slice non-empty before any claim is made about it.

WHAT IS NOT PROVED HERE. That the harness actually runs the subagent at high effort: a
live dispatch is not a fixture, and the documentation quoted above is the whole evidence
that the key takes effect. This module proves the two files say the same thing about it.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, os.pardir)
SKILL = os.path.join(PLUGIN, "skills", "second-opinion", "SKILL.md")
AGENT = os.path.join(PLUGIN, "agents", "second-opinion.md")

# The frontmatter key, on its own line. `grep -c 'effort: high'` over the agent file is
# the item's own acceptance criterion, so the same spelling is what is asserted.
EFFORT_KEY = re.compile(r"^effort:[ \t]+high[ \t]*$", re.MULTILINE)

# The claim T401 put in step 2 and this slice retracted.
T401_CLAIM = re.compile(r"no\s+`?effort`?\s+(field|parameter)", re.IGNORECASE)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter(case, text, path):
    """The YAML block between the first two `---` fences, asserted non-empty."""
    case.assertTrue(text.startswith("---\n"),
                    "%s no longer opens with a frontmatter fence" % path)
    parts = text.split("---", 2)
    case.assertEqual(len(parts), 3, "%s has no closing frontmatter fence" % path)
    block = parts[1].strip()
    case.assertTrue(block, "%s frontmatter block is empty" % path)
    return block


class TestAgentDefinitionPinsEffort(unittest.TestCase):
    def setUp(self):
        self.body = read(AGENT)

    def test_frontmatter_declares_effort_high(self):
        """The one place the setting has an effect: the subagent's own definition."""
        block = frontmatter(self, self.body, AGENT)
        self.assertRegex(block, EFFORT_KEY,
                         "tk/agents/second-opinion.md frontmatter no longer pins "
                         "`effort: high`; the docs say the field overrides the session")

    def test_the_pin_is_declared_exactly_once(self):
        """`grep -c 'effort: high' tk/agents/second-opinion.md` = 1 is the item's
        criterion, and a second copy in the body would satisfy the grep while the
        frontmatter lost the key."""
        self.assertEqual(len(EFFORT_KEY.findall(self.body)), 1,
                         "expected exactly one `effort: high` line in "
                         "tk/agents/second-opinion.md")

    def test_the_model_pin_sits_beside_it(self):
        """Step 2 names both pins in one breath; a `model` key that drifted would leave
        half that sentence unbacked."""
        block = frontmatter(self, self.body, AGENT)
        self.assertRegex(block, re.compile(r"^model:[ \t]+fable[ \t]*$", re.MULTILINE),
                         "tk/agents/second-opinion.md frontmatter no longer pins "
                         "`model: fable`")


class TestSkillAttributesThePinToTheDefinition(unittest.TestCase):
    def setUp(self):
        self.body = read(SKILL)

    def step_2(self):
        """Step 2 with its line breaks collapsed, asserted non-empty."""
        found = re.search(r"^2\. \*\*Dispatch\*\*.*?(?=^3\. )",
                          self.body, re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(found, "step 2's heading moved — update this anchor")
        text = " ".join(found.group(0).split())
        self.assertTrue(text, "step 2 sliced empty")
        return text

    def test_step_2_says_the_definition_pins_effort_high(self):
        """The attribution is the substance: the pin lives in the frontmatter, so the
        sentence that claims it must be about the definition, not about the dispatch."""
        self.assertRegex(self.step_2(), r"definition\s+pins[^.]*`effort: high`",
                         "step 2 no longer attributes `effort: high` to the subagent's "
                         "own definition")

    def test_step_2_does_not_repeat_the_T401_claim(self):
        """Tombstone for the retracted wording: the `Agent` tool has no `effort`
        argument, but the frontmatter field is honoured all the same."""
        self.assertNotRegex(self.step_2(), T401_CLAIM,
                            "step 2 is back to denying the `effort` field; the docs say "
                            "it overrides the session effort level")

    def test_the_deviation_line_reports_the_effort_it_ran_at(self):
        """The example line is copy-pasted verbatim into every report the skill
        produces, so it has to name the effort the frontmatter actually pinned."""
        found = re.search(r"`second-opinion: none.*?/tk:second-opinion`", self.body)
        self.assertIsNotNone(found, "the deviation-line example moved or was reworded")
        self.assertIn("effort high", found.group(0),
                      "the deviation line no longer reports the pinned effort")


if __name__ == "__main__":
    unittest.main()
