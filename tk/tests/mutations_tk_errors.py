#!/usr/bin/env python3
"""Mutation harness for the `tk-errors` suite — puts each defect back.

Run: python3 tk/tests/mutations_tk_errors.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires every one of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

WHY THIS COMMAND NEEDS MUTATING AT ALL. Its output is two counts and some rows,
and both failure directions read as ordinary output: a reader that missed a
refusal prints a smaller number, and a reader that invented one prints a larger.
Neither can be sanity-checked by looking at it, which is the same reason
`tk-context` is mutated. The entries below are what say the suite can tell a
number that counted the right thing from one that did not.

THE ENTRIES THAT REPLACE A WHOLE FUNCTION are not vandalism. `the invocations are
found by a regex over the raw command` is the naive implementation this design
rejected, written out: it is what a reader who had not met a quoted briefing
would write, and the tests that survive it are exactly the ones that encode why
the tokenizer is there.

ONE ENTRY MUTATES PROSE — the pointer in `wrap-up/SKILL.md`. A command nothing
calls is a command nobody runs, and the whole point of this one is that the close
reads it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

ERRORS = os.path.join("bin", "tk-errors")
WRAP_UP = os.path.join("skills", "wrap-up", "SKILL.md")

LISTED = "TheRefusals.test_a_refused_call_is_listed_with_its_tool_and_its_command"
NOT_ERROR = "TheRefusals.test_a_result_that_is_not_an_error_is_not_a_refusal"
STRUCTURED = "TheRefusals.test_a_structured_result_is_read_like_a_plain_one"
ORPHAN = "TheRefusals.test_a_refusal_with_no_call_recorded_is_still_reported"
SIDECHAIN = "TheRefusals.test_a_subagent_entry_in_the_parent_file_is_read_from_its_own"
DISPATCHED = "TheRefusals.test_a_dispatched_agents_refusals_are_this_sessions"
WORKFLOW_AGENT = "TheRefusals.test_an_agent_a_workflow_ran_is_read_too"
HALF_LINE = "TheRefusals.test_a_half_written_last_line_costs_nothing"
ESCAPE = "TheRefusals.test_a_control_sequence_in_a_message_is_stripped"
CAPPED = "TheRefusals.test_the_rows_are_capped_and_the_cut_is_declared"
CUT = "TheRefusals.test_a_long_message_is_cut_and_says_so"

CONFIRMED = "TheQueueInvariant.test_a_write_that_printed_its_success_line_is_confirmed"
UNCONFIRMED = "TheQueueInvariant.test_a_write_with_no_success_line_is_unconfirmed"
NO_RESULT = "TheQueueInvariant.test_a_write_whose_call_never_returned_is_unconfirmed"
HELP = "TheQueueInvariant.test_help_is_not_a_write"
SHORT_HELP = "TheQueueInvariant.test_the_short_help_flag_is_not_a_write_either"
SEMICOLON = ("TheQueueInvariant."
             "test_a_semicolon_ends_the_segment_before_an_unrelated_flag")
TWO_RECORDS = "TheQueueInvariant.test_a_result_written_in_two_records_is_read_whole"
LINE_END = ("TheQueueInvariant."
            "test_a_success_line_echoed_at_the_end_of_a_line_does_not_confirm")
READ_ONLY = "TheQueueInvariant.test_a_read_only_subcommand_is_not_a_write"
QUOTED = "TheQueueInvariant.test_a_quoted_mention_is_not_an_invocation"
READER = ("TheQueueInvariant."
          "test_an_unquoted_mention_after_a_reading_command_is_not_an_invocation")
DIR_FLAG = "TheQueueInvariant.test_the_dir_option_before_the_subcommand_is_skipped"
QUALIFIED = "TheQueueInvariant.test_a_path_qualified_invocation_is_seen"
TWO_CALLS = "TheQueueInvariant.test_two_invocations_in_one_command_are_counted_apart"
NO_OP = "TheQueueInvariant.test_an_honest_no_op_counts_as_a_success_line"
THREE_WRITES = ("TheQueueInvariant."
                "test_the_briefing_the_order_and_the_done_log_are_writes_too")
TOP_NO_OP = ("TheQueueInvariant."
             "test_a_bump_on_an_item_already_at_the_top_is_a_no_op_not_a_loss")
REWROTE = "TheQueueInvariant.test_a_rewritten_briefing_counts_as_a_write"
UNPARSED = "TheQueueInvariant.test_an_untokenizable_command_is_its_own_class_not_a_write"
HEREDOC = "TheQueueInvariant.test_a_heredoc_body_is_data_and_not_a_command"
COMMIT_MSG = "TheQueueInvariant.test_a_commit_message_naming_a_write_is_not_one"
AFTER_BODY = "TheQueueInvariant.test_a_write_after_a_heredoc_is_still_seen"
NOT_MINE = "TheQueueInvariant.test_an_untokenizable_command_without_the_bin_is_silent"
UNSPACED = "TheQueueInvariant.test_an_unspaced_separator_still_starts_an_invocation"
LATER_HELP = "TheQueueInvariant.test_a_later_help_does_not_suppress_an_earlier_write"
QUOTED_SEP = "TheQueueInvariant.test_a_separator_inside_quotes_is_not_a_boundary"
NEWLINE = "TheQueueInvariant.test_a_newline_between_two_calls_ends_the_first_one"
LATER_FLAG = ("TheQueueInvariant."
              "test_a_later_unrelated_flag_on_its_own_line_does_not_reach_back")
BLANK_LINES = "TheQueueInvariant.test_two_blank_lines_separate_as_one_does"
QUOTED_NEWLINE = ("TheQueueInvariant."
                  "test_a_newline_inside_the_items_own_text_is_not_a_boundary")
COMMENT = "TheQueueInvariant.test_a_trailing_comment_swallows_the_newline_after_it"
ANCHORED = "TheQueueInvariant.test_a_success_line_quoted_back_does_not_confirm_another_call"
BOTH = "TheQueueInvariant.test_a_refused_write_lands_in_both_classes"
TWO_LINES = "TheQueueInvariant.test_two_writes_of_one_kind_need_two_success_lines"
BOTH_LINES = "TheQueueInvariant.test_two_writes_with_both_lines_are_both_confirmed"

PINNED = "TheQueueSeam.test_every_pinned_shape_is_still_a_literal_in_tk_queue"
TABLES = "TheQueueSeam.test_the_two_tables_cover_the_same_subcommands"
REAL_SUB = "TheQueueSeam.test_every_watched_subcommand_is_a_real_one"
READS_OUT = "TheQueueSeam.test_the_read_only_subcommands_are_left_out"

EXIT_ZERO = "TheExitCodes.test_a_reading_that_happened_exits_zero_whatever_it_found"
UNREAD = "TheExitCodes.test_an_unread_transcript_is_not_a_clean_one"
NO_RECORD = "TheExitCodes.test_a_transcript_that_yielded_no_record_is_unread"
NO_SESSION = "TheExitCodes.test_a_missing_session_id_says_so"
USAGE = "TheExitCodes.test_a_bad_flag_exits_sixty_four"
GLOB = "TheExitCodes.test_a_wildcard_session_id_does_not_glob"
TWO_FILES = "TheExitCodes.test_two_transcripts_for_one_id_are_refused"
THE_FLAG = "TheExitCodes.test_a_transcript_path_wins_over_the_session_id"

ARGV = "TheSiblingSeam.test_main_takes_its_argv_like_every_sibling_bin"
POINTER = "TheSiblingSeam.test_the_wrap_up_sends_its_first_step_here"
GATE = "TheSiblingSeam.test_the_first_step_cannot_close_over_what_the_command_found"

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- class 1: the refusals -----------------------------------------------
    ("the harness's own verdict is ignored, so nothing is ever refused",
     "                    if block.get(\"is_error\"):",
     "                    if False:",
     [LISTED, STRUCTURED, ORPHAN, HALF_LINE, ESCAPE, CAPPED, EXIT_ZERO, THE_FLAG,
      BOTH],
     ERRORS),

    ("every result is a refusal, so the report is noise and gets skipped",
     "                    if block.get(\"is_error\"):",
     "                    if True:",
     [NOT_ERROR, EXIT_ZERO],
     ERRORS),

    ("a dispatched agent's line is reported twice — once from each file",
     """                if source == path and record.get("isSidechain"):
                    continue          # the agent's own file carries this line
