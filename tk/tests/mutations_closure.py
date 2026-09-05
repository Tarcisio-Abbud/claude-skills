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
`skills/kickoff/AFK.md` and `skills/merge-gate/SKILL.md`. A skill file is code
an agent executes, and the defects two of this ticket's criteria name live there
rather than in Python — the attended path dispatching without the reference, and
a verdict row whose keyword rule the checker has already left behind. Neither
can be falsified by mutating a bin.

SOME ENTRIES SWITCH OFF ONE CLAUSE, not one statement. The runner replaces a
whole `if` with `if False:`, and a compound predicate dies from that whichever
clause the test was aiming at: six live guards here — the repository half of a
cited reference, the case-folding on both halves, the number compared as text,
the closing lines after the first — were each half of a condition whose other
half was booking the kill. So the clause is switched off on its own, and the
entry says which clause it is.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

READER = os.path.join("bin", "tk-ticket-ref")
CHECKER = os.path.join("bin", "tk-closure-check")
KICKOFF = os.path.join("skills", "kickoff", "SKILL.md")
AFK = os.path.join("skills", "kickoff", "AFK.md")
GATE = os.path.join("skills", "merge-gate", "SKILL.md")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # --- the reader composes the reference ---------------------------------
    ("T238 the reference is emitted without its owner half, as the queue stores it",
     '    return f"{owner}/{tracked}#{number}"',
     '    return f"{tracked}#{number}"',
     ["TestTheReferenceReader.test_an_items_ticket_is_printed_owner_qualified",
      "TestTheReferenceReader.test_the_closing_line_flag_prints_the_whole_line",
      "TestTheReferenceReader.test_a_claimed_item_still_answers_with_its_reference"],
     READER),

    ("T238 the emitted repo half is the queue's lower-cased spelling, not the tracker's",
     '    return f"{owner}/{tracked}#{number}"',
     '    return f"{owner}/{repo}#{number}"',
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
      "test_a_ticket_in_another_repository_is_refused_not_given_this_owner",
      "TestTheClosureChecker.test_a_cited_repository_the_tracker_does_not_name_is_red"],
     READER),

    ("T238 CLAUSE: the two repo halves are compared case-sensitively, so the tracker's own "
     "spelling reads as another repository",
     "    if repo != tracked.lower():", "    if repo != tracked:",
     ["TestTheReferenceReader.test_the_trackers_spelling_of_both_halves_is_the_one_printed"],
     READER),

    # --- which clone is asked ----------------------------------------------
    ("T238 a path that is not a directory is handed to git, which reports a broken git",
     "    if not os.path.isdir(clone.path):", "    if False:",
     ["TestTheReferenceReader."
      "test_a_path_that_is_not_a_directory_is_refused_before_git_is_asked"], READER),

    ("T238 a directory that is no clone is reported as a clone declaring no tk.tracker",
     "        if not is_clone(repo):", "        if False:",
     ["TestTheReferenceReader."
      "test_a_directory_that_is_no_clone_is_not_reported_as_a_clone_with_no_key"], READER),

    ("T238 a `git config` that FAILED is folded into the branch for a key that is missing",
     "    if run.returncode not in (0, 1):", "    if False:",
     ["TestTheReferenceReader.test_a_config_that_could_not_be_read_is_not_an_unset_key"],
     READER),

    ("T238 the item's own **Repo:** is not read, so the cwd answers for every item",
     "        if address:", "        if False:",
     ["TestTheReferenceReader."
      "test_the_clone_comes_from_the_items_own_repo_field_when_no_flag_names_one",
      "TestTheClosureChecker.test_the_clone_comes_from_the_items_repo_field_here_too"],
     READER),

    ("T238 an item whose **Repo:** no reader may use is reported as one naming none",
     "        elif present:", "        elif False:",
     ["TestTheReferenceReader."
      "test_an_item_whose_repo_field_no_reader_may_use_is_told_apart_from_one_with_none"],
     READER),

    ("T238 --repo is ignored, so the flag names a clone nothing reads",
     '    if explicit:\n        clone = Clone(explicit, "`--repo`")',
     '    if False:\n        clone = Clone(explicit, "`--repo`")',
     ["TestTheReferenceReader.test_an_items_ticket_is_printed_owner_qualified"], READER),

    ("T238 the refusal does not say where the refused path came from",
     'f"this run looked for `tk.tracker`, taken from {clone.source}. Name the clone "',
     '"this run looked for `tk.tracker`, taken from somewhere. Name the clone "',
     ["TestTheReferenceReader."
      "test_an_item_naming_no_clone_and_a_cwd_that_is_none_is_refused_naming_the_gap"],
     READER),

    ("T238 CLAUSE: the message is spoken under a hard-coded name, so the checker's failed "
     "run reads as a command that never ran",
     '    return os.path.basename(sys.argv[0]) or "tk-ticket-ref"',
     '    return "tk-ticket-ref"',
     ["TestTheClosureChecker.test_a_failed_run_is_spoken_under_the_command_that_made_it"],
     READER),

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

    # --- the five conditions -----------------------------------------------
    ("T238 the keyword set is not consulted, so any word in front of a reference counts",
     "    honoured = [m for m in found if m[0].lower() in reader.KEYWORDS]",
     "    honoured = list(found)",
     ["TestTheClosureChecker."
      "test_a_closing_word_the_forge_does_not_honour_is_red_on_keyword",
      "TestTheClosureChecker."
      "test_a_word_the_forge_ignores_still_gets_the_other_conditions_answered"], CHECKER),

    ("T238 a body carrying no closing line at all is reported green",
     '        out.append(("keyword", FAILED,\n'
     '                    f"no closing line in the body: nothing reads `<keyword> <ref>` for "',
     '        out.append(("keyword", OK,\n'
     '                    f"no closing line in the body: nothing reads `<keyword> <ref>` for "',
     ["TestTheClosureChecker.test_a_body_with_no_closing_line_at_all_is_red_on_keyword"],
     CHECKER),

    ("T238 the keyword-red path answers only the keyword, so one defect reads as three",
     "    candidates = honoured or found", "    candidates = honoured",
     ["TestTheClosureChecker."
      "test_a_word_the_forge_ignores_still_gets_the_other_conditions_answered"], CHECKER),

    ("T238 CLAUSE: the subject is the FIRST line in the body rather than the one naming "
     "this item's ticket, so two lines in the other order give the other verdict",
     "    subject = (right or aimed or candidates or [None])[0]",
     "    subject = (candidates or [None])[0]",
     ["TestTheClosureChecker."
      "test_the_same_two_closing_lines_give_the_same_verdict_in_either_order"], CHECKER),

    ("T238 CLAUSE: only the first closing line is examined, so every other one closes its "
     "own ticket on merge, silently",
     "    strays = [m for m in honoured if not aims_at(m[1], m[2], repo, number)]",
     "    strays = []",
     ["TestTheClosureChecker.test_a_second_closing_line_closes_a_second_ticket_and_is_red",
      "TestTheClosureChecker."
      "test_the_same_two_closing_lines_give_the_same_verdict_in_either_order",
      "TestTheClosureChecker."
      "test_a_closing_line_for_another_repository_does_not_count_as_this_ticket"], CHECKER),

    ("T238 CLAUSE: the repository half of the cited reference is not compared, so a line "
     "closing another repository's issue of the same number counts",
     "    return cited == number and (not half or half.lower() == repo.lower())",
     "    return cited == number",
     ["TestTheClosureChecker."
      "test_a_closing_line_for_another_repository_does_not_count_as_this_ticket"], CHECKER),

    ("T238 CLAUSE: the cited number is not compared at all, so any ticket of the right "
     "repository counts",
     "    return cited == number and (not half or half.lower() == repo.lower())",
     "    return (not half or half.lower() == repo.lower())",
     ["TestTheClosureChecker.test_a_body_closing_another_ticket_is_red_on_number"], CHECKER),

    ("T238 CLAUSE: the cited number is compared through int(), so `#0007` — a spelling the "
     "forge's `#N` syntax does not resolve — reads as the right ticket",
     "    return cited == number and (not half or half.lower() == repo.lower())",
     "    return int(cited) == int(number) and (not half or half.lower() == repo.lower())",
     ["TestTheClosureChecker."
      "test_a_number_spelled_with_leading_zeros_is_not_the_form_that_resolves"], CHECKER),

    ("T238 CLAUSE: the repository halves are compared case-sensitively, so a re-cased slug "
     "the forge resolves reads as another repository",
     "    return cited == number and (not half or half.lower() == repo.lower())",
     "    return cited == number and (not half or half == repo)",
     ["TestTheClosureChecker."
      "test_a_re_cased_slug_resolves_to_the_same_repository_and_is_green"], CHECKER),

    ("T238 CLAUSE: an ABSENT repository half is read as a different repository, so a bare "
     "`#n` is reported wrong twice for one defect",
     "    return cited == number and (not half or half.lower() == repo.lower())",
     "    return cited == number and half.lower() == repo.lower()",
     ["TestTheClosureChecker."
      "test_a_bare_reference_is_red_on_owner_and_not_on_the_number"], CHECKER),

    ("T238 the reference is re-derived from the item's own halves instead of composed by "
     "the reader, so the checker greenlights what the reader refuses to emit",
     "        expected = reader.qualify(ticket, reader.tracker_slug(clone, label), label)",
     '        expected = reader.tracker_slug(clone, label).partition("/")[0] + "/" + ticket',
     ["TestTheClosureChecker.test_a_cited_repository_the_tracker_does_not_name_is_red"],
     CHECKER),

    ("T238 a missing owner half is reported as a malformed one, not as an absent one",
     "    if not sep:", "    if False:",
     ["TestTheClosureChecker.test_an_ownerless_reference_is_red_on_owner",
      "TestTheClosureChecker."
      "test_a_bare_reference_is_red_on_owner_and_not_on_the_number"], CHECKER),

    ("T238 an owner half that is PRESENT is taken for a correct one",
     "    if owner.lower() != wanted.lower():", "    if False:",
     ["TestTheClosureChecker.test_an_owner_present_but_wrong_is_red"], CHECKER),

    ("T238 CLAUSE: the owner half is compared case-sensitively, so a re-cased account the "
     "forge resolves is reported as somebody else's",
     "    if owner.lower() != wanted.lower():", "    if owner != wanted:",
     ["TestTheClosureChecker."
      "test_a_re_cased_slug_resolves_to_the_same_repository_and_is_green"], CHECKER),

    ("T238 the owner half is not read against the slug shape",
     "    if not reader.TRACKER_RE.fullmatch(slug):", "    if False:",
     ["TestTheClosureChecker.test_a_malformed_owner_half_is_red_on_owner"], CHECKER),

    ("T238 the base branch is never compared, so a stacked PR passes verdict 5",
     "    if base != default:", "    if False:",
     ["TestTheClosureChecker.test_a_pull_request_off_the_default_branch_is_red_on_base",
      "TestTheClosureChecker.test_two_failing_conditions_are_both_named_in_the_verdict"],
     CHECKER),

    # --- the keyword the forge does not honour, and the ones it does -------
    ("T238 CLAUSE: the colon form `Fixes: <ref>` is read as no closing line, though the "
     "forge's own documentation says a keyword may carry one",
     r'MENTION_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z]+):?[ \t]+'
     r'(\S*)#([0-9]{1,9})(?![0-9])")',
     r'MENTION_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z]+)[ \t]+'
     r'(\S*)#([0-9]{1,9})(?![0-9])")',
     ["TestTheClosureChecker.test_a_colon_after_the_keyword_is_a_form_the_forge_honours"],
     CHECKER),

    ("T238 CLAUSE: a word merely ENDING in a keyword counts as one, so `Not-fixes <ref>` "
     "is a green verdict on a body that closes nothing",
     r'MENTION_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z]+):?[ \t]+'
     r'(\S*)#([0-9]{1,9})(?![0-9])")',
     r'MENTION_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z]+):?[ \t]+'
     r'(\S*)#([0-9]{1,9})(?![0-9])")',
     ["TestTheClosureChecker.test_a_word_merely_ending_in_a_keyword_is_not_one"], CHECKER),

    # --- the report --------------------------------------------------------
    ("T238 only the first failing condition is named, so the second is silently repaired "
     "twice",
     "    red = [name for name, state, _ in rows if state == FAILED]",
     "    red = [name for name, state, _ in rows if state == FAILED][:1]",
     ["TestTheClosureChecker.test_two_failing_conditions_are_both_named_in_the_verdict"],
     CHECKER),

    ("T238 only the failing conditions are printed, so a skipped check reads like a passed "
     "one",
     '        print(head + detail.replace("\\n", "\\n" + " " * len(head)))',
     '        print(head + detail.replace("\\n", "\\n" + " " * len(head))) '
     "if state == FAILED else None",
     ["TestTheClosureChecker.test_every_condition_is_reported_by_name_green_or_red"],
     CHECKER),

    ("T238 the verdict line is spelled some other way, so a digest greps for nothing",
     '    print(f"verdict-5: GREEN for {label}")\n    return EXIT_GREEN',
     '    print(f"verdict-5: green for {label}")\n    return EXIT_GREEN',
     ["TestTheClosureChecker.test_a_body_closing_this_items_ticket_is_green"], CHECKER),

    # --- the escape, and the state that had none ---------------------------
    ("T238 the escape asserts the item names no ticket instead of quoting it",
     '                   ("item", OK, block.splitlines()[0].strip())], label)',
     '                   ("item", OK, "(the item names no ticket)")], label)',
     ["TestTheClosureChecker.test_an_item_with_no_ticket_is_green_and_the_item_is_quoted"],
     CHECKER),

    ("T238 an item with no ticket is green even when the body closes somebody else's",
     "    if closing:", "    if False:",
     ["TestTheClosureChecker."
      "test_an_item_with_no_ticket_whose_body_closes_something_is_red"], CHECKER),

    ("T238 every refusal is read as the no-ticket escape, so a defect turns verdict 5 green",
     '        if refusal.code != "no-ticket":', "        if False:",
     ["TestTheClosureChecker.test_an_unpairable_ticket_is_red_with_its_remedy"], CHECKER),

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
     "`../../bin/tk-ticket-ref <id> --closing-line`, which reads the owner from the clone "
     "the item's\n**Repo:** field names",
     "the owner half resolved HERE (`git config tk.tracker`) from the clone the item's\n"
     "**Repo:** field names",
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
     "A\n   Portuguese `Fecha #n` is present, cites the right ticket, and closes NOTHING.",
     "A\n   Portuguese `Fecha #n` is present, cites the right ticket, and closes NOTHING. Any\n"
     "   closing keyword the forge honours counts — `Fixes`, `Closes`, `Resolves` — since "
     "they are the same mechanism.",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_file_does_not_say_a_closing_keyword_the_forge_honours_counts"], GATE),

    ("T238 the verdict row stops naming the command that answers it",
     "`../../bin/tk-closure-check <id> --pr <n>` asks all five and names the ones that "
     "failed.",
     "Ask all five, and name the ones that failed.",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_verdict_row_names_the_checker_that_asks_the_conditions"], GATE),

    ("T238 the verdict row goes back to the four-condition rule, silent on the second "
     "closing line the forge also honours",
     "owner half and all, no OTHER closing line in the body, and the PR targets",
     "owner half and all, and the PR targets",
     ["TestTheMergeGateStatesTheRuleTheCheckerEnforces."
      "test_the_verdict_row_states_the_other_closing_line_condition"], GATE),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_closure", default_src=READER))
