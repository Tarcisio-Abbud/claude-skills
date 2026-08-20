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
        "binary staged file is not scanned",
        "  git diff --cached --text --unified=0",
        "  git diff --cached --unified=0",
        ["test_value_inside_a_binary_file_is_refused"],
    ),
    (
        "grep answers the binary stream instead of filtering it",
        "| grep -a -E '^\\+'",
        "| grep -E '^\\+'",
        ["test_value_inside_a_binary_file_is_refused"],
    ),
    (
        "context lines are scanned, so an untouched neighbour trips the guard",
        "--unified=0 | grep -a -E '^\\+'",
        "| cat",
        ["test_value_already_committed_nearby_does_not_trip_the_guard"],
    ),
    (
        "the filter drops the path header, so a value in a path walks through",
        "grep -a -E '^\\+'",
        "grep -a -E '^\\+[^+]'",
        ["test_value_in_a_path_is_refused"],
    ),
    (
        "narrowing to added lines blinds the guard to a value added now",
        "git diff --cached --text --unified=0 | grep -a -E '^\\+'",
        "true",
        [
            "test_the_same_value_added_now_is_still_refused",
            "test_slug_in_staged_content_is_refused",
        ],
    ),
    (
        "the commit message is never scanned",
        '  if [ -n "$message_file" ]; then\n    cat "$message_file"\n  fi\n',
        "",
        ["test_value_only_in_the_commit_message_is_refused"],
    ),
    (
        "only the first key is checked",
        "for key in tk.tracker tk.ghConfigDir; do",
        "for key in tk.tracker; do",
        ["test_gh_config_dir_in_staged_content_is_refused"],
    ),
    (
        "an empty value is used as a needle, matching every commit",
        '  if [ -z "$value" ]; then\n    continue\n  fi\n',
        "",
        [
            "test_empty_value_does_not_match_every_commit",
            "test_unset_key_protects_nothing",
        ],
    ),
    (
        "the refusal does not refuse",
        "exit 1\n",
        "exit 0\n",
        [
            "test_slug_in_staged_content_is_refused",
            "test_gh_config_dir_in_staged_content_is_refused",
            "test_value_in_a_path_is_refused",
            "test_value_inside_a_binary_file_is_refused",
            "test_value_only_in_the_commit_message_is_refused",
        ],
    ),
    (
        "the refusal names a fixed key instead of the one that fired",
        '    echo "  - the value of: git config $key" >&2\n',
        '    echo "  - the value of: git config tk.tracker" >&2\n',
        ["test_refusal_names_the_key_that_fired"],
    ),
    (
        "the printed remedy loses the lookup that makes it run",
        '\\"\\$(git config $key)\\"" >&2\n    echo "    replace by',
        '\\"$key\\"" >&2\n    echo "    replace by',
        ["test_printed_remedy_runs_and_finds_the_line"],
    ),
    (
        "the guard refuses everything, blocking all work",
        '  if published | grep -a -q -F -- "$value"; then\n',
        "  if true; then\n",
        ["test_clean_commit_is_accepted"],
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

            survived, _ = run_tests(targets, ids)
            if survived:
                problems.append("%s: SURVIVED — %s still pass with the defect back" % (label, targets))
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
