#!/usr/bin/env python3
"""Mutation harness for the wall's step-2 suite — puts each defect back.

Run: python3 tk/tests/mutations_window_wall.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`, runs only
the tests named for it, and requires each of them to fail. A mutation that SURVIVES is a hole
in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

SEVEN ENTRIES MUTATE PROSE and five mutate `bin/tk-queue`, which is the default source. Prose is
half the subject here: the suite audits a procedure a skill file prescribes, so an instruction
deleted from that file is exactly the defect it exists to catch — the shipped one T265 fixed.

THE TWO THAT CARRY THE DESIGN. `the instruction is deleted` and `the instruction is negated`
must both fail the BEHAVIOUR test, not only the reading test. That is the claim the suite
makes: the fixture executes what the prose says, so prose that stops saying it stops doing it.
An earlier draft failed only a regex here, and the behaviour test measured `tk-queue` while
the fix it was written for was gone.

WHAT A GREEN SCORE DOES NOT SAY. `the flags are swapped` kills the reading test and leaves the
fixture green — deliberately: the fixture fills by flag NAME, so a swapped prescription still
runs correctly. It is the READER filling three identical placeholders left to right who is
harmed, and only a rule about the prose can catch that. `the queue is not named` is the same
shape for the same reason: the fixture attaches a `--dir` of its own to every invocation, so
the run stays green with the flag gone and only the argv assertion sees it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

QUEUE = os.path.join("bin", "tk-queue")
WINDOW = os.path.join("skills", "kickoff", "WINDOW.md")
VERIFY = os.path.join("skills", "verify", "SKILL.md")

READS = "WallStep2Test.test_the_wall_step_prescribes_the_handoff_and_instructs_the_printed_edit"
FIELDS = "WallStep2Test.test_the_prescribed_command_carries_the_mandatory_fields_in_rendered_order"
POINTS = "WallStep2Test.test_the_pointers_in_the_step_resolve_and_the_home_states_the_rule"
RUNS = "WallStep2Test.test_an_ordinary_item_points_at_its_briefing_after_the_prescribed_steps"
QUEUE_DIR = "WallStep2Test.test_the_prescribed_command_names_the_queue_it_writes"

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- the shipped defect, and its opposite --------------------------------
    ("T265 the wall's step 2 writes the briefing and never says to run the printed `edit`",
     ", **then run the `edit` it prints** (same file, *The item\n   points at the briefing*)",
     "",
     [READS, RUNS], WINDOW),

    ("T265 the wall's step 2 says the OPPOSITE — never run the printed `edit`",
     "**then run the `edit` it prints**",
     "**then never run the `edit` it prints**",
     [READS, RUNS], WINDOW),

    # -- the prescription itself ---------------------------------------------
    ("T265 step 2 names the briefing and prescribes no command for it",
     '`tk-queue handoff "<id>" --dir "<queue dir>" --objective "..."\n'
     '   --state "..." --blockers "..."`, in the form',
     "the briefing, in the form",
     [READS, FIELDS, RUNS], WINDOW),

    ("T265 the prescribed command drops --state, which the gate demands",
     '--objective "..."\n   --state "..." --blockers "..."',
     '--objective "..." --blockers "..."',
     [FIELDS, RUNS], WINDOW),

    ("T265 the prescribed command lists its fields in another order than the briefing renders",
     '--objective "..."\n   --state "..." --blockers "..."',
     '--blockers "..."\n   --state "..." --objective "..."',
     [FIELDS], WINDOW),

    ("T304 the prescribed command does not name the queue it writes",
     '`tk-queue handoff "<id>" --dir "<queue dir>" --objective',
     '`tk-queue handoff "<id>" --objective',
     [QUEUE_DIR], WINDOW),

    # -- the pointer and what it points at -----------------------------------
    ("T265 the pointer names a section that does not exist",
     "(same file, *The item\n   points at the briefing*). That warning",
     "(same file, *The briefing\n   points at the item*). That warning",
     [POINTS], WINDOW),

    ("T265 the home five sites route to stops stating the rule",
     "**Run the `edit` it\nprints.** That pointer",
     "That pointer",
     [POINTS], VERIFY),

    ("T265 the home states the OPPOSITE of the rule",
     "**Run the `edit` it\nprints.**",
     "**Never run the `edit` it\nprints.**",
     [POINTS], VERIFY),

    # -- the tool stops holding up its half ----------------------------------
    ("T265 handoff stops warning about an item that points at nothing",
     "    if args.id not in handoff_refs(block):",
     "    if False:",
     [RUNS], QUEUE),

    ("T265 the printed remedy is no longer quoted for the shell",
     "f\"{shlex.quote(fixed)}{forced}`.\", file=sys.stderr)",
     "f\"{fixed}{forced}`.\", file=sys.stderr)",
     [RUNS], QUEUE),

    ("T265 handoff reports a briefing it never wrote",
     "    write_atomic(path, candidate)",
     "    pass",
     [RUNS], QUEUE),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_window_wall",
                 os.path.dirname(os.path.dirname(os.path.abspath(__file__))), QUEUE))
