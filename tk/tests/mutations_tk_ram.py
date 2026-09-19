#!/usr/bin/env python3
"""Mutation harness for the `tk-ram` suite — puts each defect back.

Run: python3 tk/tests/mutations_tk_ram.py

Same contract as its siblings: each entry restores one defect in a COPY of `tk/`,
runs only the tests named for it, and requires every one of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`.

THE ENTRIES THAT CARRY THE DESIGN are the arithmetic ones. `tk-ram` prints a
small integer that reads as authoritative at any value — 2 is as plausible as 3
— and every operand it divides can be dropped without the line looking wrong. So
the reserve, `anon` and `swap` are each removed in turn, and each removal is
required to move a fixture the suite already pins. A number with no failing test
behind it is a preference wearing a measurement's clothes.

THE CLAMP IS MUTATED IN BOTH DIRECTIONS, because it is the half no measurement
passed. Stripping the ceiling lets an empty container authorise four agents;
stripping the floor lets the bin print 0, which is the verdict the quota floor
and the wall give and this sensor does not. Two more strip the WORDS that say a
clamp fired: a clamped number that does not announce itself is indistinguishable
from arithmetic, and the ledger keeps it for months.

TEN ENTRIES MUTATE PROSE, in `skills/kickoff/AFK.md`, `WINDOW.md` and
`LEDGER.md`. A reading nobody is told to take is a bin nobody runs, and a reading
taken once per package is the constant this whole item replaced. The LEDGER pair
guards the other end: a reading that is taken and then folded into `<quota>` is
lost as a reading, and the next package starts from the site key again.

THREE OF THE TEN GUARD THE BUDGET'S READING OF THE NUMBER, which is where the
clamp turns back into the defect. The bin never prints 0, so a saturated
container prints 1 with the clamp on stderr alone; a budget that reads the digit
and stops dispatches one more agent into a container with nothing left. The
third holds the fit to what a fire ADDS — `anon` already counts the runs in
flight, so read as a live-at-once cap the same line authorises them twice.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

RAM = os.path.join("bin", "tk-ram")
AFK = os.path.join("skills", "kickoff", "AFK.md")
WINDOW = os.path.join("skills", "kickoff", "WINDOW.md")
LEDGER = os.path.join("skills", "kickoff", "LEDGER.md")

EMPTY = "TheFit.test_an_empty_container_fits_three"
NINE = "TheFit.test_nine_live_sessions_fit_no_more_than_two"
HALF = "TheFit.test_a_half_full_container_fits_two"
SWAP = "TheFit.test_swap_counts_against_the_fit"
RESERVE = "TheFit.test_the_reserve_is_kept_off_the_ceiling_before_the_division"
CAPPED = "TheFit.test_a_quotient_above_three_is_capped_and_the_line_says_so"
RAISED = "TheFit.test_a_quotient_below_one_is_raised_and_the_line_says_so"
FLOOR_SAID = "TheFit.test_a_raw_fit_at_or_below_zero_says_the_floor_is_not_a_measurement"
OPERANDS = "TheFit.test_the_line_names_every_number_that_went_into_the_division"
BY_KEY = "TheFit.test_the_anon_line_is_found_by_its_key_and_not_by_its_position"

UNLIMITED = "WhenThereIsNoNumber.test_an_unlimited_cgroup_is_refused"
NOT_BYTES = "WhenThereIsNoNumber.test_a_memory_max_that_is_not_a_byte_count_is_refused"
NOT_INT = "WhenThereIsNoNumber.test_a_digit_int_cannot_convert_is_refused_and_not_raised"
NO_ANON = "WhenThereIsNoNumber.test_a_memory_stat_with_no_anon_line_is_refused"
NO_DIR = "WhenThereIsNoNumber.test_a_cgroup_directory_that_is_not_there_is_refused"
NO_FILES = "WhenThereIsNoNumber.test_a_cgroup_directory_missing_its_files_is_refused"
FIFO = "WhenThereIsNoNumber.test_a_fifo_where_a_file_should_be_is_refused_before_it_blocks"
FALLBACK = "WhenThereIsNoNumber.test_the_refusal_names_the_site_key_the_caller_falls_back_on"

NO_SWAP_FILE = "WhatIsDisclosedRatherThanRefused.test_an_absent_swap_file_counts_as_zero_and_says_so"
NESTED = "WhatIsDisclosedRatherThanRefused.test_a_nested_cgroup_is_named_on_stderr_with_the_default_directory"
FLAGGED = "WhatIsDisclosedRatherThanRefused.test_a_cgroup_given_on_the_flag_is_not_checked_against_proc"

FLAT = "WhatComesFromOutsideThisProcess.test_a_control_sequence_in_a_cgroup_file_is_printed_flat"
USAGE = "Usage.test_an_unknown_flag_exits_sixty_four"

VEHICLE = "TheProseThatCallsIt.test_the_vehicle_reads_the_axis_before_each_local_dispatch"
TICK = "TheProseThatCallsIt.test_the_tick_says_the_site_key_is_the_fallback_and_not_the_reading"
MEMINFO = "TheProseThatCallsIt.test_the_tick_says_the_harness_warning_does_not_cover_this"
FLOOR_PROSE = "TheProseThatCallsIt.test_the_tick_says_a_printed_one_may_be_the_floor_and_not_a_fit"
ADDS = "TheProseThatCallsIt.test_the_tick_says_the_fit_bounds_what_the_fire_adds"
LEDGER_LINE = "TheProseThatCallsIt.test_the_ledger_takes_the_reading_on_the_dispatch_line"

FREE = "    free = ceiling - RESERVE - anon - swap"

MUTATIONS = [
    # -- the arithmetic ------------------------------------------------------
    ("the reserve is never kept off the ceiling",
     FREE, "    free = ceiling - anon - swap",
     [RESERVE], RAM),

    ("swap is not counted, so a swapped agent's memory is free",
     FREE, "    free = ceiling - RESERVE - anon",
     [SWAP], RAM),

    ("anon is not counted at all, so occupancy stops reaching the answer",
     FREE, "    free = ceiling - RESERVE - swap",
     [NINE, HALF, RESERVE, RAISED], RAM),

    ("the per-agent cost is half what was measured",
     "PER_AGENT = 0.74 * GIB", "PER_AGENT = 0.5 * GIB",
     [HALF, RESERVE, OPERANDS], RAM),

    ("the reserve is a tenth of what the calibration set aside",
     "RESERVE = 0.5 * GIB", "RESERVE = 0.1 * GIB",
     [RESERVE, OPERANDS], RAM),

    ("the line prints the count alone, so nothing can be recomputed from it",
     '''    line = (f"tk-ram: {clamped} agents fit now ({gib(ceiling)} max, {gib(anon)} anon, "
            f"{gib(swap)} swap, {gib(RESERVE)} reserve, {gib(PER_AGENT)} per agent "
            f"-> {raw:.2f}")''',
     '    line = (f"tk-ram: {clamped} agents fit now (read from the cgroup")',
     [OPERANDS], RAM),

    # -- the clamp, in both directions ---------------------------------------
    ("the ceiling is dropped, so an empty container authorises four agents",
     "    clamped = min(FIT_CEILING, max(FIT_FLOOR, fit))",
     "    clamped = max(FIT_FLOOR, fit)",
     [EMPTY, CAPPED], RAM),

    ("the floor is dropped, so the bin gives the verdict `dispatch nothing`",
     "    clamped = min(FIT_CEILING, max(FIT_FLOOR, fit))",
     "    clamped = min(FIT_CEILING, fit)",
     [RAISED], RAM),

    ("the ceiling is raised to a number no measurement passed",
     "FIT_CEILING = 3 ", "FIT_CEILING = 4 ",
     [EMPTY, CAPPED], RAM),

    ("the line does not say the ceiling fired",
     '        line += f", capped at {FIT_CEILING}"',
     '        line += ""',
     [CAPPED], RAM),

    ("the line does not say the floor fired",
     '        line += f", raised to {FIT_FLOOR}"',
     '        line += ""',
     [RAISED], RAM),

    ("a raw fit of zero is printed as 1 with nothing said about it",
     "    if fit < FIT_FLOOR:\n        note(", "    if False:\n        note(",
     [FLOOR_SAID], RAM),

    # -- reading the cgroup --------------------------------------------------
    ("the anon line is taken by position, so a new kernel key is read as anon",
     '        if key.lstrip(BOM) == "anon":',
     "        if True:",
     [BY_KEY], RAM),

    ("an unlimited cgroup is divided as if `max` were a byte count",
     '    if value == "max":', "    if False:",
     [UNLIMITED], RAM),

    ("a cgroup file holding words is parsed anyway",
     "    if not value.isdecimal():", "    if False:",
     [NOT_BYTES], RAM),

    ("the guard is `isdigit`, so a digit `int()` refuses dies with a traceback",
     "    if not value.isdecimal():", "    if not value.isdigit():",
     [NOT_INT], RAM),

    ("a memory.stat with no anon line is read as an empty container",
     '    no_number(f"{plain(path)} has no `anon` line — is this cgroup v2?")',
     "    return 0",
     [NO_ANON], RAM),

    ("the cgroup argument is never checked for being a directory",
     "    if not os.path.isdir(directory):", "    if False:",
     [NO_DIR], RAM),

    ("a missing memory.max is treated as absent rather than refused",
     '    value = read_text(path).strip()',
     '    value = (read_text(path, missing_ok=True) or "").strip()',
     [NO_FILES], RAM),

    ("the regular-file question is not asked, so a FIFO blocks the command",
     "    if not os.path.isfile(path):", "    if False:",
     [FIFO], RAM),

    # -- what a refusal owes the caller --------------------------------------
    ("the refusal stops at `no number` and names no fallback",
     '''    print(f"tk-ram: no number — fall back on `{SITE_KEY}` in ~/.claude/tk/env "
          "and say in the package ledger that the reading failed", file=sys.stderr)''',
     '    print("tk-ram: no number", file=sys.stderr)',
     [FALLBACK], RAM),

    ("a value from the cgroup reaches the terminal unflattened",
     '        no_number(f"{plain(directory)} is not a directory")',
     '        no_number(f"{directory} is not a directory")',
     [FLAT], RAM),

    ("a usage error exits 2, which is this command's `no number`",
     "        sys.exit(EXIT_USAGE)", "        sys.exit(EXIT_NO_NUMBER)",
     [USAGE], RAM),

    # -- disclosed rather than refused ---------------------------------------
    ("an absent swap file is refused, and a zero costs the whole number",
     '    text = read_text(path, missing_ok=True)\n    if text is None:',
     "    text = read_text(path)\n    if text is None:",
     [NO_SWAP_FILE], RAM),

    ("an absent swap file is counted as zero in silence",
     '        note(f"{plain(path)} is absent (swap controller off) — counted as 0")',
     "        pass",
     [NO_SWAP_FILE], RAM),

    ("a nested cgroup is never disclosed, so the default file is read as ours",
     "    if text is None or text.strip() == OWN_CGROUP:", "    if True:",
     [NESTED], RAM),

    ("the disclosure fires for a directory the caller named on the flag",
     "    if directory != CGROUP:\n        return", "    if False:\n        return",
     [FLAGGED], RAM),

    # -- the prose that calls it ---------------------------------------------
    ("the vehicle never names the bin, so the site key stays the ceiling",
     "`../../bin/tk-ram` prints what the cgroup fits now",
     "the site key is what the cgroup fits",
     [VEHICLE], AFK),

    ("the vehicle takes the reading once per package, which is a constant again",
     "**Read it before each local dispatch:**", "**Read it once per package:**",
     [VEHICLE], AFK),

    ("the tick's budget never names the bin",
     "`../../bin/tk-ram` reads this container's own cgroup",
     "The orchestrator judges this container's own cgroup",
     [TICK], WINDOW),

    ("the budget does not say which exit hands the fire back to the site key",
     "Where the bin refuses — exit 2 — `max-local-subagents` is the",
     "Where the bin refuses, `max-local-subagents` is the",
     [TICK], WINDOW),

    ("the budget lets the reader wait for a warning that cannot fire",
     "2.1.274 reads `/proc/meminfo`, which inside a container is the\n  HOST's, and is "
     "blind to the cgroup that actually kills the run.",
     "the harness warns on low memory before it matters.",
     [MEMINFO], WINDOW),

    ("the budget reads the printed 1 as a fit, so the floor dispatches into a full container",
     "**A printed `1` may be the floor and not a fit.**",
     "The number it prints is the fit.",
     [FLOOR_PROSE], WINDOW),

    ("the budget names the clamp and never says what the fire owes when it fires",
     "the fire dispatches nothing local and the ledger line\n  carries that stderr line",
     "the fire may still dispatch one and the ledger line\n  carries that stderr line",
     [FLOOR_PROSE], WINDOW),

    ("the fit reads as how many may be alive at once, not as the room left",
     "the fit bounds what this fire ADDS, never what may be\n  alive at once",
     "the fit is how many may be\n  alive at once",
     [ADDS], WINDOW),

    ("the ledger admits no reading, so it is taken and then lost",
     "the line `../../bin/tk-ram` printed for it",
     "whatever the orchestrator judged",
     [LEDGER_LINE], LEDGER),

    ("the ledger folds the reading into the quota field",
     "It is never folded into `<quota>`", "It may go in `<quota>` instead",
     [LEDGER_LINE], LEDGER),
]

if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_ram"))
