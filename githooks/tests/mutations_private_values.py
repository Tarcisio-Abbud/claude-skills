"""Mutation proof for `test_private_values.py`.

Each mutation restores one defect the guard exists to prevent, then requires the tests named
for it to FAIL. A test that still passes with the defect back protects nothing.

Two checks keep the harness itself honest, both paid for by earlier slices:

- a test named by a mutation must EXIST, or a typo in the name reports as a killed mutant;
- every test in the suite is enumerated, and any test no mutation names is reported UNPROVED,
  because a score of 100% only ever measures the mutants that were written.

Run: python3 githooks/tests/mutations_private_values.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.abspath(os.path.join(HERE, os.pardir, "private-values"))

# name -> (what the defect is, the literal to replace, its replacement, tests it must kill)
MUTATIONS = [
    (
        'binary staged file is not scanned',
        'git diff --cached --text --unified=0 |\n    grep',
        'git diff --cached --unified=0 |\n    grep',
        [
            'test_value_inside_a_binary_file_is_refused',
        ],
    ),
    (
        'grep answers the binary stream instead of filtering it',
        "    grep -a -E '^\\+' | grep -a -v",
        "    grep -E '^\\+' | grep -a -v",
        [
            'test_value_inside_a_binary_file_is_refused',
        ],
    ),
    (
        'context is neither suppressed nor filtered, so an untouched neighbour trips the guard',
        "  git diff --cached --text --unified=0 |\n    grep -a -E '^\\+' | grep -a -v -E '^\\+\\+\\+ ' | sed 's/^+//'\n",
        '  git diff --cached --text\n',
        [
            'test_value_already_committed_nearby_does_not_trip_the_guard',
        ],
    ),
    (
        'the added lines are never read',
        '  git diff --cached --text --unified=0 |\n    grep -a -E',
        '  : |\n    grep -a -E',
        [
            'test_slug_in_staged_content_is_refused',
            'test_the_same_value_added_now_is_still_refused',
        ],
    ),
    (
        'a pure rename is invisible, because only added lines are read',
        '  for surface in added_lines new_paths message_text; do',
        '  for surface in added_lines message_text; do',
        [
            'test_rename_into_a_leaky_path_is_refused',
        ],
    ),
    (
        'every touched path is read, so an already-tracked leaky path is re-reported',
        'git diff --cached --name-only --diff-filter=ACR\n',
        'git diff --cached --name-only\n',
        [
            'test_editing_a_file_whose_path_already_leaked_is_accepted',
        ],
    ),
    (
        'case is honoured, so a re-cased slug publishes the same identity unchecked',
        '  grep -a -q -i -F -- "$1"\n',
        '  grep -a -q -F -- "$1"\n',
        [
            'test_case_changed_value_is_refused',
        ],
    ),
    (
        'the URL-encoded spelling is never considered',
        '    "$(printf \'%s\' "$value" | sed \'s|/|%2F|g\')" \\\n',
        '    "$value" \\\n',
        [
            'test_percent_encoded_value_is_refused',
        ],
    ),
    (
        'the doubly-encoded spelling is never considered',
        '    "$(printf \'%s\' "$value" | sed \'s|/|%252F|g\')"\n',
        '    "$(printf \'%s\' "$value" | sed \'s|/|%2F|g\')"\n',
        [
            'test_double_encoded_value_is_refused',
        ],
    ),
    (
        'the join runs across the whole diff, so two files collide at the seam',
        '    /^\\+\\+\\+ / { if (path != "") print path "\\t" buf; path = substr($0, 7); buf = ""; next }\n',
        '    /^\\+\\+\\+ / { if (path == "") path = substr($0, 7); next }\n',
        [
            'test_two_files_meeting_at_the_seam_are_accepted',
        ],
    ),
    (
        'a carriage return is left on each line, so a CRLF file cannot be rejoined',
        '    /^\\+/      { l = substr($0, 2); sub(/\\r$/, "", l); buf = buf l; next }\n',
        '    /^\\+/      { l = substr($0, 2); buf = buf l; next }\n',
        [
            'test_wrapped_remedy_survives_crlf_line_endings',
        ],
    ),
    (
        'the joined match is asked of the whole row, so the path answers for it',
        '      NEEDLE="$needle" awk -F\'\\t\' \'index(tolower($2), tolower(ENVIRON["NEEDLE"])) { print; exit }\')\n',
        '      NEEDLE="$needle" awk -F\'\\t\' \'index(tolower($0), tolower(ENVIRON["NEEDLE"])) { print; exit }\')\n',
        [
            'test_editing_a_file_whose_path_already_leaked_is_accepted',
        ],
    ),
    (
        'the branch name is never read',
        '    if branch_name | fold_separators | contains "$(printf \'%s\' "$needle" | fold_separators)"; then\n',
        '    if false; then\n',
        [
            'test_branch_name_transliterating_the_value_is_refused',
            'test_branch_name_carrying_the_literal_value_is_refused',
        ],
    ),
    (
        'only `/` and `_` are folded, so a dot or no separator at all walks through',
        "  LC_ALL=C tr -dc 'A-Za-z0-9'\n",
        "  tr '/_' '--'\n",
        [
            'test_branch_name_with_other_separators_is_refused',
            'test_branch_name_with_no_separators_at_all_is_refused',
        ],
    ),
    (
        'the wrapped remedy leaves the +++ header in what it shows',
        '      printf \'%s\\n\' "    see it:     git diff --cached --text -U0 -- \'$hit_path\' | grep -a -E \'^\\\\+\' | grep -a -v -E \'^\\\\+\\\\+\\\\+ \' | sed \'s/^+//\'" >&2\n',
        '      printf \'%s\\n\' "    see it:     git diff --cached --text -U0 -- \'$hit_path\' | grep -a -E \'^\\\\+\' | sed \'s/^+//\'" >&2\n',
        [
            'test_wrapped_remedy_runs_and_finds_the_value',
        ],
    ),
    (
        'the joined reading is never taken, so a wrapped value walks through',
        '    row=$(joined_per_file |\n      NEEDLE="$needle" awk -F\'\\t\' \'index(tolower($2), tolower(ENVIRON["NEEDLE"])) { print; exit }\')\n',
        '    row=\n',
        [
            'test_value_wrapped_across_two_lines_is_refused',
            'test_a_wrap_inside_one_file_is_still_refused',
            'test_wrapped_remedy_survives_crlf_line_endings',
        ],
    ),
    (
        'the branch check uses an empty needle, refusing every branch',
        '    if branch_name | fold_separators | contains "$(printf \'%s\' "$needle" | fold_separators)"; then\n',
        '    if branch_name | fold_separators | contains ""; then\n',
        [
            'test_an_ordinary_branch_name_is_accepted',
        ],
    ),
    (
        'the commit message is never scanned',
        '  if [ -n "$message_file" ]; then\n    cat "$message_file"\n  fi\n',
        '  :\n',
        [
            'test_value_only_in_the_commit_message_is_refused',
        ],
    ),
    (
        'the refusal does not say which surface fired',
        '      echo "  - the value of: git config $key — in the commit message" >&2\n',
        '      echo "  - the value of: git config $key" >&2\n',
        [
            'test_refusal_names_the_surface_that_fired',
        ],
    ),
    (
        'only the first key is checked',
        'for key in tk.tracker tk.ghConfigDir; do',
        'for key in tk.tracker; do',
        [
            'test_gh_config_dir_in_staged_content_is_refused',
        ],
    ),
    (
        'an empty value is used as a needle, matching every commit',
        '  if [ -z "$value" ]; then\n    continue\n  fi\n',
        '',
        [
            'test_empty_value_does_not_match_every_commit',
            'test_unset_key_protects_nothing',
        ],
    ),
    (
        'the refusal does not refuse',
        'exit 1\n',
        'exit 0\n',
        [
            'test_slug_in_staged_content_is_refused',
            'test_value_in_a_path_is_refused',
            'test_rename_into_a_leaky_path_is_refused',
            'test_branch_name_transliterating_the_value_is_refused',
            'test_a_wrap_inside_one_file_is_still_refused',
        ],
    ),
    (
        'the refusal names a fixed key instead of the one that fired',
        '      echo "  - the value of: git config $key — in a line this commit adds" >&2\n',
        '      echo "  - the value of: git config tk.tracker — in a line this commit adds" >&2\n',
        [
            'test_refusal_names_the_key_that_fired',
        ],
    ),
    (
        'the printed remedy loses the lookup that makes it run',
        '      echo "    see it:     git diff --cached --text -U0 | grep -n -i -F -- \\"\\$(git config $key)\\"" >&2\n',
        '      echo "    see it:     git diff --cached --text -U0 | grep -n -i -F -- \\"$key\\"" >&2\n',
        [
            'test_printed_remedy_runs_and_finds_the_line',
        ],
    ),
    (
        'the guard refuses everything, blocking all work',
        '      if $surface | contains "$needle"; then\n',
        '      if true; then\n',
        [
            'test_clean_commit_is_accepted',
        ],
    ),
]


def suite_test_ids():
    """method name -> full unittest id. Derived, never hand-kept: a list beside a
    completeness check is the next defect, and hardcoding the TestCase name would turn a
    second test class into a misdiagnosed 'suite is not green'."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=HERE, pattern="test_*.py")
    ids = {}

    def walk(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                walk(item)
            else:
                full = item.id()
                ids[full.rsplit(".", 1)[-1]] = full

    walk(suite)
    return ids


def run_tests(names, ids):
    """Run the named tests against whatever is currently on disk. True when all passed."""
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "-q"] + [ids[n] for n in names],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def main():
    with open(GUARD, encoding="utf-8") as fh:
        original = fh.read()

    ids = suite_test_ids()
    available = set(ids)
    named = set()
    problems = []

    ok, output = run_tests(sorted(available), ids)
    if not ok:
        print("the suite is not green before mutating; fix that first\n%s" % output)
        return 1

    backup = tempfile.mkstemp(prefix="guard-backup-")[1]
    shutil.copy(GUARD, backup)
    original_mode = os.stat(GUARD).st_mode
    try:
        for label, needle, replacement, targets in MUTATIONS:
            named.update(targets)

            missing = [t for t in targets if t not in available]
            if missing:
                problems.append("%s: names a test that does not exist: %s" % (label, missing))
                continue

            if original.count(needle) != 1:
                problems.append(
                    "%s: its anchor matches %d times, so the mutation is not the one described"
                    % (label, original.count(needle))
                )
                continue

            with open(GUARD, "w", encoding="utf-8") as fh:
                fh.write(original.replace(needle, replacement))

            # One at a time. Running the named tests together lets a survivor hide behind a
            # sibling that failed: the batch reports non-zero either way, and the mutation
            # books a kill it did not earn.
            survivors = [t for t in targets if run_tests([t], ids)[0]]
            if survivors:
                problems.append(
                    "%s: SURVIVED — %s still pass with the defect back" % (label, survivors)
                )
            else:
                print("killed: %s" % label)
    finally:
        shutil.copy(backup, GUARD)
        os.chmod(GUARD, original_mode)
        os.unlink(backup)

    unproved = sorted(available - named)
    for name in unproved:
        print("UNPROVED: %s — no mutation names it" % name)

    for problem in problems:
        print("PROBLEM: %s" % problem)

    print(
        "\n%d mutations, %d problems, %d of %d tests proved"
        % (len(MUTATIONS), len(problems), len(named & available), len(available))
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
