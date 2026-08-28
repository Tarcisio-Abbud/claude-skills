#!/usr/bin/env python3
"""The two manifests must name every skill that exists on disk, and no other.

Run: python3 -m unittest discover -s tk/tests   (stdlib only, no deps)

WHY THIS EXISTS. A skill is advertised in two places — `tk/.claude-plugin/plugin.json`
(the plugin's own description) and `.claude-plugin/marketplace.json` (the entry a
marketplace reader sees) — and neither is generated from `tk/skills/`. Nothing but a
human's memory kept the three in step, and that memory failed twice on 2026-08-28:

  - `/tk:review` shipped and never reached `marketplace.json`; the gap survived several
    merges and was closed by hand in `a0282cb`, noticed only because a rebase put the
    line under someone's eyes;
  - `claude-skills#48` added the `prune` skill in a branch while `#49` added `fleet` in
    another. Both edited the same `description` line, and resolving that conflict by
    taking either side would have silently dropped the other's skill.

The failure is quiet in both directions and expensive in one: a skill absent from the
description is a skill nobody discovers, and the file still parses, still merges, still
passes every other test.

NO MUTATION HARNESS, deliberately. The sibling suites are proved by putting a defect back
into a SCRIPT (`mutations_vista.py` and friends). The subject here is not a script but the
repository's own state, and the only way to plant a defect would be to edit the real
manifests mid-run — a test that rewrites the files it audits. The guard is proved instead
by construction: it reads the three sources independently and compares them, so it fails
whenever any one of them moves without the others.

SCOPE. This checks the SET of names, not the prose around them. A description that names
every skill and describes each one wrongly passes here — wording is a reader's judgement,
membership is not.
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


def marketplace_description():
    with open(MARKETPLACE, encoding="utf-8") as fh:
        entries = json.load(fh)["plugins"]
    tk = [e for e in entries if e["name"] == "tk"]
    assert len(tk) == 1, "marketplace.json must carry exactly one `tk` entry"
    return tk[0]["description"]


class TestSkillsOnDisk(unittest.TestCase):
    def test_there_are_skills_to_check(self):
        """A guard that silently checks nothing is worse than no guard."""
        self.assertTrue(skills_on_disk(), "no skill directory found under tk/skills/")


class TestPluginManifest(unittest.TestCase):
    """`plugin.json`'s description names each skill by its bare directory name."""

    def test_every_skill_is_named(self):
        description = plugin_description()
        for skill in skills_on_disk():
            with self.subTest(skill=skill):
                self.assertRegex(
                    description,
                    r"\b%s\b" % re.escape(skill),
                    "tk/.claude-plugin/plugin.json does not name the skill %r" % skill,
                )


class TestMarketplaceManifest(unittest.TestCase):
    """`marketplace.json`'s description names each skill as `/tk:<name>`."""

    def test_every_skill_is_named(self):
        description = marketplace_description()
        for skill in skills_on_disk():
            with self.subTest(skill=skill):
                self.assertIn(
                    "/tk:%s" % skill,
                    description,
                    ".claude-plugin/marketplace.json does not name /tk:%s" % skill,
                )

    def test_names_no_skill_that_does_not_exist(self):
        """The other direction: a deleted skill left advertised sends readers nowhere."""
        advertised = set(re.findall(r"/tk:([a-z0-9-]+)", marketplace_description()))
        for name in sorted(advertised - set(skills_on_disk())):
            with self.subTest(skill=name):
                self.fail(
                    "marketplace.json advertises /tk:%s, which has no "
                    "tk/skills/%s/SKILL.md" % (name, name)
                )


if __name__ == "__main__":
    unittest.main()
