"""Mutation proof for `test_tracker_gh.py`.

Each mutation restores one defect the wrapper exists to prevent, then requires the tests named
for it to FAIL. Same shape and same two honesty checks as
`githooks/tests/mutations_private_values.py` — a test named by a mutation must exist, and any
test no mutation names is reported UNPROVED, because a green score counts only the mutants
someone wrote.

Run: python3 bin/tests/mutations_tracker_gh.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.abspath(os.path.join(HERE, os.pardir, "tracker-gh"))

MUTATIONS = [
    (
        'an unset tracker is not checked, so gh runs with an empty -R',
        'if [ -z "$tracker" ]; then\n  missing="$missing tk.tracker"\nfi\n',
        '',
        [
            'test_an_unconfigured_tracker_refuses_before_gh_runs',
            'test_an_empty_configured_value_counts_as_unconfigured',
        ],
    ),
    (
        'an unset gh config dir is not checked, so gh picks the ambient identity',
        'if [ -z "$gh_dir" ]; then\n  missing="$missing tk.ghConfigDir"\nfi\n',
        '',
        [
            'test_an_unconfigured_gh_dir_refuses_before_gh_runs',
        ],
    ),
    (
        'the refusal prints but does not stop, so gh runs anyway',
        '  exit 78\n',
        '  return 0\n',
        [
            'test_an_unconfigured_tracker_refuses_before_gh_runs',
            'test_a_command_naming_no_tracker_is_refused',
            'test_a_write_to_another_repo_is_refused',
        ],
    ),
    (
        'the shape of the configured value is never checked',
        'if ! printf \'%s\' "$tracker" |\n',
        'if false; then\n',
        [
            'test_a_tracker_carrying_a_metacharacter_is_refused',
        ],
    ),
    (
        "a command naming no tracker is allowed through to the cwd's repo",
        'if [ "$placeholder" = no ]; then\n',
        'if false; then\n',
        [
            'test_a_command_naming_no_tracker_is_refused',
        ],
    ),
    (
        'the placeholder is never substituted',
        '        substituted="$substituted${rest%%\\{tracker\\}*}$tracker"\n',
        '        substituted="$substituted${rest%%\\{tracker\\}*}"\n',
        [
            'test_the_placeholder_is_replaced_by_the_configured_slug',
            'test_every_argument_is_substituted_not_only_the_first',
            'test_a_dotted_value_survives_substitution_intact',
        ],
    ),
    (
        'only the first argument is substituted',
        'count=$#\n',
        'count=1\n',
        [
            'test_every_argument_is_substituted_not_only_the_first',
        ],
    ),
    (
        'the gh identity is resolved but never exported',
        'GH_CONFIG_DIR=$gh_dir\nexport GH_CONFIG_DIR\n',
        '',
        [
            'test_the_gh_identity_is_exported_for_the_call',
        ],
    ),
    (
        'the -R value is not read back, so it may name any repo',
        '    -R|--repo) add_ref "$arg" ;;\n',
        '    -R|--repo) : ;;\n',
        [
            'test_a_write_to_another_repo_is_refused',
        ],
    ),
    (
        'an api path is not read back, so it may name any repo',
        '    sed -n \'s|.*repos/\\([A-Za-z0-9._-]\\{1,\\}\\)/\\([A-Za-z0-9._-]\\{1,\\}\\).*|\\1/\\2|p\')"\n',
        '    :\n',
        [
            'test_an_api_path_to_another_repo_is_refused',
            'test_an_api_path_naming_the_tracker_is_the_target',
        ],
    ),
    (
        'a URL argument is not read back, so it may name any repo',
        '    sed -n \'s|.*github\\.com/\\([A-Za-z0-9._-]\\{1,\\}\\)/\\([A-Za-z0-9._-]\\{1,\\}\\).*|\\1/\\2|p\')"\n',
        '    :\n',
        [
            'test_a_url_to_another_repo_is_refused',
        ],
    ),
    (
        'a foreign target is found but not refused',
        'if [ -n "$foreign" ]; then\n',
        'if false; then\n',
        [
            'test_a_write_to_another_repo_is_refused',
            'test_an_api_path_to_another_repo_is_refused',
            'test_a_url_to_another_repo_is_refused',
        ],
    ),
    (
        'a command that decides no target at all is allowed through',
        'if [ "$names_tracker" = no ]; then\n',
        'if false; then\n',
        [
            'test_a_command_with_no_decidable_target_is_refused',
        ],
    ),
    (
        'gh is never reached, so the wrapper blocks all work',
        'exec gh "$@"\n',
        'exit 0\n',
        [
            'test_a_configured_clone_reaches_gh',
        ],
    ),
    (
        'the target is compared case-sensitively, so a re-cased slug reads as another repo',
        '  if [ "$(printf \'%s\' "$ref" | tr \'A-Z\' \'a-z\')" = "$wanted" ]; then\n',
        '  if [ "$ref" = "$wanted" ]; then\n',
        [
            'test_the_target_is_compared_case_insensitively',
        ],
    ),
]


def suite_test_ids():
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
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "-q"] + [ids[n] for n in names],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def main():
    with open(TARGET, encoding="utf-8") as fh:
        original = fh.read()

    ids = suite_test_ids()
    available = set(ids)
    named = set()
    problems = []

    ok, output = run_tests(sorted(available), ids)
    if not ok:
        print("the suite is not green before mutating; fix that first\n%s" % output)
        return 1

    backup = tempfile.mkstemp(prefix="tracker-gh-backup-")[1]
    shutil.copy(TARGET, backup)
    original_mode = os.stat(TARGET).st_mode
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

            with open(TARGET, "w", encoding="utf-8") as fh:
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
        shutil.copy(backup, TARGET)
        os.chmod(TARGET, original_mode)
        os.unlink(backup)

    for name in sorted(available - named):
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
