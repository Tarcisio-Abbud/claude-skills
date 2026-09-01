#!/usr/bin/env python3
"""Mutation harness for the `test_tk_closure` suite — puts each defect back.

Run: python3 tk/tests/mutations_closure.py

Same contract as its siblings: each entry restores one defect in a COPY of
`tk/`, runs only the tests named for it, and requires each of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass. The runner is
`mutations_tk_contract.run`, which also enumerates the suite and reports any
test NO entry names as UNPROVED — the half a score of N/N cannot show.

FIVE SOURCES, not one. The two bins are mutated, and so are the three prose
files that dispatch or govern them: `skills/kickoff/SKILL.md`,
`skills/kickoff/AFK.md` and `skills/wrap-up/MERGE-GATE.md`. A skill file is code
an agent executes, and the defects two of this ticket's criteria name live there
rather than in Python — the attended path dispatching without the reference, and
a verdict row whose keyword rule the checker has already left behind. Neither
can be falsified by mutating a bin.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

READER = os.path.join("bin", "tk-ticket-ref")
CHECKER = os.path.join("bin", "tk-closure-check")
KICKOFF = os.path.join("skills", "kickoff", "SKILL.md")
AFK = os.path.join("skills", "kickoff", "AFK.md")
GATE = os.path.join("skills", "wrap-up", "MERGE-GATE.md")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # --- the reader composes the reference ---------------------------------
    ("T238 the reference is emitted without its owner half, as the queue stores it",
     '    qualified = f"{owner}/{tracked}#{number}"',
     '    qualified = f"{tracked}#{number}"',
     ["TestTheReferenceReader.test_an_items_ticket_is_printed_owner_qualified",
      "TestTheReferenceReader.test_the_closing_line_flag_prints_the_whole_line",
      "TestTheReferenceReader.test_a_claimed_item_still_answers_with_its_reference"],
     READER),

    ("T238 the emitted repo half is the queue's lower-cased spelling, not the tracker's",
     '    qualified = f"{owner}/{tracked}#{number}"',
     '    qualified = f"{owner}/{repo}#{number}"',
     ["TestTheReferenceReader.test_the_trackers_spelling_of_both_halves_is_the_one_printed"],
     READER),

    ("T238 --closing-line prints the bare reference, with no keyword in front of it",
     '    print(f"{CLOSING_KEYWORD} {qualified}" if args.closing_line else qualified)',
     "    print(qualified)",
     ["TestTheReferenceReader.test_the_closing_line_flag_prints_the_whole_line"], READER),

    ("T238 an item naming no ticket is refused like a defect, not answered with exit 3",
     '        return EXIT_NO_TICKET if refusal.code == "no-ticket" else EXIT_REFUSED',
     "        return EXIT_REFUSED",
     ["TestTheReferenceReader."
      "test_an_item_naming_no_ticket_exits_three_and_prints_no_reference"], READER),

    # --- the states a presence check cannot see ----------------------------
    ("T238 an unreadable **Ticket:** is not noticed, so the reference is composed from None",
     "    if ref is None:", "    if False:",
     ["TestTheReferenceReader.test_an_unpairable_ticket_is_refused_with_a_reachable_remedy",
      "TestTheClosureChecker.test_an_unpairable_ticket_is_red_with_its_remedy"], READER),

    ("T238 the unreadable **Ticket:** is refused with no remedy anyone can run",
     '                      f"  tk-queue cancel {label} --why \\"unreadable Ticket, '
     're-added\\"\\n"',
     '                      "  (repair the item by hand)\\n"',
     ["TestTheReferenceReader.test_an_unpairable_ticket_is_refused_with_a_reachable_remedy",
      "TestTheClosureChecker.test_an_unpairable_ticket_is_red_with_its_remedy"], READER),

    ("T238 an unconfigured clone is not told apart from a misconfigured one",
     "    if not value:", "    if False:",
     ["TestTheReferenceReader."
      "test_an_unset_tracker_refuses_rather_than_emitting_an_ownerless_reference",
      "TestTheClosureChecker.test_an_unconfigured_clone_is_red_rather_than_green_by_default"],
     READER),

    ("T238 the tracker value is pasted without the shape gate `bin/tracker-gh` applies",
     "    if not TRACKER_RE.fullmatch(value):", "    if False:",
     ["TestTheReferenceReader.test_a_tracker_outside_the_slug_shape_is_refused_not_pasted"],
     READER),

    ("T238 a ticket in another repository is given this tracker's owner anyway",
     "    if repo != tracked.lower():", "    if False:",
     ["TestTheReferenceReader."
      "test_a_ticket_in_another_repository_is_refused_not_given_this_owner"], READER),

    # --- which item is read ------------------------------------------------
    ("T238 the id is ignored, so any open item answers for the one that was asked",
     '        if kind == "item-open" and tk_queue.item_id(text) == wanted:',
     '        if kind == "item-open":',
     ["TestTheReferenceReader."
      "test_an_id_no_open_item_carries_is_a_failed_run_not_a_refusal"], READER),

    ("T238 a claimed item is skipped, the way `pack` skips it — and the gate loses its "
     "ticket",
     '        if kind == "item-open" and tk_queue.item_id(text) == wanted:',
     '        if kind == "item-open" and tk_queue.item_id(text) == wanted \\\n'
     '                and "**Claimed:**" not in text:',
     ["TestTheReferenceReader.test_a_claimed_item_still_answers_with_its_reference"],
     READER),

    # --- the four conditions -----------------------------------------------
    ("T238 the keyword set is not consulted, so any word in front of a reference counts",
     "    honoured = [m for m in found if m[0].lower() in reader.KEYWORDS]",
     "    honoured = list(found)",
     ["TestTheClosureChecker."
      "test_a_closing_word_the_forge_does_not_honour_is_red_on_keyword"], CHECKER),

    ("T238 a body carrying no closing line at all is reported green",
     '        return [("keyword", FAILED,\n'
     '                 f"no closing line in the body: nothing reads `<keyword> <ref>` for "',
     '        return [("keyword", OK,\n'
     '                 f"no closing line in the body: nothing reads `<keyword> <ref>` for "',
     ["TestTheClosureChecker.test_a_body_with_no_closing_line_at_all_is_red_on_keyword"],
     CHECKER),

    ("T238 the cited ticket is not compared against the item's own",
     "    if int(cited) != int(number) or (repo_half and repo_half != wanted_repo):",
     "    if False:",
     ["TestTheClosureChecker.test_a_body_closing_another_ticket_is_red_on_number"], CHECKER),

    ("T238 a missing owner half is reported as a malformed one, not as an absent one",
     "    if not sep:", "    if False:",
     ["TestTheClosureChecker.test_an_ownerless_reference_is_red_on_owner"], CHECKER),

    ("T238 an owner half that is PRESENT is taken for a correct one",
     "    if owner.lower() != wanted.lower():", "    if False:",
     ["TestTheClosureChecker.test_an_owner_present_but_wrong_is_red"], CHECKER),

    ("T238 the owner half is not read against the slug shape",
     "    if not reader.TRACKER_RE.fullmatch(slug):", "    if False:",
     ["TestTheClosureChecker.test_a_malformed_owner_half_is_red_on_owner"], CHECKER),

    ("T238 the base branch is never compared, so a stacked PR passes verdict 5",
     "    if base != default:", "    if False:",
     ["TestTheClosureChecker.test_a_pull_request_off_the_default_branch_is_red_on_base",
      "TestTheClosureChecker.test_two_failing_conditions_are_both_named_in_the_verdict"],
     CHECKER),

    ("T238 only the first failing condition is named, so the second is silently repaired "
     "twice",
     "    red = [name for name, state, _ in rows if state == FAILED]",
     "    red = [name for name, state, _ in rows if state == FAILED][:1]",
     ["TestTheClosureChecker.test_two_failing_conditions_are_both_named_in_the_verdict"],
     CHECKER),

    ("T238 only the failing conditions are printed, so a skipped check reads like a passed "
     "one",
     '        print(f"{name.ljust(width)}  {state}  {detail}")',
     '        print(f"{name.ljust(width)}  {state}  {detail}") if state == FAILED else None',
     ["TestTheClosureChecker.test_every_condition_is_reported_by_name_green_or_red"],
     CHECKER),

    ("T238 the verdict line is spelled some other way, so a digest greps for nothing",
     '    print(f"verdict-5: GREEN for {label}")\n    return EXIT_GREEN',
     '    print(f"verdict-5: green for {label}")\n    return EXIT_GREEN',
     ["TestTheClosureChecker.test_a_body_closing_this_items_ticket_is_green"], CHECKER),

    # --- the escape, and the state that had none ---------------------------
    ("T238 the escape asserts the item names no ticket instead of quoting it",
     '        print(f"item    {OK}  {block.splitlines()[0].strip()}")',
     '        print(f"item    {OK}  (the item names no ticket)")',
     ["TestTheClosureChecker.test_an_item_with_no_ticket_is_green_and_the_item_is_quoted"],
     CHECKER),

    ("T238 an item with no ticket is green even when the body closes somebody else's",
     "        if closing:", "        if False:",
     ["TestTheClosureChecker."
      "test_an_item_with_no_ticket_whose_body_closes_something_is_red"], CHECKER),

    ("T238 every refusal is read as the no-ticket escape, so a defect turns verdict 5 green",
     '        if refusal.code != "no-ticket":', "        if False:",
     ["TestTheClosureChecker.test_an_unpairable_ticket_is_red_with_its_remedy",
      "TestTheClosureChecker.test_an_unconfigured_clone_is_red_rather_than_green_by_default"],
     CHECKER),

    ("T238 the offline mode leaves the base condition unasked instead of refusing",
     "    if args.body_file is not None and not (args.base and args.default_branch):",
     "    if False:",
     ["TestTheClosureChecker."
      "test_the_offline_mode_refuses_to_leave_the_base_condition_unasked"], CHECKER),

    # --- the forge, and the network ----------------------------------------
    ("T238 the forge CLI is resolved somewhere other than PATH, so the fake is never reached",
     '        run = subprocess.run(["gh", *argv], cwd=repo, capture_output=True, text=True)',
     '        run = subprocess.run(["/nonexistent/gh", *argv], cwd=repo, '
     "capture_output=True, text=True)",
     ["TestTheForgeIsReachedThroughPath.test_the_pull_request_is_read_through_gh_on_path",
      "TestTheForgeIsReachedThroughPath."
      "test_a_forge_naming_no_default_branch_is_a_failed_run_not_an_assumed_main"], CHECKER),

    ("T238 a forge naming no default branch is read as an empty one and compared anyway",
     "        if not default:", "        if False:",
     ["TestTheForgeIsReachedThroughPath."
      "test_a_forge_naming_no_default_branch_is_a_failed_run_not_an_assumed_main"], CHECKER),

    # --- the prose that dispatches -----------------------------------------
    ("T238 the attended dispatch stops naming the reference command",
     "`../../bin/tk-ticket-ref <id> --closing-line`, composed there and never here",
     "the reference, composed elsewhere and never here",
     ["TestTheDispatchProseNamesTheCommands."
      "test_the_attended_dispatch_names_the_contract_block_and_the_reference"], KICKOFF),

    ("T238 the attended dispatch prescribes a bin that is not in tk/bin",
     "the contract block from `../../bin/tk-contract",
     "the contract block from `../../bin/tk-contract-invented",
     ["TestTheDispatchProseNamesTheCommands."
      "test_every_bin_the_dispatch_prose_names_is_on_disk"], KICKOFF),

    ("T238 the unattended dispatch goes back to reading the tracker's config itself",
     "`../../bin/tk-ticket-ref <id> --closing-line` — exit 3 is the item that has none",
     "the owner half resolved HERE (`git config tk.tracker`) — exit 3 is the item that "
     "has none",
     ["TestTheDispatchProseNamesTheCommands."
      "test_the_unattended_dispatch_composes_the_reference_through_the_bin"], AFK),

    # --- the prose the checker enforces ------------------------------------
    ("T238 the verdict row lists the keyword set short of one keyword",
     "`Fixes`, `Closes`, `Resolves` and their `fix`/`fixed` forms",
     "`Fixes` and `Closes` and their `fix`/`fixed` forms",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_verdict_row_names_the_keyword_set"], GATE),

    ("T238 the verdict row stops saying the keyword set is English",
     "a closing line under an English keyword the forge honours",
     "a closing line under a keyword the forge honours",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_verdict_row_says_the_set_is_english"], GATE),

    ("T238 the retracted claim that any keyword the forge honours counts comes back",
     "A verdict an agent can satisfy by asserting it is not a verdict.",
     "A verdict an agent can satisfy by asserting it is not a verdict. Any closing\n"
     "keyword the forge honours counts \u2014 `Fixes`, `Closes`, `Resolves` \u2014 since "
     "they are the same mechanism.",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_file_does_not_say_a_closing_keyword_the_forge_honours_counts"], GATE),

    ("T238 the verdict row stops naming the command that answers it",
     "`../../bin/tk-closure-check <id> --pr <n>` asks all four and names the ones that "
     "failed.",
     "Ask all four, and name the ones that failed.",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_verdict_row_names_the_checker_that_asks_the_four_conditions"], GATE),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_closure", default_src=READER))
