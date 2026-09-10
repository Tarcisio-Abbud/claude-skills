#!/usr/bin/env python3
"""Mutation harness for the two compaction hooks — puts each defect back.

Run: python3 tk/tests/mutations_compact_hooks.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires every one of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

WHY SILENCE IS MUTATED AS HARD AS OUTPUT. Both scripts are wired into
`~/.claude/settings.json` for every session on this machine, and only a few
sessions are packages. The expensive defects here are therefore the ones that
speak when there is nothing to say — a hook that errors interrupts a session, and
a hook that injects a package's instruction into an unrelated compacted session
sends it to read a file that is not its own. Four entries below restore exactly
that shape.

THE LAST ENTRY IS THE DEFECT THAT SHIPPED. The pointer hook printed its paragraph
as plain text, ran for a live session on 2026-09-09, and delivered nothing: the
harness attaches `hookSpecificOutput.additionalContext` and logs a payload-less
hook as "produced no response payload". Every test here read raw stdout, and
every one of them was green.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

MARK = os.path.join("bin", "tk-compact-mark")
POINTER = os.path.join("bin", "tk-compact-pointer")

QUIET = "TheMarkHook.test_no_package_pointer_writes_nothing_and_says_nothing"
SEVEN = "TheMarkHook.test_one_line_is_appended_with_the_seven_fields_the_ledger_defines"
HOUR = "TheMarkHook.test_the_hour_is_a_clock_reading_and_not_a_placeholder"
QUOTA_LINE = "TheMarkHook.test_the_quota_field_is_the_bins_own_line_and_never_a_bare_number"
QUOTA_NONE = "TheMarkHook.test_a_quota_that_cannot_be_vouched_for_says_so_instead_of_a_number"
PIPE = "TheMarkHook.test_a_trigger_carrying_a_pipe_cannot_add_a_field"
BAD_POINTER = "TheMarkHook.test_a_pointer_file_nobody_can_read_costs_the_session_nothing"
BAD_PAYLOAD = ("TheMarkHook."
               "test_an_unreadable_payload_costs_the_line_its_trigger_and_not_the_line")

FIFO = "TheMarkHook.test_a_ledger_address_that_is_a_fifo_does_not_hang_the_session"
ABSENT_LEDGER = "TheMarkHook.test_a_ledger_nobody_has_created_yet_is_still_written"
NOT_COMPACT = "ThePointerHook.test_a_source_other_than_compact_prints_nothing"
NO_SOURCE = "ThePointerHook.test_a_payload_with_no_source_at_all_prints_nothing"
NO_PACKAGE = "ThePointerHook.test_no_package_pointer_injects_nothing"
ADDRESSES = "ThePointerHook.test_the_injected_paragraph_names_the_handoff_and_the_resume_procedure"
NO_HANDOFF = "ThePointerHook.test_a_handoff_that_is_not_there_is_said_and_never_pointed_at"
ENVELOPE = ("ThePointerHook."
            "test_the_paragraph_travels_in_the_envelope_and_never_as_plain_stdout")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- the mark hook's silence ---------------------------------------------
    ("a session that is not a package is interrupted by the hook",
     """        # No package is running, or the pointer names no ledger. Silence is the
        # answer: this hook is wired for every session on the machine.
        return 0""",
     """        print("tk-compact-mark: no package pointer", file=sys.stderr)
        return 1""",
     [QUIET], MARK),

    ("the pointer reader is unguarded, so a path nobody can read stops the session",
     """    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8-sig") as handle:
            found = json.load(handle)
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        print(f"tk-compact-mark: cannot read {path}: {exc}", file=sys.stderr)
        return None""",
     """    with open(path, encoding="utf-8-sig") as handle:
        found = json.load(handle)""",
     [BAD_POINTER], MARK),

    ("an unreadable payload costs the whole line instead of one field",
     """    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}""",
     """    payload = json.load(sys.stdin)""",
     [BAD_PAYLOAD], MARK),

    ("the ledger address is opened unguarded, and a FIFO there blocks the session",
     """    if os.path.exists(address) and not os.path.isfile(address):""",
     """    if False:""",
     [FIFO], MARK),

    ("the guard refuses absence too, and the first compact of a package leaves no line",
     """    if os.path.exists(address) and not os.path.isfile(address):""",
     """    if not os.path.isfile(address):""",
     [ABSENT_LEDGER], MARK),

    # -- the mark hook's line -------------------------------------------------
    ("the model field is dropped, and every field after it shifts left",
     """        SYSTEM_LANE,
        EMPTY,
        EMPTY,""",
     """        SYSTEM_LANE,
        EMPTY,""",
     [SEVEN], MARK),

    ("the hour is a placeholder, and the rate computed from it is nothing",
     '        time.strftime("%H:%M"),',
     '        "??:??",',
     [HOUR], MARK),

    ("the percentage is retyped out of the line, losing what said it was a reading",
     "    return plain(line[0])",
     "    return plain(line[0].split()[1])",
     [QUOTA_LINE], MARK),

    ("a window nothing can vouch for is written as a number anyway",
     '        return f"no reading (tk-quota exit {run.returncode})"',
     '        return "0% used"',
     [QUOTA_NONE], MARK),

    ("the pipe survives the sanitiser, and the harness's own word adds fields",
     '    return re.sub(r"[\\x00-\\x1f\\x7f|]", "?", str(value)).strip()',
     '    return re.sub(r"[\\x00-\\x1f\\x7f]", "?", str(value)).strip()',
     [PIPE], MARK),

    # -- the pointer hook -----------------------------------------------------
    ("every session start is injected into, not only a compacted one",
     '    if payload.get("source") != SOURCE:',
     "    if False:",
     [NOT_COMPACT, NO_SOURCE], POINTER),

    ("an unidentified payload passes the guard, as it did before the banner was believed",
     '    if payload.get("source") != SOURCE:',
     '    if payload.get("source") not in (None, SOURCE):',
     [NO_SOURCE], POINTER),

    ("a compacted session with no package is sent to read one anyway",
     """    package = pointer(path)
    if not package:
        return 0""",
     """    package = pointer(path) or {"handoff": RESUME}""",
     [NO_PACKAGE], POINTER),

    ("the injection names the handoff and forgets the procedure that resumes it",
     '''        said.append(f"Read the handoff at {handoff} before anything else, then resume "
                    f"by {RESUME}.")''',
     '''        said.append(f"Read the handoff at {handoff} before anything else.")''',
     [ADDRESSES], POINTER),

    ("a handoff nobody wrote is pointed at as though it were there",
     """        said.append(f"The package pointer names a handoff at {handoff} and there is no "
                    f"file there. Do not reconstruct it from the summary above: read "
                    f"{RESUME}, and rebuild the state from git and the ledger.")""",
     """        said.append(f"Read the handoff at {handoff} before anything else, then resume "
                    f"by {RESUME}.")""",
     [NO_HANDOFF], POINTER),

    ("the paragraph is printed bare, and the harness attaches none of it",
     """        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": EVENT, "additionalContext": " ".join(said)}}))""",
     '        print(" ".join(said))',
     [ENVELOPE], POINTER),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_compact_hooks"))
