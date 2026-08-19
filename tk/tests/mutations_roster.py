#!/usr/bin/env python3
"""Mutation harness for the tk-roster suite.

Run: python3 tk/tests/mutations_roster.py

Same contract as `mutations.py` beside it, for the same reason: a test that
passes with the defect put back protects nothing. Each entry restores one
defect in a copy of the tree, reruns the tests named alongside it, and REQUIRES
them to fail. A mutation no test catches is reported as SURVIVED — a hole in the
suite, not a passing result.

WHY A SECOND FILE. `mutations.py` runs every named test as `test_tk_queue.<name>`,
hardcoded in its `run_suite()`, so a roster entry cannot even be expressed there
without editing it — and that file was another session's while this slice was
written. The two merge into one harness the day it is free: this file's entries
already carry the 5th element (the source, relative to tk/) that `mutations.py`
grew for exactly this, and the merge is that plus one line teaching `run_suite`
which module a name belongs to.

KNOWN BLIND SPOT, the same one `mutations.py` documents: a score of N/N measures
only the mutants WRITTEN. A guard nobody mutated is invisible here — reading the
list of what is covered is the check, never the tally.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)
ROSTER = "bin/tk-roster"
SITE = "bin/tk_site.py"

# (label, old, new, [tests that must fail], source relative to tk/)
MUTATIONS = [
    ("T128 roster any project directory counts, queue file or not",
     "if os.path.isfile(os.path.join(root, name, MEMORY_DIR, QUEUE_FILE))]", "if True]",
     ["TestSweep.test_a_directory_without_the_queue_file_is_not_a_project"], ROSTER),

    ("T128 roster the queue is the done log, so a finished project is swept",
     'QUEUE_FILE = "next-steps.md"', 'QUEUE_FILE = "done-log.md"',
     ["TestSweep.test_a_directory_without_the_queue_file_is_not_a_project"], ROSTER),

    ("T128 site the encoding alphabet keeps a character tk-queue replaces",
     'PROJECT_ALPHABET = "A-Za-z0-9-"', 'PROJECT_ALPHABET = "A-Za-z0-9_-"',
     ["TestProjectPath.test_the_path_is_the_directory_that_encodes_to_the_name"], SITE),

    ("T128 roster a projects root that does not exist is a failure to report",
     "    except FileNotFoundError:\n"
     "        # not a failure of this machine's setup: a machine where no session ever\n"
     "        # ran has no such directory, and an empty roster is the true answer\n"
     "        return []",
     "    except FileNotFoundError:\n        fail(\"no projects root\")",
     ["TestSweep.test_an_absent_projects_root_is_an_empty_roster_not_a_failure"], ROSTER),

    ("T128 roster a name no POSIX path encodes to is resolved anyway",
     '    return name.startswith("-")', "    return True",
     ["TestProjectPath.test_a_name_another_machine_wrote_is_not_resolved_as_a_shorter_path"],
     ROSTER),

    ("T128 roster a queue another machine wrote is reported as a gone directory",
     "    if not encodes_a_posix_path(name):\n        return \"the name encodes no POSIX "
     "absolute path, so another machine wrote it\"\n",
     "",
     ["TestProjectPath.test_a_name_another_machine_wrote_is_not_resolved_as_a_shorter_path"],
     ROSTER),

    ("T128 roster the report names the wrong list as the keeper",
     '        return "fleet-allow"', '        return "fleet-deny"',
     ["TestAllowDeny.test_fleet_allow_admits_only_what_it_lists"], ROSTER),

    ("T128 roster an ambiguous name is dispatched to the first match",
     "        if len(paths) == 1:", "        if paths:",
     ["TestProjectPath.test_two_directories_encoding_to_one_name_are_not_dispatchable"], ROSTER),

    ("T128 roster a symlinked directory counts as a candidate",
     "if not entry.is_dir(follow_symlinks=False):", "if not entry.is_dir(follow_symlinks=True):",
     ["TestProjectPath.test_a_symlink_does_not_make_a_project_ambiguous"], ROSTER),

    ("T128 roster deny is consulted only when there is no allowlist",
     "    if any(list_key(e) == name for e in deny):",
     "    if not allow and any(list_key(e) == name for e in deny):",
     ["TestAllowDeny.test_a_name_in_both_lists_is_denied"], ROSTER),

    ("T128 roster an absent allowlist excludes everything",
     "    if allow and not any(list_key(e) == name for e in allow):",
     "    if not any(list_key(e) == name for e in allow):",
     ["TestAllowDeny.test_without_lists_every_queue_enters"], ROSTER),

    ("T128 roster the allowlist admits what it does NOT list",
     "    if allow and not any(list_key(e) == name for e in allow):",
     "    if allow and any(list_key(e) == name for e in allow):",
     ["TestAllowDeny.test_fleet_allow_admits_only_what_it_lists"], ROSTER),

    ("T128 roster a list entry that is a path is matched verbatim, never encoded",
     '    return project_slug(entry) if entry.startswith("/") else entry',
     "    return entry",
     ["TestAllowDeny.test_an_entry_written_as_a_path_names_the_same_project"], ROSTER),

    ("T128 roster an entry that matched nothing is passed over in silence",
     "        unmatched = [e for e in entries if list_key(e) not in listed]",
     "        unmatched = []",
     ["TestAllowDeny.test_an_entry_matching_no_queue_is_reported"], ROSTER),

    ("T128 roster every entry is reported as unmatched, matched ones included",
     "        unmatched = [e for e in entries if list_key(e) not in listed]",
     "        unmatched = list(entries)",
     ["TestAllowDeny.test_a_matching_entry_is_not_reported_as_unmatched"], ROSTER),

    ("T128 roster a rotten site file is read as an absent one",
     "    except tk_site.SiteError as e:\n        fail(str(e))",
     "    except tk_site.SiteError as e:\n        site = None",
     ["TestSiteFile.test_a_rotten_site_file_stops_the_sweep_instead_of_ignoring_the_lists"],
     ROSTER),

    ("T128 roster an absent site file is swept without a word",
     "    if site is None:\n        print(", "    if False:\n        print(",
     ["TestSiteFile.test_no_site_file_sweeps_everything_and_says_the_file_is_absent"], ROSTER),

    ("T128 site an empty fleet list reads as an absent one",
     "        if not entries:", "        if False:",
     ["TestListValidation.test_an_empty_list_is_refused_not_read_as_an_absent_one"], SITE),

    ("T128 site a project name outside the encoding alphabet is accepted",
     "            if not PROJECT_NAME_RE.match(entry):", "            if False:",
     ["TestListValidation.test_a_relative_path_names_no_project",
      "TestListValidation.test_a_name_outside_the_encoding_alphabet_is_refused"], SITE),

    ("T128 site an unknown key is refused instead of ignored",
     "        pairs[key] = value.strip()",
     "        pairs[key] = value.strip()\n"
     "        if key not in REQUIRED + CEILINGS + FLEET_LISTS:\n"
     '            raise SiteError(f"{path}:{n}: unknown key {key!r}.")',
     ["TestSiteFile.test_an_unknown_key_is_still_ignored"], SITE),
]


def run_suite(tk_dir, names):
    argv = [sys.executable, "-m", "unittest", "-v"] + [f"test_tk_roster.{n}" for n in names]
    return subprocess.run(argv, cwd=os.path.join(tk_dir, "tests"),
                          capture_output=True, text=True)


def main():
    baseline = run_suite(TK_DIR, ["TestSweep", "TestProjectPath", "TestSiteFile",
                                  "TestAllowDeny", "TestListValidation"])
    if baseline.returncode != 0:
        print("BASELINE IS RED — fix the suite before mutating\n", baseline.stderr[-3000:])
        return 1

    sources, survived, unrunnable = {}, [], []
    for label, old, new, names, rel in MUTATIONS:
        if rel not in sources:
            with open(os.path.join(TK_DIR, rel), encoding="utf-8") as f:
                sources[rel] = f.read()
        src = sources[rel]
        if src.count(old) != 1:
            # NOT a survivor: the mutation never ran, so it says nothing about
            # the suite. Still a failure — a stale anchor silently stops proving
            # whatever it used to prove — but calling it "survived" would lie
            unrunnable.append(f"{label} (anchor matched {src.count(old)}x, not once)")
            print(f"UNRUNNABLE {label}\n           anchor matched {src.count(old)}x, not once")
            continue
        tmp = tempfile.mkdtemp(prefix="tk-roster-mutation.")
        try:
            dst = os.path.join(tmp, "tk")
            # NOT the bytecode cache: copytree preserves mtimes, so a copied
            # __pycache__ entry still matches its copied source and Python
            # imports the PRE-MUTATION bytecode — reporting a guard as
            # unprotected when it is merely unmutated
            shutil.copytree(TK_DIR, dst, ignore=shutil.ignore_patterns("__pycache__"))
            with open(os.path.join(dst, rel), "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
            # EACH named test must fall on its own: run as one batch, a listed
            # test that quietly still passes stays invisible behind another's fall
            still_passing = [n for n in names if run_suite(dst, [n]).returncode == 0]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if still_passing:
            survived.append(f"{label} → {', '.join(still_passing)} still passed")
            print(f"SURVIVED   {label}\n           {', '.join(still_passing)} still passed")
        else:
            print(f"caught     {label}\n           → all {len(names)} named test(s) fell")

    ran = len(MUTATIONS) - len(unrunnable)
    print(f"\n{ran - len(survived)}/{ran} mutations caught"
          + (f" ({len(unrunnable)} could not run)" if unrunnable else ""))
    for title, items in (("SURVIVORS (the suite does not actually protect these)", survived),
                         ("UNRUNNABLE (stale anchor — proves nothing until fixed)", unrunnable)):
        if items:
            print(f"{title}:")
            for i in items:
                print("  -", i)
    return 1 if survived or unrunnable else 0


if __name__ == "__main__":
    sys.exit(main())
