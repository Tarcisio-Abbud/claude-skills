#!/usr/bin/env python3
"""The `tk` manifests must name the skills that exist, and only those.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)
Proved by: python3 tk/tests/mutations_manifests.py

WHY THIS EXISTS. A skill is advertised in two files that nothing generates from
`tk/skills/` — `tk/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
Only the memory of whoever edits kept the three in step, and it failed twice on
2026-08-28:

  - `/tk:review` shipped and never reached `marketplace.json`; the gap outlived several
    merges and was closed by hand in `a0282cb`, noticed only because a rebase happened
    to put the line under someone's eyes;
  - `#48` added the `prune` skill on one branch while `#49` added `fleet` on another,
    both rewriting the same `description` from the same base. Resolving that conflict by
    taking either side would have dropped the other's skill with nothing going red.

The failure is quiet in both directions and expensive in one: a skill absent from a
description is a skill nobody discovers, and the file still parses, still merges, still
passes every other test.

THE ANCHOR IS THE POINT. An earlier draft of this suite matched the bare word
(`\\bprune\\b`) against the description's free prose, and was vacuous against the very
defect above: deleting a skill's clause while a neighbouring sentence still happened to
use the word left the suite green. Every skill here is an ordinary English word, so each
was one prose edit away from that. Both manifests are matched on the form they actually
advertise in — `<name> (` in the plugin description, `/tk:<name>` in the marketplace one —
and each match refuses a longer neighbour, so a future `review-fast` cannot satisfy the
row for `review`.

WHAT THIS DOES NOT COVER, deliberately:

  - **Wording.** A description naming every skill and describing each one wrongly passes.
    Membership is verifiable; prose is a reader's judgement.
  - **`README.md`**, which advertises the same nine skills in a table and was edited by
    both #48 and #49. It is a third surface with a third format, and it is unguarded.
  - **The sibling plugins** in `marketplace.json` (`tk-cowork`, `asr`, `plugin-drift`).
    They do not share this convention — `asr` and `plugin-drift` never name their single
    skill at all, describing the plugin instead — so the same rule would not merely be
    wider, it would be wrong. Guarding them needs a rule of their own.
"""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
PLUGIN = os.path.join(ROOT, "tk", ".claude-plugin", "plugin.json")
MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
SKILLS_DIR = os.path.join(ROOT, "tk", "skills")

# A skill is advertised as a clause `<name> (…)` in the plugin description, and as
# `/tk:<name>` in the marketplace one. Both refuse a longer name that merely starts the
# same way, which is what makes them anchors rather than substring probes.
PLUGIN_CLAUSE = r"(?<![a-z0-9-])%s \("
MARKETPLACE_REF = r"/tk:%s(?![a-z0-9-])"


def skills_on_disk():
    """Every skill directory, i.e. one holding a SKILL.md."""
    return sorted(
        name
        for name in os.listdir(SKILLS_DIR)
        if os.path.isfile(os.path.join(SKILLS_DIR, name, "SKILL.md"))
    )


def plugin_description():
    with open(PLUGIN, encoding="utf-8") as fh:
        return json.load(fh)["description"]


def tk_entries():
    """Every `tk` entry of the marketplace — a list, so its length can be asserted."""
    with open(MARKETPLACE, encoding="utf-8") as fh:
        return [e for e in json.load(fh)["plugins"] if e["name"] == "tk"]


def marketplace_description():
    return tk_entries()[0]["description"]


class TestTheGuardHasSomethingToCheck(unittest.TestCase):
    """A guard that silently checks nothing is worse than no guard at all."""

    def test_there_are_skills_on_disk(self):
        self.assertTrue(skills_on_disk(), f"no skill directory found under {SKILLS_DIR}")

    def test_the_marketplace_carries_exactly_one_tk_entry(self):
        # Not a bare `assert`: that is stripped under `python3 -O`, and a second `tk`
        # entry would then be picked silently by whichever came first.
        self.assertEqual(
            len(tk_entries()), 1,
            "the marketplace must carry exactly one `tk` entry; the description of a "
            "second would drift unchecked",
        )


class TestPluginManifest(unittest.TestCase):
    """`plugin.json` advertises each skill as a clause `<name> (…)`."""

    def test_every_skill_is_named(self):
        description = plugin_description()
        for skill in skills_on_disk():
            with self.subTest(skill=skill):
                self.assertRegex(
                    description, PLUGIN_CLAUSE % re.escape(skill),
                    f"tk/.claude-plugin/plugin.json advertises no `{skill} (…)` clause",
                )

    def test_names_no_skill_that_does_not_exist(self):
        """A clause naming no directory sends a reader to a skill that is not there."""
        advertised = set(re.findall(r"(?<![a-z0-9-])([a-z][a-z0-9-]*) \(",
                                    plugin_description()))
        for name in sorted(advertised - set(skills_on_disk())):
            with self.subTest(skill=name):
                self.fail(
                    f"plugin.json has a `{name} (…)` clause with no "
                    f"tk/skills/{name}/SKILL.md behind it — the description's clause "
                    f"list is one clause per skill, so a parenthetical that is not a "
                    f"skill belongs outside it"
                )


class TestMarketplaceManifest(unittest.TestCase):
    """`marketplace.json` advertises each skill as `/tk:<name>`."""

    def test_every_skill_is_named(self):
        description = marketplace_description()
        for skill in skills_on_disk():
            with self.subTest(skill=skill):
                self.assertRegex(
                    description, MARKETPLACE_REF % re.escape(skill),
                    f".claude-plugin/marketplace.json does not name /tk:{skill}",
                )

    def test_names_no_skill_that_does_not_exist(self):
        advertised = set(re.findall(r"/tk:([a-z0-9-]+)", marketplace_description()))
        for name in sorted(advertised - set(skills_on_disk())):
            with self.subTest(skill=name):
                self.fail(
                    f"marketplace.json advertises /tk:{name}, which has no "
                    f"tk/skills/{name}/SKILL.md"
                )


if __name__ == "__main__":
    unittest.main()
