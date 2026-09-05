#!/usr/bin/env python3
"""Mutation harness for the `tk-context` suite — puts each defect back.

Run: python3 tk/tests/mutations_tk_context.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires every one of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

WHY THE ARITHMETIC IS MUTATED AT ALL. Every defect here is one an eyeball passes:
a number six digits long is plausible whether or not it counted the right three
fields, read the newest entry, or came from this session. The suite exists
because the output cannot be sanity-checked by looking at it, and these entries
are what say the suite can tell the difference.

FOUR ENTRIES MUTATE PROSE — three in `WINDOW.md`, one in `AFK.md`. Prose is half the subject: a
command nothing calls is a command nobody runs, and the instruction that calls it
is exactly what went missing for three generations. The shipped defect — the seam
sent to the statusline — is entry `the seam is sent back to the statusline`.

ONE ENTRY MUTATES THE TEST FILE, which no sibling does. `sends_to_the_statusline`
is a reader, not a substring check: it must let WINDOW.md SAY the number is not in
the statusline while refusing an instruction to go and read it there. That
distinction lives in a lookbehind, and nothing outside this file can break it. So
the lookbehind is mutated where it lives.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

CONTEXT = os.path.join("bin", "tk-context")
WINDOW = os.path.join("skills", "kickoff", "WINDOW.md")
AFK = os.path.join("skills", "kickoff", "AFK.md")
SUITE = os.path.join("tests", "test_tk_context.py")

SUM = "TheNumber.test_the_three_input_counters_are_summed_and_output_is_left_out"
NEWEST = "TheNumber.test_the_newest_entry_wins_over_every_older_one"
SIDECHAIN = "TheNumber.test_a_sidechain_entry_is_not_this_session"
HALF_LINE = "TheNumber.test_a_half_written_last_line_costs_nothing"
NO_PCT = "TheNumber.test_the_output_carries_no_percentage"
NO_ENV = "WhenThereIsNoNumber.test_no_session_id_in_the_environment"
NO_FILE = "WhenThereIsNoNumber.test_no_transcript_for_this_session"
NO_CALL = "WhenThereIsNoNumber.test_a_transcript_with_no_api_response_yet"
CURVE_FD = "TheCurve.test_the_curve_goes_to_stderr_and_leaves_stdout_the_bare_number"
CURVE_OFF = "TheCurve.test_without_the_flag_nothing_but_the_number_is_printed"
CALLS_IT = "TheProseThatCallsIt.test_window_and_afk_send_the_seam_to_the_command"
NOT_STATUS = "TheProseThatCallsIt.test_no_seam_still_sends_the_reader_to_the_statusline"
BOTH_WAYS = "TheProseThatCallsIt.test_the_reading_of_that_assertion_goes_both_ways"
ABSOLUTE = "TheProseThatCallsIt.test_window_states_that_the_threshold_is_absolute"
DECLARED = "TheProseThatCallsIt.test_window_licenses_judgement_only_when_it_is_declared"

BOUNDARY_WINS = "AfterACompaction.test_a_boundary_newer_than_the_last_response_decides_the_number"
BOUNDARY_SAID = "AfterACompaction.test_the_reading_says_it_came_from_a_boundary"
RESPONSE_BACK = "AfterACompaction.test_a_response_after_the_boundary_takes_it_back"
ZERO_ROW = "RecordsThatLookLikeAnOccupancyAndAreNot.test_an_all_zero_usage_block_is_skipped"
NOT_A_NUMBER = ("RecordsThatLookLikeAnOccupancyAndAreNot."
                "test_a_counter_that_is_not_a_number_refuses_rather_than_reports_an_older_window")
NUMERIC_STR = ("RecordsThatLookLikeAnOccupancyAndAreNot."
               "test_a_counter_written_as_a_numeric_string_is_still_a_number")
BAD_BYTE = "RecordsThatLookLikeAnOccupancyAndAreNot.test_a_byte_the_encoding_cannot_hold_costs_nothing"
LITERAL_ID = "ResolvingTheFile.test_a_session_id_is_a_literal_and_never_a_glob"
TWO_FILES = "ResolvingTheFile.test_two_transcripts_for_one_id_are_refused_and_both_named"
THE_FLAG = "ResolvingTheFile.test_the_transcript_flag_is_the_file_that_gets_read"
TYPO = "TheExitCodes.test_a_mistyped_flag_does_not_read_as_no_number"

BOUNDARY_BLANK_REFUSES = ("AfterACompaction."
                          "test_a_boundary_with_no_usable_count_refuses_and_does_not_fall_back")
FLAT_ID = "WhatComesFromOutsideThisProcess.test_a_session_id_carrying_an_escape_is_printed_flat"
FLAT_STAMP = ("WhatComesFromOutsideThisProcess."
              "test_a_boundary_timestamp_from_the_file_is_printed_flat")
FLAT_UUID = "WhatComesFromOutsideThisProcess.test_a_record_uuid_from_the_file_is_printed_flat"
ARGV = "TheSiblingSeam.test_main_takes_its_argv_like_every_sibling_bin"

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- the number itself ---------------------------------------------------
    ("output tokens are counted into the window, so the number stops matching a statusline",
     '''INPUT_FIELDS = ("input_tokens", "cache_creation_input_tokens",
                "cache_read_input_tokens")''',
     '''INPUT_FIELDS = ("input_tokens", "cache_creation_input_tokens",
                "cache_read_input_tokens", "output_tokens")''',
     [SUM], CONTEXT),

    ("the OLDEST reading is printed — a session's opening size, forever",
     "    last = points[-1]",
     "    last = points[0]",
     [NEWEST], CONTEXT),

    ("a subagent's entry is counted as this session's window",
     """            if record.get("isSidechain"):
                continue
