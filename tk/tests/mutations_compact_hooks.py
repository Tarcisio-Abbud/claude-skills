#!/usr/bin/env python3
"""Mutation harness for the two compaction hooks and tk's mod — puts each defect back.

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
MOD = os.path.join("hooks", "compact-veto.js")

QUIET = "TheMarkHook.test_no_package_pointer_writes_nothing_and_says_nothing"
SEVEN = "TheMarkHook.test_one_line_is_appended_with_the_seven_fields_the_ledger_defines"
HOUR = "TheMarkHook.test_the_hour_is_a_clock_reading_and_not_a_placeholder"
QUOTA_LINE = "TheMarkHook.test_the_quota_field_is_the_bins_own_line_and_never_a_bare_number"
QUOTA_NONE = "TheMarkHook.test_a_quota_that_cannot_be_vouched_for_says_so_instead_of_a_number"
PIPE = "TheMarkHook.test_a_trigger_carrying_a_pipe_cannot_add_a_field"
BAD_POINTER = "TheMarkHook.test_a_pointer_file_nobody_can_read_costs_the_session_nothing"
BAD_PAYLOAD = ("TheMarkHook."
               "test_an_unreadable_payload_costs_the_line_its_trigger_and_not_the_line")
SUBAGENT = ("TheMarkHook."
            "test_a_subagents_compaction_is_not_a_seam_of_the_orchestrator")
AGENT_SESSION = ("TheMarkHook."
                 "test_the_main_thread_of_an_agent_session_still_leaves_its_line")
BLANK_AGENT = ("TheMarkHook."
               "test_a_blank_agent_id_is_not_a_subagent_and_leaves_its_line")

FIFO = "TheMarkHook.test_a_ledger_address_that_is_a_fifo_does_not_hang_the_session"
ABSENT_LEDGER = "TheMarkHook.test_a_ledger_nobody_has_created_yet_is_still_written"
NOT_COMPACT = "ThePointerHook.test_a_source_other_than_compact_prints_nothing"
NO_SOURCE = "ThePointerHook.test_a_payload_with_no_source_at_all_prints_nothing"
NO_PACKAGE = "ThePointerHook.test_no_package_pointer_injects_nothing"
ADDRESSES = "ThePointerHook.test_the_injected_paragraph_names_the_handoff_and_the_resume_procedure"
NO_HANDOFF = "ThePointerHook.test_a_handoff_that_is_not_there_is_said_and_never_pointed_at"
ENVELOPE = ("ThePointerHook."
            "test_the_paragraph_travels_in_the_envelope_and_never_as_plain_stdout")
SUBAGENT_WAKE = ("ThePointerHook."
                 "test_a_subagent_that_compacted_is_not_told_it_was_orchestrating")
AGENT_WAKE = ("ThePointerHook."
              "test_the_main_thread_of_an_agent_session_is_still_pointed_at_the_handoff")
BLANK_WAKE = ("ThePointerHook."
              "test_a_blank_agent_id_is_not_a_subagent_and_the_handoff_is_still_named")
WAKE_OTHER = "ThePointerHook.test_a_session_the_pointer_does_not_name_hears_nothing"
WAKE_OWN = "ThePointerHook.test_the_session_the_pointer_names_is_pointed_at_the_handoff"
EXCLUSION = ("ThePointerHook."
             "test_the_paragraph_opens_with_the_exclusion_a_dispatched_agent_obeys")

O = "TheOrchestratorsLedger."
OTHER_SESSION = O + "test_another_sessions_compaction_writes_nothing_in_this_ledger"
OWN_SESSION = O + "test_the_orchestrators_own_compaction_is_written"
NAMES = O + "test_the_line_names_the_session_and_a_numeric_window"
NOT_NUMERIC = O + "test_a_window_that_is_not_a_number_says_a_subagent_lands_here"
SETTINGS_KEY = O + "test_the_settings_key_is_read_from_the_sessions_own_directory"

M = "TheModVeto."
VETOED = M + "test_a_subagent_auto_compaction_in_the_package_session_is_vetoed"
MAIN_KEPT = M + "test_the_main_conversation_is_never_vetoed"
MANUAL = M + "test_a_manual_compaction_of_a_subagent_is_not_vetoed"
NO_POINTER = M + "test_with_no_package_pointer_nothing_is_vetoed"
BAD_JSON = M + "test_a_pointer_nobody_can_parse_vetoes_nothing"
OTHER_SUBAGENTS = M + "test_another_sessions_subagents_compact_while_a_package_runs"
NO_SESSION = M + "test_a_pointer_that_names_no_session_vetoes_nothing"
AT_LIMIT = M + "test_a_window_at_the_model_limit_vetoes_nothing"
PROBE = M + "test_the_pointer_address_can_be_named_for_a_probe"
DECIDE = M + "test_decide_refuses_every_input_that_is_not_a_veto"

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

    ("a subagent's compaction is written as the orchestrator's, as it shipped",
     """    if from_subagent(payload):""",
     """    if False:""",
     [SUBAGENT], MARK),

    ("the guard asks the agent TYPE, which the main thread of an --agent session has",
     '''    agent = payload.get("agent_id")
    return isinstance(agent, str) and agent.strip() != ""''',
     '''    agent = payload.get("agent_type")
    return isinstance(agent, str) and agent.strip() != ""''',
     [AGENT_SESSION], MARK),

    ("any agent_id at all is a subagent, blank and non-string included",
     '''    agent = payload.get("agent_id")
    return isinstance(agent, str) and agent.strip() != ""''',
     '''    return payload.get("agent_id") is not None''',
     [BLANK_AGENT], MARK),

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
     '''                    f"before anything else, then resume by {RESUME}.")''',
     '''                    f"before anything else.")''',
     [ADDRESSES], POINTER),

    ("a handoff nobody wrote is pointed at as though it were there",
     """        said.append(f"If you were orchestrating {name}: the package pointer names a "
                    f"handoff at {handoff} and there is no file there. Do not "
                    f"reconstruct it from the summary above: read {RESUME}, and "
                    f"rebuild the state from git and the ledger.")""",
     """        said.append(f"If you were orchestrating {name}: read the handoff at {handoff} "
                    f"before anything else, then resume by {RESUME}.")""",
     [NO_HANDOFF], POINTER),

    ("a subagent that compacted is told it was orchestrating, as it shipped",
     """    if from_subagent(payload):""",
     """    if False:""",
     [SUBAGENT_WAKE], POINTER),

    ("the wake guard asks the agent TYPE, which an --agent orchestrator has",
     '''    agent = payload.get("agent_id")
    return isinstance(agent, str) and agent.strip() != ""''',
     '''    agent = payload.get("agent_type")
    return isinstance(agent, str) and agent.strip() != ""''',
     [AGENT_WAKE], POINTER),

    ("any agent_id at all is a subagent, blank and non-string included",
     '''    agent = payload.get("agent_id")
    return isinstance(agent, str) and agent.strip() != ""''',
     '''    return payload.get("agent_id") is not None''',
     [BLANK_WAKE], POINTER),

    ("the paragraph is printed bare, and the harness attaches none of it",
     """        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": EVENT, "additionalContext": " ".join(said)}}))""",
     '        print(" ".join(said))',
     [ENVELOPE], POINTER),

    ("the exclusion is dropped, and a subagent hears only the orchestrator's order",
     """    said = [f"tk: a compaction happened while package {name} was running.",
            "If the summary above shows you were dispatched with a brief or an item, "
            "this paragraph is not for you: continue your item and do not read the "
            "handoff."]""",
     """    said = [f"tk: this session was compacted while orchestrating {name}."]""",
     [EXCLUSION], POINTER),

    ("another session's compaction is sent to this package's handoff",
     """    if isinstance(owner, str) and owner.strip() and payload.get("session_id") != owner:""",
     """    if False:""",
     [WAKE_OTHER], POINTER),

    ("the wake gate compares nothing, and the orchestrator itself hears nothing",
     """    if isinstance(owner, str) and owner.strip() and payload.get("session_id") != owner:""",
     """    if isinstance(owner, str) and owner.strip():""",
     [WAKE_OWN], POINTER),

    # -- the mark hook's session gate and judgement ----------------------------
    ("another session's compaction is written in the package's ledger",
     """    if other_session(package, payload):""",
     """    if False:""",
     [OTHER_SESSION], MARK),

    ("the gate compares nothing, and the orchestrator's own compaction is dropped",
     """    return payload.get("session_id") != owner""",
     """    return True""",
     [OWN_SESSION, NAMES, NOT_NUMERIC, SETTINGS_KEY], MARK),

    ("a pointer that names no session gates every compaction out",
     """    if not isinstance(owner, str) or not owner.strip():
        return False""",
     """    if not isinstance(owner, str) or not owner.strip():
        return True""",
     [SEVEN], MARK),

    ("the line keeps the old wording and names neither session nor judgement",
     '''        plain(f"context emptied (session {session}: {judgement(payload)}); "''',
     '''        plain("context emptied; "''',
     [NAMES, NOT_NUMERIC, SETTINGS_KEY], MARK),

    ("the judgement reads the window backwards",
     """    if found is None:
        return "window not numeric""",
     """    if found is not None:
        return "window not numeric""",
     [NAMES, NOT_NUMERIC, SETTINGS_KEY], MARK),

    ("the window is read from the payload's cwd instead of the session's directory",
     '''        base = (context.session_dir(path) if isinstance(path, str) else None) \\
            or payload.get("cwd") or os.getcwd()''',
     '''        base = payload.get("cwd") or os.getcwd()''',
     [SETTINGS_KEY], MARK),

    # -- the mod ------------------------------------------------------------------
    ("the skip is never returned, and every subagent compacts mid-item",
     """    return why === null ? next(e) : { skip: why }""",
     """    return next(e)""",
     [VETOED, PROBE], MOD),

    ("the agentId test is flipped, and the main conversation is vetoed instead",
     """  if (typeof agentId !== 'string' || agentId === '') return null""",
     """  if (typeof agentId === 'string' && agentId !== '') return null""",
     [VETOED, MAIN_KEPT, PROBE, DECIDE], MOD),

    ("the trigger gate is dropped, and a person's /compact of a subagent is refused",
     """  on('session.compact', { trigger: 'auto' }, async ($, e, next) => {""",
     """  on('session.compact', async ($, e, next) => {""",
     [MANUAL], MOD),

    ("the pointer gate is dropped, so a missing pointer throws inside the verdict",
     """  if (pointer === null || typeof pointer !== 'object' || Array.isArray(pointer)) return null""",
     "",
     [DECIDE], MOD),

    ("a missing or unreadable pointer is read as this session's package",
     """    return null                       // no package running: the ordinary case""",
     """    return { session: await $.session.id() }""",
     [NO_POINTER, BAD_JSON], MOD),

    ("the session gate is dropped, and every session's subagents lose their compaction",
     """  if (pointer.session !== sessionId) return null""",
     "",
     [OTHER_SUBAGENTS], MOD),

    ("a pointer with no session matches a session that has no id",
     """  if (typeof pointer.session !== 'string' || pointer.session === '') return null""",
     "",
     [DECIDE], MOD),

    ("a pointer written before the session field vetoes in every session",
     """  if (typeof pointer.session !== 'string' || pointer.session === '') return null""",
     """  if (pointer.session === undefined) return VETO""",
     [NO_SESSION], MOD),

    ("the window gate is dropped, and the recovery at the model's limit is refused",
     """  if (compactWindow >= modelWindow) return null""",
     "",
     [AT_LIMIT], MOD),

    ("a window nobody read is taken for a number",
     """  if (!Number.isFinite(compactWindow) || !Number.isFinite(modelWindow)) return null""",
     "",
     [DECIDE], MOD),

    ("the probe's pointer address is ignored",
     """(await $.env.get('TK_PACKAGE_POINTER')) || """,
     "",
     [PROBE], MOD),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_compact_hooks"))
