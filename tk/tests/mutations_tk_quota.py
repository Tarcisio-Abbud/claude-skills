#!/usr/bin/env python3
"""Mutation harness for the `tk-quota` suite — puts each defect back.

Run: python3 tk/tests/mutations_tk_quota.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires every one of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

NINE ENTRIES MUTATE THE WRITER, and they are why this file was rewritten. When
the writing lived in the site's statusline script — outside this repo, outside
any suite — a system lens found four wrong-number defects in it on 2026-09-03,
against zero in the reading half beside it, which had a suite and mutants. The
writer is in the bin now, so it is mutated like everything else.

THE ENTRIES THAT CARRY THE DESIGN are the boundary one and the freshness ones.
`the write is gated on the 5-hour window` restores the measured defect: Claude
Code drops a window as it resets, so the render at the boundary carries a live
weekly and no 5-hour, and a writer waiting for the 5-hour records nothing while
the reader vouches for the previous weekly. The freshness three restore the
modelling error underneath it — staleness treated as ONE question (is the window
open) when it is two (and is this reading fresh), which lets a six-day-old weekly
through a window that stays open for seven.

SEVENTEEN ENTRIES MUTATE THE FLOOR, and they carry a design point rather than a
guard: `--estimate` prints a computed number, and the whole risk is that it be
read as a measured one. So every mark that separates the two lines is mutated in
BOTH directions — stripped from the estimate, and pasted onto the reading. A mark
that both lines carry separates nothing, and an entry that only strips it leaves
that half unproved. Two more hold the rate on the WINDOW: the weekend measured the
5-hour window alone, and the same pp/h against a budget seven days wide is an
overstatement, which is the one thing a floor may never be.

FOUR ENTRIES MUTATE PROSE, in `skills/kickoff/WINDOW.md`: a command the wall
does not name is a command nobody runs, a wall that promises exit 0 means good
numbers hides the partial answer this command can give, and a wall naming only
the two refusals lets a reading that survives both be read as current when it is
days behind.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

QUOTA = os.path.join("bin", "tk-quota")
WINDOW = os.path.join("skills", "kickoff", "WINDOW.md")

W_BOTH = "TheWriter.test_both_windows_are_recorded"
W_BOUNDARY = "TheWriter.test_a_render_at_the_five_hour_boundary_is_still_recorded"
W_OMIT = "TheWriter.test_an_absent_window_is_omitted_and_never_written_as_null"
W_KEEP = "TheWriter.test_a_payload_with_no_window_leaves_a_good_sidecar_alone"
W_ESCAPE = "TheWriter.test_a_value_carrying_a_backslash_still_writes_parseable_json"
W_STDIN = "TheWriter.test_an_unreadable_payload_records_nothing"
W_NOTOBJ = "TheWriter.test_a_payload_that_is_not_an_object_records_nothing"
W_NOTEMP = "TheWriter.test_no_temp_file_survives_a_successful_write"
W_ORPHAN = "TheWriter.test_an_orphan_temp_file_is_cleared_and_a_fresh_one_is_kept"

ONE_LINE = "TheNumbers.test_both_windows_are_printed_on_one_line"
DAYS = "TheNumbers.test_the_weekly_window_is_spelled_in_days"
TRUNC = "TheNumbers.test_a_fractional_percentage_is_truncated_as_the_statusline_truncates"
DEFAULT = "TheNumbers.test_the_default_sidecar_is_the_one_read_when_no_flag_is_given"

RESET = "AWindowThatCannotBeVouchedFor.test_a_reset_that_has_passed_is_not_a_low_percentage"
OLDER = "AWindowThatCannotBeVouchedFor.test_a_reading_older_than_its_own_window_is_refused"
INSIDE = "AWindowThatCannotBeVouchedFor.test_a_reading_inside_its_own_window_is_reported"
NO_WRITTEN = "AWindowThatCannotBeVouchedFor.test_a_sidecar_that_does_not_say_when_it_was_written_is_refused"
BOOL = "AWindowThatCannotBeVouchedFor.test_a_percentage_that_is_a_boolean_is_not_a_percentage"
PARTIAL = "AWindowThatCannotBeVouchedFor.test_one_window_refused_still_prints_the_other_and_says_why"
AGE_SAID = "AWindowThatCannotBeVouchedFor.test_a_reading_still_inside_its_window_but_days_old_says_how_old"
AGE_QUIET = "AWindowThatCannotBeVouchedFor.test_a_reading_from_this_minute_carries_no_age"

NO_FILE = "WhenThereIsNoNumber.test_no_sidecar_at_all"
BAD_JSON = "WhenThereIsNoNumber.test_a_sidecar_that_is_not_json"
NOT_OBJ = "WhenThereIsNoNumber.test_a_sidecar_that_is_not_an_object"

FLAT_MISSING = "WhatComesFromOutsideThisProcess.test_the_missing_file_arm_prints_flat"
FLAT_UNREAD = "WhatComesFromOutsideThisProcess.test_the_unreadable_file_arm_prints_flat"
FLAT_REFUSED = "WhatComesFromOutsideThisProcess.test_the_every_window_refused_arm_prints_flat"

THE_FLAG = "TheEdgesOfTheContract.test_the_file_flag_is_the_file_that_gets_read"
TYPO = "TheEdgesOfTheContract.test_a_mistyped_flag_does_not_read_as_no_number"

E = "TheEstimate."
E_MARK = E + "test_the_line_carries_the_mark_that_says_it_is_not_a_reading"
E_NOMARK = E + "test_the_reading_line_carries_no_such_mark"
E_FLOOR = E + "test_the_estimate_is_qualified_as_a_floor"
E_NOFLOOR = E + "test_the_reading_line_is_qualified_as_neither"
E_DIFFER = E + "test_the_two_lines_are_not_the_same_line"
E_AGE = E + "test_the_line_carries_the_age_of_the_anchor"
E_RATE = E + "test_the_line_carries_the_rate_that_was_applied"
E_ANCHOR = E + "test_the_line_carries_the_percentage_the_anchor_actually_read"
E_CLIMB = E + "test_the_floor_climbs_with_the_age_and_the_agent_count"
E_ZERO = E + "test_no_agents_at_all_leaves_the_floor_at_the_anchor"
E_RECAL = E + "test_the_rate_can_be_recalibrated_from_a_runs_own_ledger"
E_CLAMP = E + "test_the_floor_never_climbs_past_a_hundred"
E_WEEKLY = E + "test_the_weekly_window_gets_no_floor_and_the_refusal_is_said_aloud"
E_WEEKLY_RATE = E + "test_a_recalibrated_rate_does_not_unlock_the_weekly_either"

N = "TheEstimateWhenItCannotAnswer."
E_RESET = N + "test_a_window_that_has_reset_gets_no_floor_either"
E_OLD = N + "test_a_reading_older_than_its_own_window_gets_no_floor_either"
E_NOFILE = N + "test_no_sidecar_at_all_is_still_exit_2"
E_CORRUPT = N + "test_a_corrupt_sidecar_is_still_exit_2"

F = "TheFlagsOfTheEstimate."
F_NOCOUNT = F + "test_the_estimate_without_a_count_is_a_usage_error_not_a_zero"
F_COUNTALONE = F + "test_a_count_without_the_estimate_is_a_usage_error"
F_RATEALONE = F + "test_a_rate_without_the_estimate_is_a_usage_error"
F_WRITE = F + "test_writing_and_estimating_are_not_asked_together"
F_NEG = F + "test_a_negative_count_is_a_usage_error"
F_NAN = F + "test_a_count_that_is_not_a_number_is_a_usage_error_not_no_number"

CALLS_IT = "TheProseThatCallsIt.test_the_wall_sends_the_reader_to_the_command"
SAYS_REFUSAL = "TheProseThatCallsIt.test_the_wall_says_the_reading_can_be_a_previous_windows"
SAYS_PARTIAL = "TheProseThatCallsIt.test_the_wall_describes_the_partial_answer"
SAYS_AGE = "TheProseThatCallsIt.test_the_wall_says_an_old_reading_announces_its_age"

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- the writer: the half that had no suite at all -----------------------
    ("the write is gated on the 5-hour window, so the boundary render is thrown away",
     "    if not found:",
     '    if "five_hour" not in found:',
     [W_BOUNDARY], QUOTA),

    ("a window whose values are null is recorded as null instead of omitted",
     "        if found is None:\n            continue",
     '        if found is None:\n            bad = limits.get(key) or {}\n            out[key] = {"used_percentage": bad.get("used_percentage"), "resets_at": bad.get("resets_at")}\n            continue',
     [W_OMIT], QUOTA),

    ("a payload carrying no window overwrites the good sidecar anyway",
     "    found = windows_from_payload(payload)\n    if not found:",
     "    found = windows_from_payload(payload)\n    if False:",
     [W_KEEP], QUOTA),

    ("the sidecar is emitted by hand instead of by a JSON emitter",
     "                json.dump(found, fh)",
     '                fh.write("{\\"written_by\\": \\"" + str(payload.get("session_id")) + "\\"}")',
     [W_BOTH, W_ESCAPE], QUOTA),

    ("an unreadable payload on stdin is treated as an empty object",
     "        except (ValueError, OSError) as exc:\n            print(f\"tk-quota: unreadable payload on stdin: {plain(exc)}\", file=sys.stderr)\n            return EXIT_NOT_RECORDED",
     "        except (ValueError, OSError):\n            payload = {}",
     [W_STDIN], QUOTA),

    ("a payload that is not an object is walked anyway",
     "        if not isinstance(payload, dict):\n            print(\"tk-quota: the payload on stdin is not an object\", file=sys.stderr)\n            return EXIT_NOT_RECORDED",
     "        if False:\n            pass",
     [W_NOTOBJ], QUOTA),

    ("the temp file is left beside the sidecar instead of replacing it",
     "            os.replace(tmp, path)",
     "            import shutil; shutil.copyfile(tmp, path)",
     [W_NOTEMP], QUOTA),

    ("orphan temp files are never cleared",
     "        clear_orphans(directory, now)",
     "        pass",
     [W_ORPHAN], QUOTA),

    ("a fresh temp file is swept along with the orphans",
     "                if now - os.stat(path).st_mtime > ORPHAN_AGE:",
     "                if True:",
     [W_ORPHAN], QUOTA),

    # -- freshness: the second question, which collapsing loses --------------
    ("the reading's age is never asked, only whether the window is open",
     "    if written < opened:",
     "    if False:",
     [OLDER, E_OLD], QUOTA),

    ("a sidecar with no written_at is vouched for",
     "    if written is None:\n        return None, \"the sidecar does not say when it was written\"",
     "    if written is None:\n        written = now",
     [NO_WRITTEN], QUOTA),

    ("the freshness test is inverted, so only ancient readings pass",
     "    if written < opened:",
     "    if written >= opened:",
     [INSIDE], QUOTA),

    # The map that carries the design: one entry per window, label beside
    # length. As two maps a hundred lines apart, nothing here could restore
    # the drift between them — this restores its consequence instead.
    ("both windows are judged against one length, so the weekly is asked for five hours",
     '    "seven_day": Window("7d", 7 * 86400),',
     '    "seven_day": Window("7d", 5 * 3600),',
     [INSIDE], QUOTA),

    ("a window whose reset has passed is reported anyway",
     "    if resets <= now:",
     "    if False:",
     [RESET, E_RESET], QUOTA),

    ("a boolean is accepted as a percentage",
     "    if isinstance(value, bool) or not isinstance(value, (int, float)):",
     "    if not isinstance(value, (int, float)):",
     [BOOL], QUOTA),

    # -- the third question, disclosed instead of refused --------------------
    # The two refusals leave a reading that is inside its own window and still
    # days behind. Silence there is what lets a floor be read as the current
    # spend; announcing it on every reading is what makes the announcement mean
    # nothing. Both directions are mutated.
    ("a reading days old is reported with no word about its age",
     "    if value.age > STALE_AFTER:",
     "    if False:",
     [AGE_SAID], QUOTA),

    ("every reading is stamped with an age, so the stamp stops meaning anything",
     "    if value.age > STALE_AFTER:",
     "    if True:",
     [AGE_QUIET], QUOTA),

    ("the wall names only the refusals, so a days-old figure reads as current",
     "**A reading that survives both\nand is still old SAYS SO**: `(read 4d02h ago)` on the line means nothing has rendered since, so\nthe percentage is a floor on what has been spent, never the current figure.",
     "A reading that survives both is the current figure.",
     [SAYS_AGE], WINDOW),

    # -- what the numbers say ------------------------------------------------
    ("the two windows are printed on separate lines",
     'print(" · ".join(parts))',
     'print("\\n".join(parts))',
     [ONE_LINE], QUOTA),

    ("the weekly window is spelled in hours, so 4d11h arrives as 107h",
     "    if seconds >= 86400:",
     "    if False:",
     [DAYS], QUOTA),

    ("the percentage is rounded, and 99.6 becomes a 100% the bar never showed",
     '    said = f"{spec.label} {int(value.used)}% used, {spell(value.left)} left"',
     '    said = f"{spec.label} {value.used:.0f}% used, {spell(value.left)} left"',
     [TRUNC], QUOTA),

    ("a refused window vanishes with no word, so the seam cannot tell it lost an answer",
     "    for line in refused:\n        print(f\"tk-quota: {line}\", file=sys.stderr)",
     "    pass",
     [PARTIAL], QUOTA),

    # -- resolving the file --------------------------------------------------
    ("the default sidecar path is not expanded, so the documented call finds nothing",
     "    path = args.file or os.path.expanduser(SIDECAR)",
     "    path = args.file or SIDECAR",
     [DEFAULT], QUOTA),

    # Named for THE_FLAG alone, deliberately. The default-path test calls with
    # no `--file`, so a mutant that ignores `--file` cannot change its outcome —
    # naming it here would demand a failure the test has no way to produce.
    ("--file is ignored and the default sidecar is read",
     "    path = args.file or os.path.expanduser(SIDECAR)",
     "    path = os.path.expanduser(SIDECAR)",
     [THE_FLAG], QUOTA),

    ("a missing sidecar is not told apart from a corrupt one",
     "    except FileNotFoundError:",
     "    except NotADirectoryError:",
     [NO_FILE], QUOTA),

    ("a half-written sidecar crashes instead of refusing",
     "    except (OSError, ValueError) as exc:",
     "    except OSError as exc:",
     [BAD_JSON], QUOTA),

    ("a sidecar holding a list is walked as though it were an object",
     "    if not isinstance(payload, dict):\n        no_number(f\"{plain(path)} does not hold an object\")",
     "    if False:\n        pass",
     [NOT_OBJ], QUOTA),

    ("a mistyped flag exits 2 — indistinguishable from `no number, use judgement`",
     "        sys.exit(EXIT_USAGE)",
     "        sys.exit(EXIT_NO_NUMBER)",
     [TYPO, F_NAN], QUOTA),

    # -- what came from outside this process ---------------------------------
    ("the escape stripper passes everything through",
     '    return re.sub(r"[\\x00-\\x1f\\x7f]", "?", str(value))',
     "    return str(value)",
     [FLAT_MISSING, FLAT_UNREAD, FLAT_REFUSED], QUOTA),

    ("the unreadable-file arm echoes the path and the error raw",
     '        no_number(f"cannot read {plain(path)}: {plain(exc)}")',
     '        no_number(f"cannot read {path}: {exc}")',
     [FLAT_UNREAD], QUOTA),

    ("the every-window-refused arm echoes the path raw",
     '        no_number("no window in " + plain(path) + " can be vouched for — "',
     '        no_number("no window in " + path + " can be vouched for — "',
     [FLAT_REFUSED], QUOTA),

    # -- the floor, and the marks that keep it from passing as a reading -----
    # Taking an estimate for a measurement is what put wrong lines in the
    # 05-07/09 ledger. Every mark is mutated in BOTH directions: stripped from
    # the estimate, and pasted onto the reading — a mark both lines carry
    # separates nothing, and a suite that only checked the estimate stays green.

    ("the estimate line drops the mark that says it is not a reading",
     '    return (f"{spec.label} estimate: at least {int(floor)}% used, "',
     '    return (f"{spec.label} {int(floor)}% used, "',
     [E_MARK, E_FLOOR], QUOTA),

    ("the reading line is stamped with the estimate's own marks",
     '    said = f"{spec.label} {int(value.used)}% used, {spell(value.left)} left"',
     '    said = f"{spec.label} estimate: at least {int(value.used)}% used, {spell(value.left)} left"',
     [E_NOMARK, E_NOFLOOR], QUOTA),

    ("the floor is printed bare, with no rate, no anchor and no age to audit it",
     '''    return (f"{spec.label} estimate: at least {int(floor)}% used, "
            f"{spell(value.left)} left (floor from {int(value.used)}% read "
            f"{spell(value.age)} ago, {applied:g} pp/h = {opus} Opus x {rate:g})")''',
     '    return f"{spec.label} {int(floor)}% used, {spell(value.left)} left"',
     [E_AGE, E_RATE, E_ANCHOR], QUOTA),

    ("estimate mode prints the reading line, so a floor arrives dressed as a measurement",
     '''        else:
            rate = spec.rate if estimate.rate is None else estimate.rate
            parts.append(estimate_line(spec, value, estimate.opus, rate))''',
     "        else:\n            parts.append(reading_line(spec, value))",
     [E_DIFFER, E_CLIMB], QUOTA),

    # -- the arithmetic ------------------------------------------------------

    ("the anchor's age is never applied, so the floor never leaves the anchor",
     "    climbed = applied * (value.age / 3600)",
     "    climbed = 0",
     [E_CLIMB, E_CLAMP, E_RECAL], QUOTA),

    ("the agent count is ignored, so one Opus and five cost the same",
     "    applied = rate * opus",
     "    applied = rate",
     [E_CLIMB, E_ZERO, E_RATE], QUOTA),

    ("the floor is not clamped, and prints a percentage above a hundred",
     "    floor = min(100.0, value.used + climbed)",
     "    floor = value.used + climbed",
     [E_CLAMP], QUOTA),

    # -- the rate belongs to the window, not to the flag ---------------------
    # Both weekend measurements are of the 5-hour window. The same pp/h against
    # a budget seven days wide prints a number nobody measured, in the alarming
    # direction — and a floor that overstates is not a floor.

    ("the weekly window is given the 5-hour window's measured rate",
     '    "seven_day": Window("7d", 7 * 86400),   # never measured; see Window.rate',
     '    "seven_day": Window("7d", 7 * 86400, RATE_PER_OPUS),',
     [E_WEEKLY, E_WEEKLY_RATE], QUOTA),

    ("a window with no measured rate vanishes instead of being refused out loud",
     '''        elif spec.rate is None:
            # Said aloud, through the same channel a refused window uses. A
            # window that simply vanished here would read as one nobody asked
            # about, and the 5-hour line beside it as the whole answer.
            refused.append(f"{spec.label}: no pp/h rate has been measured for "
                           "it, so no floor can be computed")''',
     "        elif spec.rate is None:\n            continue",
     [E_WEEKLY, E_WEEKLY_RATE], QUOTA),

    ("--rate silently promotes a window that had no measured rate",
     "        elif spec.rate is None:",
     "        elif spec.rate is None and estimate.rate is None:",
     [E_WEEKLY_RATE], QUOTA),

    # -- the anchor is not optional ------------------------------------------

    ("the estimate answers from the flags alone, without consulting the sidecar",
     "    parts, refused = report(read_sidecar(path), now, estimate)",
     '''    if estimate is not None:
        print(f"5h estimate: at least {estimate.opus * 10}% used, 0h00m left "
              f"(floor from 0% read 0h00m ago, {estimate.opus * 10} pp/h)")
        return EXIT_OK
    parts, refused = report(read_sidecar(path), now, estimate)''',
     [E_NOFILE, E_CORRUPT], QUOTA),

    # -- the flags -----------------------------------------------------------

    ("--estimate with no count defaults to zero agents instead of refusing",
     '''        if args.opus is None:
            parser.error("--estimate needs --opus N: nothing here can count the agents")''',
     "        if args.opus is None:\n            args.opus = 0",
     [F_NOCOUNT], QUOTA),

    ("--opus and --rate are accepted without --estimate, and quietly do nothing",
     '''    elif args.opus is not None or args.rate is not None:
        parser.error("--opus and --rate only mean something with --estimate")''',
     "    elif False:\n        pass",
     [F_COUNTALONE, F_RATEALONE], QUOTA),

    ("--write and --estimate are asked together and the write silently wins",
     '''        if args.write:
            parser.error("--write records a reading and --estimate reads one back")''',
     "        if False:\n            pass",
     [F_WRITE], QUOTA),

    ("a negative agent count is accepted, and the floor walks backwards",
     '''        if args.opus < 0 or (args.rate is not None and args.rate < 0):
            parser.error("--opus and --rate are never negative")''',
     '''        if False:
            parser.error("--opus and --rate are never negative")''',
     [F_NEG], QUOTA),

    ("the agent count is taken as text, so `two` reaches the arithmetic",
     '    parser.add_argument("--opus", type=int, default=None,',
     '    parser.add_argument("--opus", default=None,',
     [F_NAN], QUOTA),

    # -- the prose that calls it ---------------------------------------------
    ("the wall never names the command",
     "**Read the quota before dispatching, not only after it fails.** `../../bin/tk-quota` prints",
     "**Read the quota before dispatching, not only after it fails.** The statusline prints",
     [CALLS_IT], WINDOW),

    ("the wall drops the warning that the reading can be a previous window's",
     "It **exits 2 rather than report a figure it cannot vouch for**, and two independent things can",
     "It reports what the sidecar holds, and two independent things can",
     [SAYS_REFUSAL], WINDOW),

    ("the wall never says exit 0 can be a partial answer",
     "**Exit 0 can still be a partial answer: it prints one window where it can only vouch for one.**",
     "**Exit 0 means the numbers are good.**",
     [SAYS_PARTIAL], WINDOW),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_quota"))