""",
     "",
     [SIDECHAIN], CONTEXT),

    ("a half-written last line crashes the reading instead of being skipped",
     """            except ValueError:
                continue""",
     """            except ValueError:
                raise""",
     [HALF_LINE], CONTEXT),

    ("the output helpfully carries a percentage, which is the forbidden comparison",
     'print(f"{last.tokens} tokens in context")',
     'print(f"{last.tokens} tokens in context ({last.tokens / 1000000:.0%})")',
     [NO_PCT], CONTEXT),

    # -- the three ways there is no number -----------------------------------
    ("a failure to read exits 0, so a caller cannot tell a number from none",
     "EXIT_NO_NUMBER = 2",
     "EXIT_NO_NUMBER = 0",
     [NO_ENV, NO_FILE, NO_CALL], CONTEXT),

    ("the failure says nothing about judgement — the licence the caller needs",
     '''    print("tk-context: no number — decide by judgement, and say it is judgement",
          file=sys.stderr)
''',
     "",
     [NO_ENV, NO_FILE, NO_CALL], CONTEXT),

    # -- the curve -----------------------------------------------------------
    ("the curve's rows go to stdout, burying the number a caller compares",
     '        print(f"  {stamp:19}  {point.tokens:>9,d}{delta}{mark}", file=sys.stderr)',
     '        print(f"  {stamp:19}  {point.tokens:>9,d}{delta}{mark}")',
     [CURVE_FD], CONTEXT),

    ("the curve prints whether or not it was asked for",
     """    if args.curve:
        print_curve(points)""",
     """    if True:
        print_curve(points)""",
     [CURVE_OFF], CONTEXT),

    # -- the prose that calls it ---------------------------------------------
    ("the seam is sent back to the statusline — the shipped defect, in AFK.md",
     """the last from
`../../bin/tk-context` at that seam""",
     """the last read
