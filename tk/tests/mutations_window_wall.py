#!/usr/bin/env python3
"""Mutation harness for the wall's step-2 suite — puts each defect back.

Run: python3 tk/tests/mutations_window_wall.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`, runs only
the tests named for it, and requires each of them to fail. A mutation that SURVIVES is a
hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`, which takes the
test module, the entry list and the default source as arguments.

WHAT IS MUTATED HERE IS PROSE as often as it is code, because the subject is prose: three
entries edit `WINDOW.md` and `verify/SKILL.md`, which is exactly the edit a careless prune
makes. The two that matter most are the pair restoring the reported defect — the wall's
step 2 with its `edit` instruction removed, and the file it points at with the rule removed
— because that instruction is what T265 added and nothing else would notice its loss.

WHAT A GREEN SCORE HERE DOES NOT SAY. The fixture executes the wall's step 2 and nothing
else. The wall's other five steps, and the four sibling sites that prescribe the same
handoff (`WINDOW.md`'s planning seam, `AFK.md`'s close and its oversized item,
`wrap-up/SKILL.md`), are held by review alone.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

QUEUE = os.path.join("bin", "tk-queue")
WINDOW = os.path.join("skills", "kickoff", "WINDOW.md")
VERIFY = os.path.join("skills", "verify", "SKILL.md")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- the reported defect, put back ---------------------------------------
    ("T265 the wall's step 2 writes the briefing and never says to run the printed `edit`",
     "prescribes, **then run the `edit` it\n   prints**, as that file asks.",
     "prescribes.",
     ["WallStep2Test.test_the_wall_step_prescribes_the_handoff_and_the_edit_it_prints"],
     WINDOW),

    ("T265 the file the wall points at for the form stops stating the rule",
     "Run it as printed: that pointer is the briefing's only discovery path,",
     "That pointer is the briefing's only discovery path,",
     ["WallStep2Test.test_the_file_the_wall_sends_the_reader_to_carries_the_rule"],
     VERIFY),

    ("T265 the wall's step 2 names the briefing and prescribes no command for it",
     '`tk-queue handoff "<id>" --objective "..." --state "..."\n'
     '   --blockers "..."`, in the form',
     'the briefing, in the form',
     ["WallStep2Test.test_an_ordinary_item_points_at_its_briefing_after_the_printed_edit",
      "WallStep2Test.test_the_wall_step_prescribes_the_handoff_and_the_edit_it_prints"],
     WINDOW),

    # -- the tool stops holding up its half ----------------------------------
    ("T265 handoff stops warning about an item that points at nothing",
     "    if args.id not in handoff_refs(block):",
     "    if False:",
     ["WallStep2Test.test_an_ordinary_item_points_at_its_briefing_after_the_printed_edit"],
     QUEUE),

    ("T265 the printed remedy is no longer quoted for the shell",
     "f\"{shlex.quote(fixed)}{forced}`.\", file=sys.stderr)",
     "f\"{fixed}{forced}`.\", file=sys.stderr)",
     ["WallStep2Test.test_an_ordinary_item_points_at_its_briefing_after_the_printed_edit"],
     QUEUE),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_window_wall",
                 os.path.dirname(os.path.dirname(os.path.abspath(__file__))), QUEUE))
