#!/usr/bin/env python3
"""Mutation harness for the tk-queue suite.

Run: python3 tk/tests/mutations.py

A test that passes with the defect put back protects nothing. Each MUTATIONS
entry restores one defect by editing a copy of `bin/tk-queue`, reruns the tests
named alongside it, and REQUIRES them to fail. A mutation that no test catches
is reported as SURVIVED — that is a hole in the suite, not a passing result.

Each mutation switches off the RULE (the guard's decision), never a whole step:
deleting the step would also break tests that merely pass through it, which
proves nothing about the guard.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)
SRC = os.path.join(TK_DIR, "bin", "tk-queue")

# (label, old, new, [test names that must fail])
MUTATIONS = [
    ("T025 done/cancel/edit reject the displayed T-form again",
     'd.add_argument("id", type=parse_id)', 'd.add_argument("id", type=int)',
     ["TestPrefixedId.test_done_accepts_the_displayed_form"]),

    ("T025 the ID grammar loosens to a prefix match (\"6x\" → 6)",
     "ID_INPUT_RE.fullmatch(raw)", "ID_INPUT_RE.match(raw)",
     ["TestPrefixedId.test_garbage_is_still_rejected"]),

    ("T060 the queue lock stops serializing",
     "    if fcntl is None:\n        # No flock", "    if True:\n        # No flock",
     ["TestConcurrency.test_concurrent_adds_lose_nothing_and_never_reuse_an_id"]),

    ("T060 the temp file goes back to a shared name",
     'fd, tmp = tempfile.mkstemp(dir=d, prefix=os.path.basename(path) + ".tk-queue.",\n'
     '                               suffix=".tmp")',
     'tmp = path + ".tk-queue.tmp"\n'
     '    fd = os.open(tmp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)',
     ["TestAtomicWrite.test_concurrent_writers_never_leave_a_mixed_or_truncated_file"]),

    ("T060 a miss reports the flat \"no open item\" again",
     "fail(missing_item_message(memdir, content, wanted_id))",
     'fail(f"no open item **T{wanted_id:03d}** in next-steps.md (see `tk-queue list`)")',
     ["TestMissingItemMessage"]),

    ("T064 the project tag is dropped on close",
     '        line += f" **Project:** {tag_m.group(1)}."',
     '        pass',
     ["TestProjectTagInDoneLog.test_tag_reaches_the_done_log",
      "TestProjectTagInDoneLog.test_report_groups_by_tag_untagged_last"]),

    ("T064 --summary drops the tag (tag read from the title instead of the block)",
     "tag_m = PROJECT_TAG_RE.search(block)",
     "tag_m = PROJECT_TAG_RE.search(args.summary or item_title(block, limit=400))",
     ["TestProjectTagInDoneLog.test_tag_survives_summary_replacing_the_text"]),

    ("T064 report stops grouping by tag",
     "        if not any(tag for tag, _ in tagged):",
     "        if True:",
     ["TestProjectTagInDoneLog.test_report_groups_by_tag_untagged_last"]),

    ("T064 the log tag is read from the whole entry, notes included",
     "    m = LOG_TAG_RE.search(entry_text.split(\"\\n\", 1)[0])",
     "    m = PROJECT_TAG_RE.search(entry_text)",
     ["TestProjectTagInDoneLog.test_a_note_quoting_the_marker_does_not_become_a_group"]),

    ("T065 add stops refusing an embedded marker",
     "    ensure_no_embedded_marker(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                              criterion=args.criterion, source=args.source)",
     "    pass",
     ["TestEmbeddedMarker.test_add_refuses_a_marker_in_the_text",
      "TestEmbeddedMarker.test_add_refuses_it_in_every_free_text_flag",
      "TestEmbeddedMarker.test_list_groups_by_the_project_that_was_passed"]),

    ("T065 edit stops refusing an embedded marker",
     "    ensure_no_embedded_marker(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                              criterion=args.criterion)",
     "    pass",
     ["TestEmbeddedMarker.test_edit_refuses_a_marker_in_the_new_text"]),

    ("T065 close stops refusing an embedded marker",
     "    ensure_no_embedded_marker(summary=args.summary, outcome=outcome, note=args.note)",
     "    pass",
     ["TestEmbeddedMarker.test_close_refuses_a_marker_in_summary_and_note"]),

    ("T065 the guard's decision inverts (marker shape no longer matches)",
     'EMBEDDED_MARKER_RE = re.compile(r"\\*\\*(?:" + ANY_FIELD + r"):\\*\\*")',
     'EMBEDDED_MARKER_RE = re.compile(r"(?!x)x")',
     ["TestEmbeddedMarker.test_add_refuses_a_marker_in_the_text"]),

    ("T065 edit rewrites the FIRST marker again, eating the prose",
     "            m = matches[-1]", "            m = matches[0]",
     ["TestEmbeddedMarker.test_edit_rewrites_the_real_field_not_prose_that_looks_like_one"]),
]


def run_suite(tk_dir, names):
    tests = os.path.join(tk_dir, "tests")
    argv = [sys.executable, "-m", "unittest", "-v"] + [f"test_tk_queue.{n}" for n in names]
    return subprocess.run(argv, cwd=tests, capture_output=True, text=True)


def main():
    baseline = run_suite(TK_DIR, ["TestPrefixedId", "TestConcurrency", "TestMissingItemMessage",
                                  "TestDirResolution", "TestProjectTagInDoneLog",
                                  "TestEmbeddedMarker", "TestAtomicWrite"])
    if baseline.returncode != 0:
        print("BASELINE IS RED — fix the suite before mutating\n", baseline.stderr[-3000:])
        return 1

    src = open(SRC, encoding="utf-8").read()
    survived = []
    for label, old, new, names in MUTATIONS:
        if src.count(old) != 1:
            print(f"SKIP  {label}\n      anchor matched {src.count(old)}x, not once")
            survived.append(label)
            continue
        tmp = tempfile.mkdtemp(prefix="tk-mutation.")
        try:
            dst = os.path.join(tmp, "tk")
            shutil.copytree(TK_DIR, dst)
            with open(os.path.join(dst, "bin", "tk-queue"), "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
            r = run_suite(dst, names)
            if r.returncode == 0:
                print(f"SURVIVED  {label}\n          {', '.join(names)} still passed")
                survived.append(label)
            else:
                failed = [ln.split(" ")[1] for ln in (r.stderr or "").splitlines()
                          if ln.startswith(("FAIL: ", "ERROR: "))]
                print(f"caught    {label}\n          → {len(failed)} test(s) failed")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{len(MUTATIONS) - len(survived)}/{len(MUTATIONS)} mutations caught")
    if survived:
        print("SURVIVORS (the suite does not actually protect these):")
        for s in survived:
            print("  -", s)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
