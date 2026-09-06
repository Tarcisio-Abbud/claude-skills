#!/usr/bin/env python3
"""Mutation harness for the `tk-collisions` suite — each defect put back, and
the test that claims to prove it must fall.

Run: python3 tk/tests/mutations_collisions.py

Entries only: the runner is the one `mutations_tk_contract.py` exposes, through
the seam its docstring describes. Same contract as its own: an anchor must
match EXACTLY ONCE, a mutant no named test kills is a SURVIVOR, and a test no
entry names is reported UNPROVED, because a green score counts only the mutants
somebody wrote.

ONE ENTRY MUTATES TWO GUARDS AT ONCE, and says so where it sits: `conflicts_of`
reads a conflicted merge two ways on purpose, and either reading alone would
survive its own mutation while the other still answered.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations_tk_contract import run   # noqa: E402  (the path above enables it)

SCRIPT = os.path.join("bin", "tk-collisions")

MUTATIONS = [
    ("every merge is read as clean, which is the forge's answer restored",
     "    if run.returncode == 0:", "    if run.returncode != 999:",
     ["TestCollisions.test_two_branches_each_clean_against_main_can_still_collide"],
     SCRIPT),

    ("a merge that succeeded is taken for one that failed",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    tree = run.stdout.split(\"\\n\", 1)[0].strip() or None\n"
     "    if run.returncode == 0:",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    tree = run.stdout.split(\"\\n\", 1)[0].strip() or None\n"
     "    if run.returncode == 2:",
     ["TestCollisions.test_branches_that_touch_different_files_are_reported_clean"],
     SCRIPT),

    ("only neighbouring branches are paired, so a collision two apart is missed",
     "        for b in args.refs[i + 1:]:", "        for b in args.refs[i + 1:i + 2]:",
     ["TestCollisions.test_every_pair_is_measured_not_only_the_neighbours"],
     SCRIPT),

    ("a lone branch falls into the pair loop and is reported as nothing measured",
     "    if len(args.refs) < 2:", "    if False:",
     ["TestCollisions.test_one_branch_is_answered_not_refused"],
     SCRIPT),

    ("the colliding pair is reported without the files it collides in",
     '            pairs.append({"a": a, "b": b, "conflicts": bool(paths or messages),\n'
     '                          "paths": paths, "messages": messages})',
     '            pairs.append({"a": a, "b": b, "conflicts": bool(paths or messages),\n'
     '                          "paths": [], "messages": messages})',
     ["TestCollisions.test_json_names_the_colliding_pair_and_its_paths"],
     SCRIPT),

    # the merge is PERFORMED. This mutant is the heuristic it is not: the two
    # branches touched one file, so call it a collision
    ("the merge is replaced by `did both branches touch this file`",
     '    run = git(repo, "merge-tree", "--write-tree", a, b)\n'
     "    tree = run.stdout.split(\"\\n\", 1)[0].strip() or None\n"
     "    if run.returncode == 0:\n        return tree, [], []",
     '    run = git(repo, "diff", "--name-only", a, b)\n'
     "    return None, sorted(set(run.stdout.split())), []\n"
     "    tree = run.stdout.split(\"\\n\", 1)[0].strip() or None\n"
     "    if run.returncode == 0:\n        return tree, [], []",
     ["TestCollisions.test_two_branches_editing_one_file_apart_are_clean"],
     SCRIPT),

    # the two readings of a conflicted merge, mutated together — see the module
    # docstring: either one alone survives while the other still answers
    ("a conflicted merge is read by neither of its two readings",
     "        stage = re.match(r\"^\\d{6} [0-9a-f]{4,64} ([123])\\t(.*)$\", line)\n"
     "        if stage:\n"
     "            if stage.group(2) not in paths:\n"
     "                paths.append(stage.group(2))\n"
     '        elif line.startswith("CONFLICT ("):\n'
     "            messages.append(line)\n"
     '            named = re.search(r"Merge conflict in (.+)$", line)\n'
     "            if named and named.group(1) not in paths:\n"
     "                paths.append(named.group(1))",
     "        pass",
     ["TestCollisions.test_two_branches_each_clean_against_main_can_still_collide"],
     SCRIPT),

    ("a ref nobody fetched is passed to the merge and diagnosed as a conflict",
     '        if git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode != 0:',
     "        if False:",
     ["TestCollisionFailures.test_a_ref_that_names_no_commit_stops_the_run"],
     SCRIPT),

    ("a directory that is no repository is reported as a missing ref",
     '    if git(repo, "rev-parse", "--git-dir").returncode != 0:', "    if False:",
     ["TestCollisionFailures.test_a_directory_that_is_not_a_repository_stops_the_run"],
     SCRIPT),

    ("a merge that could not run at all is reported as a clean pair",
     "    if not paths and not messages:", "    if False:",
     ["TestCollisionFailures.test_a_merge_that_could_not_run_is_never_reported_as_clean"],
     SCRIPT),

    # --- the union half (`--against`) ------------------------------------

    ("the suite never runs, which is the pairwise blindness restored",
     "            pair[\"suite\"] = run_suite(repo, union[\"commit\"], args.suite)",
     '            pair["suite"] = {"returncode": 0, "tail": ""}',
     ["TestUnion.test_a_test_one_branch_adds_grades_a_file_the_other_branch_edits"],
     SCRIPT),

    ("the union is the PAIR, so a base that moved is not in the tree",
     "    landed = commit_of(repo, tree, base, pivot)", "    landed = pivot",
     ["TestUnion.test_the_union_is_taken_over_the_base_and_not_between_the_pair"],
     SCRIPT),

    ("a red union is counted as one that lands",
     '           if p["conflicts"] or (p["suite"] and p["suite"]["returncode"] != 0)]',
     '           if p["conflicts"]]',
     ["TestUnion.test_a_test_one_branch_adds_grades_a_file_the_other_branch_edits"],
     SCRIPT),

    ("a conflicted union hands its half-merged tree to the suite anyway",
     "    tree, paths, messages = measure(repo, landed, other)\n"
     "    if paths or messages:\n"
     "        return {\"commit\": None, \"pair\": (pivot, other),\n"
     "                \"paths\": paths, \"messages\": messages}",
     "    tree, paths, messages = measure(repo, landed, other)\n"
     "    if False:\n"
     "        return {\"commit\": None, \"pair\": (pivot, other),\n"
     "                \"paths\": paths, \"messages\": messages}",
     ["TestUnion.test_a_textual_conflict_in_the_union_is_reported_without_a_suite_run"],
     SCRIPT),

    ("the temporary worktree is left registered in the repository",
     "    finally:\n"
     '        remove = git(repo, "worktree", "remove", "--force", path)\n'
     "        shutil.rmtree(path, ignore_errors=True)",
     "    finally:\n"
     '        remove = git(repo, "worktree", "list")\n'
     "        shutil.rmtree(path, ignore_errors=True)",
     ["TestUnion.test_the_temporary_worktree_is_removed_even_when_the_union_is_red"],
     SCRIPT),

    ("--against is accepted with no base and no suite",
     "        if missing:", "        if False:",
     ["TestUnionFailures.test_against_without_a_suite_stops_the_run",
      "TestUnionFailures.test_against_without_a_base_stops_the_run"],
     SCRIPT),

    ("a suite named without a pivot is ignored instead of refused",
     "    elif args.base or args.suite:", "    elif False:",
     ["TestUnionFailures.test_a_suite_without_a_pivot_stops_the_run"],
     SCRIPT),

    ("the pivot is unioned with itself",
     "    others = [ref for ref in args.refs if ref != pivot]",
     "    others = list(args.refs)",
     ["TestUnion.test_the_pivot_itself_is_never_unioned_with_itself"],
     SCRIPT),

    ("a suite the shell could not start is read as a red union",
     "        if run.returncode in (126, 127):", "        if False:",
     ["TestUnionFailures.test_a_suite_that_could_not_be_run_is_never_reported_as_green"],
     SCRIPT),

    ("the pivot and the base are not checked to name a commit",
     "    for ref in args.refs + [r for r in (args.against, args.base) if r]:",
     "    for ref in args.refs:",
     ["TestUnionFailures.test_a_pivot_that_names_no_commit_stops_the_run"],
     SCRIPT),

    ("a union the suite passed is reported as one that cannot land",
     '        if pair["suite"]["returncode"] != 0:', "        if True:",
     ["TestUnion.test_a_union_whose_suite_passes_is_reported_green"],
     SCRIPT),

    ("the union answer carries the pair without the failure that named it",
     '                "tail": tail_of(run.stdout + run.stderr)}',
     '                "tail": ""}',
     ["TestUnion.test_json_carries_the_suite_result_of_every_union"],
     SCRIPT),
]


if __name__ == "__main__":
    sys.exit(run(MUTATIONS, "test_tk_collisions", default_src=SCRIPT))
