#!/usr/bin/env python3
"""Mutation harness for the `tk-quota` suite — puts each defect back.

Run: python3 tk/tests/mutations_tk_quota.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires every one of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

THE ENTRIES THAT CARRY THE DESIGN are the three on staleness. Softening the
refusal is the natural "improvement" someone will make to this command — a
fallback, a warning instead of an exit, a window reported anyway — and each of
those turns a previous window's percentage into what reads as the current one.
They must fail loudly, and here they do.

TWO ENTRIES MUTATE PROSE, in `skills/kickoff/WINDOW.md`: a command the wall does
not name is a command the wall does not run, which is the finding the Spec axis
raised against `tk-context --curve` and this slice answers in advance.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

QUOTA = os.path.join("bin", "tk-quota")
WINDOW = os.path.join("skills", "kickoff", "WINDOW.md")

ONE_LINE = "TheNumbers.test_both_windows_are_printed_on_one_line"
DAYS = "TheNumbers.test_the_weekly_window_is_spelled_in_days"
WHOLE = "TheNumbers.test_a_fractional_percentage_is_rendered_whole"
STALE = "WhenTheFileIsAPreviousWindows.test_a_reset_that_has_passed_is_not_a_low_percentage"
AGE = "WhenTheFileIsAPreviousWindows.test_the_refusal_says_how_old_the_file_is"
WEEKLY = "WhenTheFileIsAPreviousWindows.test_a_stale_five_hour_still_reports_a_live_weekly_and_says_so"
NO_FILE = "WhenThereIsNoNumber.test_no_sidecar_at_all"
BAD_JSON = "WhenThereIsNoNumber.test_a_sidecar_that_is_not_json"
NOT_OBJ = "WhenThereIsNoNumber.test_a_sidecar_that_is_not_an_object"
BAD_PCT = "WhenThereIsNoNumber.test_a_percentage_that_is_not_a_number_is_not_a_window"
BAD_RESET = "WhenThereIsNoNumber.test_a_reset_that_is_not_a_number_is_not_a_window"
THE_FLAG = "TheEdgesOfTheContract.test_the_file_flag_is_the_file_that_gets_read"
TYPO = "TheEdgesOfTheContract.test_a_mistyped_flag_does_not_read_as_no_number"
FLAT = "TheEdgesOfTheContract.test_a_control_character_in_the_file_is_printed_flat"
CALLS_IT = "TheProseThatCallsIt.test_the_wall_sends_the_reader_to_the_command"
SAYS_REFUSAL = "TheProseThatCallsIt.test_the_wall_says_the_reading_can_be_a_previous_windows"

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # -- staleness: the three that carry the design -------------------------
    ("a window whose reset has passed is reported anyway, as a low percentage",
     "    if resets <= now:\n        return None",
     "    if False:\n        return None",
     [STALE, WEEKLY], QUOTA),

    ("the refusal drops the file's age, so nobody can tell how wrong it is",
     'age = f", written {spell(int(now - written))} ago" if isinstance(written, (int, float)) else ""',
     'age = ""',
     [AGE], QUOTA),

    ("a stale 5-hour silences the weekly too, throwing away a figure still true",
     "    if five is None and seven is None:",
     "    if five is None or seven is None:",
     [WEEKLY], QUOTA),

    ("the note about only the weekly being current is dropped",
     '        print("tk-quota: the 5-hour window has reset and no session has rendered "\n'
     '              "since — only the weekly figure is current", file=sys.stderr)',
     "        pass",
     [WEEKLY], QUOTA),

    # -- what the numbers say ------------------------------------------------
    ("the two windows are printed on separate lines",
     'print(" · ".join(parts))',
     'print("\\n".join(parts))',
     [ONE_LINE], QUOTA),

    ("the weekly window is spelled in hours, so 4d11h arrives as 107h",
     "    if seconds >= 86400:\n        return f\"{seconds // 86400}d{(seconds % 86400) // 3600:02d}h\"",
     "    if False:\n        return f\"{seconds // 86400}d{(seconds % 86400) // 3600:02d}h\"",
     [DAYS], QUOTA),

    ("a fractional percentage is printed raw",
     'parts.append(f"5h {five[0]:.0f}% used, {spell(five[1])} left")',
     'parts.append(f"5h {five[0]}% used, {spell(five[1])} left")',
     [WHOLE], QUOTA),

    # -- the three ways there is no number -----------------------------------
    ("a missing sidecar is not a refusal",
     "    except FileNotFoundError:",
     "    except NotADirectoryError:",
     [NO_FILE], QUOTA),

    ("a half-written sidecar crashes instead of refusing",
     "    except (OSError, ValueError) as exc:",
     "    except OSError as exc:",
     [BAD_JSON], QUOTA),

    ("a sidecar holding a list is walked as though it were an object",
     '    if not isinstance(payload, dict):\n        no_number(f"{plain(path)} does not hold an object")',
     "    if False:\n        pass",
     [NOT_OBJ], QUOTA),

    ("a percentage that is not a number is taken as one",
     '    if not isinstance(pct, (int, float)) or not isinstance(resets, (int, float)):\n        return None',
     "    if False:\n        return None",
     [BAD_PCT, BAD_RESET], QUOTA),

    # -- the edges -----------------------------------------------------------
    ("--file is ignored and the default sidecar is read",
     '    payload = read_sidecar(args.file)',
     "    payload = read_sidecar(os.path.expanduser(SIDECAR))",
     [THE_FLAG], QUOTA),

    ("a mistyped flag exits 2 — indistinguishable from `no number, use judgement`",
     "        sys.exit(EXIT_USAGE)",
     "        sys.exit(EXIT_NO_NUMBER)",
     [TYPO], QUOTA),

    ("a control character in the path reaches the terminal",
     '    return re.sub(r"[\\x00-\\x1f\\x7f]", "?", str(value))',
     "    return str(value)",
     [FLAT], QUOTA),

    # -- the prose that calls it ---------------------------------------------
    ("the wall never names the command, so nobody reads the quota before dispatching",
     "**Read the quota before dispatching, not only after it fails.** `../../bin/tk-quota` prints",
     "**Read the quota before dispatching, not only after it fails.** The statusline prints",
     [CALLS_IT], WINDOW),

    ("the wall drops the warning that the reading can be a previous window's",
     "It **exits 2 rather than report a figure it cannot vouch for**.",
     "It reports what the sidecar holds.",
     [SAYS_REFUSAL], WINDOW),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_quota"))
