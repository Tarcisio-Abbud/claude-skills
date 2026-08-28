#!/usr/bin/env python3
"""Mutation harness for the manifests suite — puts each defect back.

Run: python3 tk/tests/mutations_manifests.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires each of them to fail. A mutation that
SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

WHAT IS MUTATED HERE IS DATA, not a bin. The subject of this suite is the repository's
own state — two manifests against a directory of skills — so the defect to restore is an
edit to a manifest, which is exactly the edit a careless merge makes. The first draft of
the suite claimed no harness was possible for that reason; it was wrong, and the claim
cost a review finding. The runner mutates a COPY and never touches the real files.

ONE WRINKLE THE SIBLINGS DO NOT HAVE. `marketplace.json` lives at the repository ROOT,
outside the `tk/` the runner copies, so its entries carry the explicit
`../.claude-plugin/marketplace.json`. That path resolves inside the copy, and the runner
creates its directory before writing — without that, the mutant would die of
`FileNotFoundError` and be scored as killed while the suite never looked at it.

THE TWO ENTRIES THAT MATTER MOST are the vacuity pair: they delete a skill's clause while
leaving the WORD in neighbouring prose. An earlier draft matched the bare word and stayed
green through both — the defect this whole suite exists to catch, alive inside it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

PLUGIN = os.path.join(".claude-plugin", "plugin.json")
MARKETPLACE = os.path.join(os.pardir, ".claude-plugin", "marketplace.json")
SUITE = os.path.join("tests", "test_manifests.py")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- a shipped skill falls out of a description -------------------------
    ("a skill's clause leaves plugin.json, the word surviving in the prose next door",
     "verify (the item's acceptance criterion as the ruler of the delivery), "
     "review (lens campaign: the second pair of eyes on a delivered code or data slice), ",
     "verify (the item's acceptance criterion, applied before review and after it), ",
     ["TestPluginManifest.test_every_skill_is_named"],
     PLUGIN),

    ("a skill's mention leaves marketplace.json — the real #48/#49 defect",
     "/tk:review puts one lens over a delivered slice, ",
     "",
     ["TestMarketplaceManifest.test_every_skill_is_named"],
     MARKETPLACE),

    # -- a description outlives the skill it names ---------------------------
    ("plugin.json keeps a clause for a skill that is not on disk",
     "prune (prunes a skill",
     "ghost (haunts nothing), prune (prunes a skill",
     ["TestPluginManifest.test_names_no_skill_that_does_not_exist"],
     PLUGIN),

    ("marketplace.json advertises a skill that is not on disk",
     "/tk:prune prunes a skill",
     "/tk:ghost haunts nothing, /tk:prune prunes a skill",
     ["TestMarketplaceManifest.test_names_no_skill_that_does_not_exist"],
     MARKETPLACE),

    # -- the guard stops seeing anything -------------------------------------
    ("the skill sweep looks for the wrong filename, so it checks nothing at all",
     'if os.path.isfile(os.path.join(SKILLS_DIR, name, "SKILL.md"))',
     'if os.path.isfile(os.path.join(SKILLS_DIR, name, "SKILL.md.absent"))',
     ["TestTheGuardHasSomethingToCheck.test_there_are_skills_on_disk"],
     SUITE),

    ("a second `tk` entry sits in the marketplace, its description unchecked",
     '    {\n      "name": "tk-cowork",',
     '    {\n      "name": "tk",\n      "displayName": "tk (stale duplicate)",\n'
     '      "source": "./tk",\n      "description": "a copy nobody updates"\n    },\n'
     '    {\n      "name": "tk-cowork",',
     ["TestTheGuardHasSomethingToCheck.test_the_marketplace_carries_exactly_one_tk_entry"],
     MARKETPLACE),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_manifests"))