""",
     "",
     [SIDECHAIN], ERRORS),

    ("the agents this session dispatched are not read at all",
     "    for source in [path] + subagent_transcripts(path):",
     "    for source in [path]:",
     [DISPATCHED, WORKFLOW_AGENT], ERRORS),

    ("only the agents at the top level are read, and a Workflow's are missed",
     '''    return sorted(glob.glob(os.path.join(glob.escape(base), "subagents",
                                         "**", "*.jsonl"), recursive=True))''',
     '''    return sorted(glob.glob(os.path.join(glob.escape(base), "subagents",
                                         "*.jsonl")))''',
     [WORKFLOW_AGENT], ERRORS),

    ("a reading that survived nothing reports a clean session",
     """    if not considered:
        no_transcript(f"{plain(path)} yielded no record of this session")
""",
     "",
     [NO_RECORD], ERRORS),

    ("a half-written last line crashes the reading instead of being skipped",
     """                except ValueError:
                    continue""",
     """                except ValueError:
                    raise""",
     [HALF_LINE], ERRORS),

    ("the row names the tool and not the call, so the reader still has to grep",
     """    for key in ("command", "file_path", "path", "pattern", "url", "prompt"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
""",
     "",
     [LISTED], ERRORS),

    ("a structured result reads as empty, and every one of them as silent",
     """    if isinstance(content, list):
        return "\\n".join(part.get("text") or "" for part in content
                         if isinstance(part, dict))
""",
     "",
     [STRUCTURED], ERRORS),

    ("a value from the file reaches the terminal with its escapes intact",
     '    return re.sub(r"[\\x00-\\x1f\\x7f]", "?", str(value))',
     "    return str(value)",
     [ESCAPE], ERRORS),

    ("the cap is ignored, so a long session prints hundreds of rows",
     "        for row in rows[:limit]:",
     "        for row in rows:",
     [CAPPED], ERRORS),

    ("the headline stops being the first line, and every seam reading it breaks",
     '    print(f"{len(refusals)} refused tool call(s), "',
     '    print(f"tk-errors says: {len(refusals)} refused tool call(s), "',
     [LISTED, CONFIRMED], ERRORS),

    # -- class 2: the queue invariant ----------------------------------------
    ("a write with no success line is taken as confirmed — the silent loss itself",
     "        if claimed < printed:",
     "        if True:",
     [UNCONFIRMED, DIR_FLAG, QUALIFIED, TWO_CALLS, ANCHORED, BOTH, TWO_LINES],
     ERRORS),

    ("no output ever confirms a write, so every write is reported as lost",
     "        if claimed < printed:",
     "        if False:",
     [CONFIRMED, NO_OP, BOTH_LINES], ERRORS),

    ("one success line answers for every invocation of its kind in the call",
     "        claimed = spent.get((key, sub), 0)",
     "        claimed = 0",
     [TWO_LINES], ERRORS),

    ("a call whose result never came back is taken as confirmed",
     """        if text is None:
            unconfirmed.append(Unconfirmed(stamp, sub, command,
                                           "the call returned nothing"))
            continue""",
     """        if text is None:
            continue""",
     [NO_RESULT], ERRORS),

    ("`--help` counts as a write — the report cries wolf on every lookup",
     """            if not any(flag in segment for flag in HELP_FLAGS):
                out.append((rest[position], ""))""",
     '            out.append((rest[position], ""))',
     [HELP], ERRORS),

    ("only the first invocation in a compound command is counted",
     """            if not any(flag in segment for flag in HELP_FLAGS):
                out.append((rest[position], ""))""",
     """            if not any(flag in segment for flag in HELP_FLAGS) and not out:
                out.append((rest[position], ""))""",
     [TWO_CALLS], ERRORS),

    ("the plain splitter is back, and an unspaced `;` hides the call after it",
     """    lexer = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION)
    lexer.whitespace = " \\t\\r"            # `\\n` is a separator here, not a space
    lexer.whitespace_split = True         # words, not the lexer's default atoms""",
     "    return shlex.split(command, comments=True)\n    lexer = None",
     [UNSPACED, LATER_FLAG], ERRORS),

    ("the newline goes back to being whitespace, and a later `-h` reaches back",
     '    lexer.whitespace = " \\t\\r"            # `\\n` is a separator here, not a space\n',
     "",
     [LATER_FLAG, BLANK_LINES], ERRORS),

    ("the newline is not a separator, so the segment runs past it",
     'SEPARATORS = (";", "|", "||", "&", "&&", "\\n")',
     'SEPARATORS = (";", "|", "||", "&", "&&")',
     [LATER_FLAG, BLANK_LINES], ERRORS),

    ("a run of newlines is not collapsed, so a blank line stops separating",
     '''    return ["\\n" if token and not token.strip("\\n") else token
            for token in lexer]           # `commenters` is already `#` by default''',
     "    return list(lexer)",
     [BLANK_LINES], ERRORS),

    ("the command is split on newlines first, which cuts a quoted item in two",
     """    lexer = shlex.shlex(command, posix=True, punctuation_chars=PUNCTUATION)
    lexer.whitespace = " \\t\\r"            # `\\n` is a separator here, not a space
    lexer.whitespace_split = True         # words, not the lexer's default atoms""",
     """    out = []
    for one in command.split("\\n"):
        out += shlex.split(one, comments=True) + ["\\n"]
    return out
    lexer = None""",
     [QUOTED_NEWLINE, UNSPACED], ERRORS),

    ("only a separator ends the segment, so a commented line lets `--help` back",
     "                if later in SEPARATORS or os.path.basename(later) == QUEUE_BIN:",
     "                if later in SEPARATORS:",
     [COMMENT], ERRORS),

    ("the segment runs to the end of the command, and any later `--help` reaches back",
     """                if later in SEPARATORS or os.path.basename(later) == QUEUE_BIN:
                    break
""",
     "",
     [LATER_HELP, NEWLINE], ERRORS),

    ("`--help` is matched inside a token, so the item's own text can suppress it",
     "            if not any(flag in segment for flag in HELP_FLAGS):",
     '            if not any(flag in " ".join(segment) for flag in HELP_FLAGS):',
     [QUOTED_SEP], ERRORS),

    ("a name read by another command counts as an invocation",
     """        if index and os.path.basename(tokens[index - 1]) in READERS:
            continue                  # the command reads this name, it does not run it
""",
     "",
     [READER], ERRORS),

    ("the option's VALUE is read as the subcommand, so no write is ever seen",
     "            position += 2 if flag in VALUE_FLAGS else 1",
     "            position += 1",
     [DIR_FLAG], ERRORS),

    ("only a bare `tk-queue` counts, so every path-qualified call is missed",
     "        if os.path.basename(token) != QUEUE_BIN:",
     "        if token != QUEUE_BIN:",
     [QUALIFIED], ERRORS),

    ("the invocations are found by a regex over the raw command, not by tokens",
     """    if QUEUE_BIN not in command:
        # The cheap gate, and a correctness one: without it the tokenizer's
        # failure below would report every unbalanced quote in the session as an
        # unconfirmed queue write, which is a wrong number in the class this
        # command exists to count.
        return []
    try:""",
     """    if QUEUE_BIN not in command:
        return []
    return [(m, "") for m in re.findall(
        rf"{re.escape(QUEUE_BIN)}\\s+({'|'.join(SUCCESS)})\\b", command)]
    try:""",
     [QUOTED, HELP, DIR_FLAG], ERRORS),

    ("an unbalanced quote anywhere in the session is reported as a queue write",
     """    if QUEUE_BIN not in command:
        # The cheap gate, and a correctness one: without it the tokenizer's
        # failure below would report every unbalanced quote in the session as an
        # unconfirmed queue write, which is a wrong number in the class this
        # command exists to count.
        return []
""",
     "",
     [NOT_MINE], ERRORS),

    ("a command the reader could not parse is skipped rather than reported",
     '        return [(UNPARSED, f"the command does not tokenize ({exc})")]',
     "        return []",
     [UNPARSED], ERRORS),

    ("a heredoc body is read as command text, and its prose as an invocation",
     "        tokens = tokenize(strip_heredocs(command))",
     "        tokens = tokenize(command)",
     [HEREDOC, COMMIT_MSG], ERRORS),

    ("the heredoc terminator is ignored, so the rest of the command is eaten",
     """            if line.strip() == awaiting[0]:
                awaiting.pop(0)       # `<<-` allows the terminator to be indented
            continue""",
     "            continue",
     [AFTER_BODY], ERRORS),

    ("the regex fallback is back, and it reads the prose inside a heredoc",
     '        return [(UNPARSED, f"the command does not tokenize ({exc})")]',
     '''        found = [sub for sub in SUCCESS
                 if re.search(rf"{re.escape(QUEUE_BIN)}[^;&|\\n]*?\\b{sub}\\b", command)]
        return [(sub, f"does not tokenize ({exc})") for sub in found]''',
     [UNPARSED], ERRORS),

    ("the third class never reaches the headline, and nobody reads its count",
     '          f"{len(unparsed)} command(s) not parsed")',
     '          "")',
     [UNPARSED, HEREDOC], ERRORS),

    ("the success line is matched anywhere in the output, quotes included",
     """    return sum(1 for line in text.splitlines()
               if any(re.search(p, line.strip()) for p in patterns))""",
     """    return sum(1 for line in text.splitlines()
               if any(re.search(p.strip("^$"), line) for p in patterns))""",
     [ANCHORED], ERRORS),

    ("an honest no-op is read as a failed write",
     '    "release": (r"^\\S+ released — ", r"^\\S+ carries no claim — nothing to release$"),',
     '    "release": (r"^\\S+ released — ",),',
     [NO_OP, TABLES], ERRORS),

    ("the briefing is written and nobody checks that it was",
     '    "handoff": (r"^(?:re)?wrote \\S*handoff-T\\d+\\.md$",),\n',
     "",
     [THREE_WRITES, TABLES], ERRORS),

    ("the queue's order is rewritten and nobody checks that it was",
     '''    "bump": (r"^\\S+ → top of the queue$",
             r"^\\S+ is already at the top of the queue$"),
''',
     "",
     [THREE_WRITES, TABLES], ERRORS),

    ("the done-log is folded and nobody checks that it was",
     '    "migrate": (r"^\\d+ \\[x\\] item\\(s\\) → done-log;",),\n',
     "",
     [THREE_WRITES, TABLES], ERRORS),

    ("a re-written briefing reads as a failed one",
     r'    "handoff": (r"^(?:re)?wrote \S*handoff-T\d+\.md$",),',
     r'    "handoff": (r"^wrote \S*handoff-T\d+\.md$",),',
     [REWROTE], ERRORS),

    ("a bump on an item already at the top reads as a failed write",
     '''    "bump": (r"^\\S+ → top of the queue$",
             r"^\\S+ is already at the top of the queue$"),''',
     '    "bump": (r"^\\S+ → top of the queue$",),',
     [TOP_NO_OP, TABLES], ERRORS),

    # -- the seam with tk-queue ----------------------------------------------
    ("a pinned shape drifts from the line tk-queue actually prints",
     '    "edit": (\'print(f"{label} updated")\',),',
     '    "edit": (\'print(f"{label} was updated")\',),',
     [PINNED], ERRORS),

    ("a subcommand is watched that tk-queue does not have",
     """    "migrate": (r"^\\d+ \\[x\\] item\\(s\\) → done-log;",),
}""",
     """    "migrate": (r"^\\d+ \\[x\\] item\\(s\\) → done-log;",),
    "purge": (r"^\\S+ purged$",),
}""",
     [REAL_SUB, TABLES], ERRORS),

    ("a read is counted as a write, so every `list` reports a mismatch",
     '    "add": (r"^added T\\S*: ",),\n    "edit"',
     '    "add": (r"^added T\\S*: ",),\n    "list": (r"^never$",),\n    "edit"',
     [READ_ONLY, READS_OUT, TABLES], ERRORS),

    ("`-h` drops out of the help list, and a flag lookup reports a lost write",
     'HELP_FLAGS = ("--help", "-h")',
     'HELP_FLAGS = ("--help",)',
     [SHORT_HELP], ERRORS),

    ("the separators are emptied, and every later flag reaches back",
     'SEPARATORS = (";", "|", "||", "&", "&&", "\\n")',
     "SEPARATORS = ()",
     [SEMICOLON, LATER_FLAG, BLANK_LINES], ERRORS),

    ("the `;` alone stops separating, and the commonest boundary goes blind",
     'SEPARATORS = (";", "|", "||", "&", "&&", "\\n")',
     'SEPARATORS = ("|", "||", "&", "&&", "\\n")',
     [SEMICOLON], ERRORS),

    ("a second result record overwrites the first instead of continuing it",
     '                        results[key] = results.get(key, "") + text',
     "                        results[key] = text",
     [TWO_RECORDS], ERRORS),

    ("the cut is silent, and half a refusal message reads like the whole one",
     '    return folded if len(folded) <= chars else folded[:chars] + " […cut]"',
     "    return folded[:chars]",
     [CUT], ERRORS),

    ("the success line is matched without its opening anchor",
     """    return sum(1 for line in text.splitlines()
               if any(re.search(p, line.strip()) for p in patterns))""",
     """    return sum(1 for line in text.splitlines()
               if any(re.search(p.lstrip("^"), line.strip()) for p in patterns))""",
     [LINE_END], ERRORS),

    # -- the exit codes ------------------------------------------------------
    ("an unread transcript exits 0, so nobody read reads as nothing wrong",
     "EXIT_NO_TRANSCRIPT = 2",
     "EXIT_NO_TRANSCRIPT = 0",
     [UNREAD, NO_SESSION, GLOB, TWO_FILES, NO_RECORD], ERRORS),

    ("a run that found something exits non-zero, and the close records a refusal",
     "    return EXIT_READ",
     "    return 1 if (refusals or unconfirmed) else EXIT_READ",
     [EXIT_ZERO], ERRORS),

    ("the failure says nothing about being unread, which is the whole warning",
     '''    print("tk-errors: nothing was read — this is not a clean session, it is an "
          "unread one", file=sys.stderr)
''',
     "",
     [UNREAD], ERRORS),

    ("a mistyped flag reads as `no transcript`, and the seam decides on it",
     "EXIT_USAGE = 64                       # sysexits.h EX_USAGE; argparse's own 2 collides",
     "EXIT_USAGE = 2",
     [USAGE], ERRORS),

    ("a limit of zero is accepted, and the rows vanish with no error",
     """    if args.limit < 1:
        parser.error("--limit must be at least 1")
""",
     "",
     [USAGE], ERRORS),

    ("the session id reaches the glob unescaped, and matches a stranger's file",
     'f"{glob.escape(session_id)}.jsonl"',
     'f"{session_id}.jsonl"',
     [GLOB], ERRORS),

    ("two files for one id are resolved by sorting, in silence",
     """    if len(hits) > 1:
        no_transcript("two transcripts carry this session id: "
                      + ", ".join(plain(h) for h in hits))
""",
     "",
     [TWO_FILES], ERRORS),

    ("`--transcript` is ignored, so the flag reads the wrong session",
     "    path = args.transcript",
     "    path = None",
     [THE_FLAG], ERRORS),

    ("`main` stops taking its argv, and no caller can drive the parser",
     "def main(argv=None):",
     "def main(argv=()):",
     [ARGV], ERRORS),

    # -- the prose that calls it ---------------------------------------------
    ("the close stops naming the command, so nobody ever runs it",
     "`tk-errors` (refusals and unconfirmed\nqueue writes) ",
     "",
     [POINTER], WRAP_UP),

    ("the step closes without naming what it printed, so nobody acts on it",
     "every session finding, refusal and unconfirmed queue write was",
     "every session finding was",
     [GATE], WRAP_UP),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_errors"))
