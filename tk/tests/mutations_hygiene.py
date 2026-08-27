#!/usr/bin/env python3
"""Mutation harness for the `tk-hygiene` suite — puts each defect back.

Run: python3 tk/tests/mutations_hygiene.py

Same contract as its siblings: each entry restores one defect in a COPY of
`tk/`, runs only the tests named for it, and requires each of them to fail. A
mutation that SURVIVES is a hole in the suite, not a pass.

This file holds entries only. The runner is `mutations_tk_contract.run`, which
takes the test module, the entry list and the default source as arguments — the
seam that file's docstring describes. It also enumerates the suite and reports
any test NO entry names (UNPROVED), which is the half a score of N/N cannot
show: N counts the mutants someone wrote.

WHAT A GREEN SCORE HERE DOES NOT SAY. The prune's idempotence is STRUCTURAL —
the prune is a delete, so a second run finds no candidate — and no single-line
mutation of the source turns the second run into a different one. Its test is
named by the guard mutations instead, because what it can be falsified on is the
outcome it pins after the FIRST run. A green score does not mean idempotence was
attacked; it means the guards that produce it were.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run      # noqa: E402  (path above enables it)

HYGIENE = os.path.join("bin", "tk-hygiene")

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    # --- the prune guards, one entry each ---------------------------------
    # THE guard for the spec's "a branch without an upstream is NEVER pruned":
    # with it gone, a no-upstream branch reaches the commit count, comes back 0
    # and is deleted. That is the mutation the rule was unfalsifiable without
    ("T128 hygiene the upstream guard is dropped, so a local-only branch is deleted",
     '    if track != "[gone]":', "    if False:",
     ["TestPrune.test_only_the_merged_gone_branch_is_pruned",
      "TestIdempotence.test_a_second_run_prunes_nothing_and_answers_the_same"], HYGIENE),

    ("T128 hygiene a branch with no upstream is described as one whose upstream lives",
     '        return ("no upstream: nothing ever said it was merged" if not upstream',
     '        return ("no upstream: nothing ever said it was merged" if upstream',
     ["TestPrune.test_only_the_merged_gone_branch_is_pruned"], HYGIENE),

    ("T128 hygiene the gone check is inverted, so a live upstream is the prunable one",
     '    if track != "[gone]":', '    if track == "[gone]":',
     ["TestPrune.test_only_the_merged_gone_branch_is_pruned",
      "TestIdempotence.test_a_second_run_prunes_nothing_and_answers_the_same"], HYGIENE),

    ("T128 hygiene commits of its own no longer hold a branch back",
     '    if count != "0":', "    if False:",
     ["TestPrune.test_only_the_merged_gone_branch_is_pruned",
      "TestIdempotence.test_a_second_run_prunes_nothing_and_answers_the_same"], HYGIENE),

    ("T128 hygiene the range is reversed, so the default's commits are counted instead",
     'f"{default}..{name}"', 'f"{name}..{default}"',
     ["TestPrune.test_only_the_merged_gone_branch_is_pruned"], HYGIENE),

    ("T128 hygiene the reason a branch is held back is computed and then ignored",
     "        if reason is not None:", "        if False:",
     ["TestPrune.test_only_the_merged_gone_branch_is_pruned",
      "TestIdempotence.test_a_second_run_prunes_nothing_and_answers_the_same"], HYGIENE),

    ("T128 hygiene without a default branch the comparison is made anyway",
     '    if default is None:\n        return [("kept", name, "no default branch '
     'to measure against")',
     '    if False:\n        return [("kept", name, "no default branch '
     'to measure against")',
     ["TestPrune.test_without_a_default_branch_to_measure_against_nothing_is_pruned"],
     HYGIENE),

    ("T128 hygiene git refusing to delete a checked-out branch is reported as a prune",
     '        if code != 0:\n            out.append(("kept", name,',
     '        if False:\n            out.append(("kept", name,',
     ["TestPrune.test_a_branch_checked_out_in_another_worktree_survives_the_refusal"],
     HYGIENE),

    # --- what the report is allowed to say ---------------------------------
    ("T128 hygiene the default branch is reported as residue like any other",
     '    if default is not None and default.rsplit("/", 1)[-1] == name:',
     "    if False:",
     ["TestPrune.test_the_default_branch_is_never_reported_as_residue"], HYGIENE),

    ("T128 hygiene every branch is a candidate, alive upstream included",
     '    return track == "[gone]" or not upstream', "    return True",
     ["TestPrune.test_a_branch_whose_upstream_is_alive_is_left_alone_and_unreported"],
     HYGIENE),

    # --- the audit and its exit codes --------------------------------------
    ("T128 hygiene a repo whose box is off still exits 0",
     "    if RED in values:\n        return EXIT_FINDING",
     "    if RED in values:\n        return EXIT_OK",
     ["TestForgeAudit.test_a_repo_with_the_box_off_is_red_in_the_literal_and_exits_1",
      "TestForgeAudit.test_a_red_repo_outranks_an_unknown_one_in_the_exit_code"], HYGIENE),

    ("T128 hygiene a repo that could not be audited still exits 0",
     "    if UNKNOWN in values:\n        return EXIT_UNAUDITED",
     "    if UNKNOWN in values:\n        return EXIT_OK",
     ["TestForgeAudit.test_a_forge_that_answers_an_error_is_unknown_and_exits_3",
      "TestForgeAudit.test_a_forge_answering_neither_true_nor_false_is_unknown"], HYGIENE),

    ("T128 hygiene a repo with no GitHub remote counts as one the audit failed to reach",
     "answers.append((path, None, NO_FORGE,", "answers.append((path, None, UNKNOWN,",
     ["TestForgeAudit.test_a_repo_with_no_github_remote_is_not_a_failed_audit"], HYGIENE),

    ("T128 hygiene a forge that answered an error is read as green",
     "        return UNKNOWN, detail", "        return GREEN, detail",
     ["TestForgeAudit.test_a_forge_that_answers_an_error_is_unknown_and_exits_3"], HYGIENE),

    ("T128 hygiene whatever the forge answered is passed through as the setting",
     '    return UNKNOWN, f"gh answered {answer!r}, which is neither true nor false"',
     '    return answer, ""',
     ["TestForgeAudit.test_a_forge_answering_neither_true_nor_false_is_unknown"], HYGIENE),

    ("T128 hygiene the report names a repo by its slug, tracker clone included",
     '        line = label(value).ljust(width) + f"  {path}"',
     '        line = label(value).ljust(width) + f"  {_slug or path}"',
     ["TestTheReportNamesRepositoriesByPath.test_the_slug_never_reaches_the_report"],
     HYGIENE),

    # --- reading the remote ------------------------------------------------
    ("T128 hygiene the scp-like ssh remote no longer names a repo",
     "         [:/]                            # ':' in the scp-like form, '/' in a URL",
     "         /                               # ':' in the scp-like form, '/' in a URL",
     ["TestForgeAudit.test_the_slug_is_read_from_an_ssh_remote_too"], HYGIENE),

    ("T128 hygiene any host is audited as though it were GitHub",
     "         github\\.com                     # this bin audits GitHub and says so",
     "         [a-z.]+                         # this bin audits GitHub and says so",
     ["TestForgeAudit.test_a_repo_hosted_elsewhere_is_not_reported_as_a_github_repo"],
     HYGIENE),

    ("T128 hygiene the .git suffix is carried into the slug",
     "         (?:\\.git)?/?$",
     "         /?$",
     ["TestForgeAudit.test_a_repo_with_the_box_on_is_green_in_the_literal_and_exits_0"],
     HYGIENE),

    # --- one repo, however many trees --------------------------------------
    ("T128 hygiene a worktree counts as a second repository",
     "        if key in seen:\n            continue",
     "        if False:\n            continue",
     ["TestOneRepoPerBranchSet.test_a_worktree_is_not_a_second_repository"], HYGIENE),

    ("T128 hygiene the forge is asked once per repository instead of once per slug",
     "        if slug not in cache:", "        if True:",
     ["TestNoNetwork.test_one_slug_is_asked_of_the_forge_once"], HYGIENE),

    ("T128 hygiene the forge CLI is resolved somewhere other than PATH",
     '        p = subprocess.run(("gh", "api", f"repos/{slug}",',
     '        p = subprocess.run(("/nonexistent/gh", "api", f"repos/{slug}",',
     ["TestNoNetwork.test_the_forge_cli_is_resolved_through_path_so_the_fake_is_reached"],
     HYGIENE),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_hygiene", default_src=HYGIENE))
