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
        '  for encoded in "$(printf \'%s\' "$value" | sed \'s|/|%2F|g\')" \\\n',
        '  for encoded in "$value" \\\n',
        [
            'test_percent_encoded_value_is_refused',
        ],
    ),
    (
        'the doubly-encoded spelling is never considered',
        '    "$(printf \'%s\' "$value" | sed \'s|/|%252F|g\')"; do\n',
        '    "$(printf \'%s\' "$value" | sed \'s|/|%2F|g\')"; do\n',
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
            'test_a_short_name_wrapped_in_a_crlf_file_is_refused',
        ],
    ),
    (
        'the joined match is asked of the whole row, so the path answers for it',
        '      { c = $2; if (ENVIRON["SQUASH"]',
        '      { c = $0; if (ENVIRON["SQUASH"]',
        [
            'test_editing_a_file_whose_path_already_leaked_is_accepted',
        ],
    ),
    (
        'the branch name is never read',
        '    if contains "$(printf \'%s\' "$needle" | fold_separators)" <"$scratch/branch_name"; then\n',
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
        'the dedupe is inverted, so an encoded spelling that differs is dropped',
        '    [ "$encoded" = "$value" ] || set -- "$@" "$encoded"\n',
        '    [ "$encoded" != "$value" ] || set -- "$@" "$encoded"\n',
        [
            'test_percent_encoded_value_is_refused',
            'test_double_encoded_value_is_refused',
        ],
    ),
    (
        'the joined reading is never taken, so a wrapped value walks through',
        ' "$scratch/joined")',
        ' /dev/null)',
        [
            'test_value_wrapped_across_two_lines_is_refused',
            'test_a_wrap_inside_one_file_is_still_refused',
            'test_wrapped_remedy_survives_crlf_line_endings',
        ],
    ),
    (
        'the branch check uses an empty needle, refusing every branch',
        '    if contains "$(printf \'%s\' "$needle" | fold_separators)" <"$scratch/branch_name"; then\n',
        '    if contains "" <"$scratch/branch_name"; then\n',
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
        '      printf \'%s\\n\' "  - $what — in the commit message" >&2\n',
        '      printf \'%s\\n\' "  - $what" >&2\n',
        [
            'test_refusal_names_the_surface_that_fired',
        ],
    ),
    (
        'only the first key is checked',
        'tk.ghConfigDir\t$(git config tk.ghConfigDir 2>/dev/null)\n',
        '',
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
            'test_an_empty_file_protects_nothing_more',
            'test_comment_and_blank_lines_are_not_needles',
        ],
    ),
    (
        'the refusal does not refuse',
        'END\nexit 1\n',
        'END\nexit 0\n',
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
        '    what="the value of: git config $key"\n',
        '    what="the value of: git config tk.tracker"\n',
        [
            'test_refusal_names_the_key_that_fired',
        ],
    ),
    (
        'the printed remedy loses the lookup that makes it run',
        '    lookup="\\"\\$(git config $key)\\""\n',
        '    lookup="\\"$key\\""\n',
        [
            'test_printed_remedy_runs_and_finds_the_line',
        ],
    ),
    (
        'the guard refuses everything, blocking all work',
        '      if contains "$look" <"$scratch/$surface.$squash"; then\n',
        '      if true; then\n',
        [
            'test_clean_commit_is_accepted',
        ],
    ),
    # --- the third source: names from the file `tk.privateValuesFile` names ----------
    (
        'the file key is never read, so no listed name is a needle',
        'needles_file=$(git config --path "$FILE_KEY" 2>/dev/null)\n',
        'needles_file=\n',
        [
            'test_file_name_in_staged_content_is_refused',
            'test_file_name_in_the_commit_message_is_refused',
            'test_commit_msg_hook_run_by_hand_refuses_a_file_name',
            'test_pre_commit_hook_run_by_hand_refuses_a_file_name',
            'test_missing_file_refuses_and_the_remedy_restores_commits',
        ],
    ),
    (
        'the names are read and never reach the loop',
        '$(printf \'%s\\n\' "$file_rows" | sed "s/^/$FILE_KEY\t/")\n',
        '\n',
        [
            'test_file_name_in_staged_content_is_refused',
            'test_file_name_in_the_commit_message_is_refused',
            'test_file_name_recased_is_refused',
            'test_file_name_wrapped_across_two_lines_is_refused',
            'test_file_name_in_a_branch_name_is_refused',
        ],
    ),
    (
        'only the first listed name becomes a needle',
        '$(printf \'%s\\n\' "$file_rows" | sed "s/^/$FILE_KEY\t/")\n',
        '$(printf \'%s\\n\' "$file_rows" | sed -n "1s/^/$FILE_KEY\t/p")\n',
        [
            'test_every_listed_name_is_a_needle_not_only_the_first',
        ],
    ),
    (
        'a set key with no readable file is let through in silence',
        '    exit 1\n  fi\nfi\n',
        '    :\n  fi\nfi\n',
        [
            'test_missing_file_refuses_and_the_remedy_restores_commits',
            'test_a_directory_in_place_of_the_file_refuses',
        ],
    ),
    (
        'the regular-file check is dropped, so a FIFO blocks the commit',
        '  if [ ! -f "$needles_file" ] || [ ! -r "$needles_file" ] ||\n',
        '  if [ ! -r "$needles_file" ] ||\n',
        [
            'test_a_fifo_in_place_of_the_file_refuses_without_blocking',
        ],
    ),
    (
        'an unset key is treated as a missing file, refusing every commit',
        'if [ -n "$needles_file" ]; then\n',
        'if true; then\n',
        [
            'test_unset_file_key_protects_nothing_more',
            'test_clean_commit_is_accepted',
        ],
    ),
    (
        'the refusal of an unreadable file prints no remedy that runs',
        '"  Regenerate that file, or stop the promise with: git config --unset $FILE_KEY"',
        '"  Regenerate that file, or stop the promise with: git config --unset"',
        [
            'test_missing_file_refuses_and_the_remedy_restores_commits',
        ],
    ),
    (
        'a comment line is kept as a needle',
        '    if (substr($0, 1, 1) != "#") print }\' "$1"\n',
        '    print }\' "$1"\n',
        [
            'test_comment_and_blank_lines_are_not_needles',
        ],
    ),
    (
        'a byte-order mark stays glued to the first name',
        'gsub(/\\357\\273\\277/, ""); ',
        '',
        [
            'test_a_byte_order_mark_does_not_hide_the_first_name',
        ],
    ),
    (
        'a byte-order mark is stripped from the first line only',
        'gsub(/\\357\\273\\277/, ""); ',
        'if (NR == 1) sub(/^\\357\\273\\277/, ""); ',
        [
            'test_a_byte_order_mark_before_a_later_name_does_not_hide_it',
        ],
    ),
    (
        'a long needle keeps its separators, as before the fold',
        '    if [ "${#look}" -ge "$FOLD_MIN" ]; then\n',
        '    if false; then\n',
        [
            'test_listed_name_with_other_separators_in_the_message_is_refused',
            'test_listed_name_with_other_separators_in_added_lines_is_refused',
            'test_listed_name_wrapped_with_other_separators_is_refused',
            'test_folded_remedy_runs_and_finds_the_line',
        ],
    ),
    (
        'every needle is folded, however short',
        'FOLD_MIN=6\n',
        'FOLD_MIN=0\n',
        [
            'test_a_short_listed_name_keeps_its_separators',
        ],
    ),
    (
        'the joined lines of a file are not folded',
        '      { c = $2; if (ENVIRON["SQUASH"] == "fold_lines") gsub(/[^A-Za-z0-9]/, "", c) }\n',
        '      { c = $2 }\n',
        [
            'test_listed_name_wrapped_with_other_separators_is_refused',
        ],
    ),
    (
        'a folded hit prints a remedy that searches the raw diff',
        '"    see it:     git diff --cached --text -U0$squash_cmd | grep',
        '"    see it:     git diff --cached --text -U0 | grep',
        [
            'test_folded_remedy_runs_and_finds_the_line',
        ],
    ),
    (
        'a carriage return stays on each name',
        'sub(/\\r$/, ""); gsub(',
        'gsub(',
        [
            'test_a_carriage_return_does_not_hide_a_name',
        ],
    ),
    (
        'the whitespace around a name is kept',
        'gsub(/^[ \\t]+|[ \\t]+$/, "")\n',
        '\n',
        [
            'test_surrounding_whitespace_does_not_hide_a_name',
        ],
    ),
    (
        'a listed name is reported as if it were a config value',
        '    what="the name $quoted, listed in the file that git config $FILE_KEY names"\n',
        '    what="the value of: git config $key"\n',
        [
            'test_file_name_refusal_names_the_file_key_and_the_name',
        ],
    ),
    (
        'a listed name is printed unquoted, so its remedy does not run',
        '    quoted="\'$(printf \'%s\' "$value" | sed "s/\'/\'\\\\\\\\\'\'/g")\'"\n',
        '    quoted="\'$value\'"\n',
        [
            'test_file_name_remedy_runs_and_finds_the_line',
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