from the statusline at that seam""",
     [CALLS_IT, NOT_STATUS], AFK),

    ("WINDOW.md says the number IS in the statusline",
     "It is not in the statusline",
     "It is in the statusline",
     [NOT_STATUS], WINDOW),

    ("WINDOW.md drops the absolute rule, and 29% of a 1M window reads as room",
     "- **Compare absolutes, never a fraction.** The threshold is the smart zone's edge",
     "- **Compare the fraction of the window.** The threshold is the ceiling's edge",
     [ABSOLUTE], WINDOW),

    ("WINDOW.md lets the judgement pass unlabelled — the defect that started this",
     "and the report names it as judgement",
     "and the report need not dwell on it",
     [DECLARED], WINDOW),

    # -- the reader inside the suite -----------------------------------------
    ("the statusline check becomes a word ban, so a DENIAL reads as an instruction",
     'r"(?<!not )(?:in|from|on) the statusline"',
     'r"(?:in|from|on) the statusline"',
     [BOTH_WAYS, NOT_STATUS], SUITE),
    # -- the record classes that decide the occupancy ------------------------
    # Every entry below restores a defect the SYSTEM LENS found on 2026-09-03,
    # or a guard the same report showed no test was watching. The class it named
    # is one shape: a reader written as a filter over the rows it likes, where
    # every row it did not name defaults to silence.
    ("the boundary is invisible again — the pre-compaction window is printed, 25x over",
     """    if record.get("subtype") != "compact_boundary":
        return None""",
     """    if True:
        return None""",
     [BOUNDARY_WINS, BOUNDARY_SAID], CONTEXT),

    ("a boundary anywhere in the file wins, even one an API response has answered",
     "    last = points[-1]",
     '    last = ([p for p in points if p.kind == "compaction"] or points)[-1]',
     [RESPONSE_BACK], CONTEXT),

    ("a boundary with no readable count falls through, and the PRE-compaction row wins",
     "        no_number(f\"the compaction at {plain(record.get('timestamp') or '?')} \"\n                  \"records no readable postTokens\")",
     "        return None",
     [BOUNDARY_BLANK_REFUSES], CONTEXT),

    ("a boundary with no readable count becomes an occupancy of zero",
     "    if not isinstance(post, int):",
     "    if False:",
     [BOUNDARY_BLANK_REFUSES], CONTEXT),

    ("the all-zero usage block of a synthetic reply is taken as the window",
     "    return total or None",
     "    return total",
     [ZERO_ROW], CONTEXT),

    ("a counter that is not a number is skipped, and an OLDER window is printed as current",
     "        no_number(\"a usage counter in \"",
     "        return None  # noqa",
     [NOT_A_NUMBER], CONTEXT),

    ("the counters are summed uncoerced, so a numeric string refuses instead of reading",
     "        total = sum(int(usage.get(f) or 0) for f in INPUT_FIELDS)",
     "        total = sum(usage.get(f) or 0 for f in INPUT_FIELDS)",
     [NUMERIC_STR], CONTEXT),

    ("a byte the encoding cannot hold crashes the reading",
     '        handle = open(path, errors="replace")',
     "        handle = open(path)",
     [BAD_BYTE], CONTEXT),

    # -- resolving the file --------------------------------------------------
    ("the session id is interpolated into the glob raw, so `--session '*'` reads a stranger",
     'f"{glob.escape(session_id)}.jsonl"',
     'f"{session_id}.jsonl"',
     [LITERAL_ID], CONTEXT),

    ("two transcripts for one id are resolved alphabetically, in silence",
     '    if len(hits) > 1:\n'
     '        no_number("two transcripts carry this session id: "\n'
     '                  + ", ".join(plain(h) for h in hits))\n',
     "",
     [TWO_FILES], CONTEXT),

    ("--transcript is ignored and the env session is read instead",
     """    path = args.transcript
    if not path:""",
     """    path = None
    if not path:""",
     [THE_FLAG], CONTEXT),

    ("a mistyped flag exits 2 — indistinguishable from `no number, use judgement`",
     "        sys.exit(EXIT_USAGE)",
     "        sys.exit(EXIT_NO_NUMBER)",
     [TYPO], CONTEXT),

    ("the curve drops its newest row, so the seam reads a stale slope",
     """    if sampled[-1] is not points[-1]:
        sampled.append(points[-1])""",
     "    pass",
     [CURVE_FD], CONTEXT),
    # -- what came from outside this process ---------------------------------
    ("the escape stripper passes everything through, and a directory name owns the terminal",
     '    return re.sub(r"[\\x00-\\x1f\\x7f]", "?", str(value))',
     "    return str(value)",
     [FLAT_ID, FLAT_STAMP, FLAT_UUID], CONTEXT),

    ("the session id reaches the terminal unstripped",
     'no_number(f"no transcript for session {plain(session_id)} under {root}")',
     'no_number(f"no transcript for session {session_id} under {root}")',
     [FLAT_ID], CONTEXT),

    ("a boundary timestamp read from the file reaches the terminal unstripped",
     'print(f"tk-context: read from the compaction at {plain(last.stamp)[:19]}, "',
     'print(f"tk-context: read from the compaction at {last.stamp[:19]}, "',
     [FLAT_STAMP], CONTEXT),

    ("a record uuid read from the file reaches the terminal unstripped",
     "f\"{plain(record.get('uuid') or 'a record')} is not a number\")",
     "f\"{record.get('uuid') or 'a record'} is not a number\")",
     [FLAT_UUID], CONTEXT),

    ("main stops taking its argv — the seam every sibling bin keeps",
     "def main(argv=None):",
     "def main():",
     [ARGV], CONTEXT),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_context"))
