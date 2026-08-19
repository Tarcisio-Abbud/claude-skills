#!/usr/bin/env python3
"""Mutation harness for `tk-contract` — puts each defect back; every test must fall.

Run: python3 tk/tests/mutations_tk_contract.py

A test that passes with its defect restored guards nothing, and reading the test
cannot tell you which it is. So each entry below restores one defect in a COPY
of `tk/`, runs only the tests named for it, and requires each of them to fail.
A mutation that SURVIVES is a hole in the suite, not a pass.

WHY THIS IS A SECOND FILE, beside `mutations.py`. That harness is the same idea
and predates this one, but its runner names its test module inline
(`test_tk_queue.<class>`) and its entries live in one hardcoded list, so there
is no seam a sibling suite can enter through. Appending here would have meant
editing a file another slice is holding. The runner below therefore takes the
test module and the entry list as ARGUMENTS — which is the seam the two files
need to become one, whenever someone unifies them: `mutations.py` can import
`run` from here and pass its own list, and nothing about its entries changes.

An entry is `(label, old, new, [tests that must fail])`, plus an optional 5th
element naming the source file the anchor lives in, relative to `tk/` (default
`bin/tk-contract`) — the same shape the older harness grew for `bin/tk_site.py`.

The anchor is a plain SUBSTRING and it must match EXACTLY ONCE: zero matches
means the code moved out from under the entry, more than one means the mutation
is not the one described. Both are reported as UNRUNNABLE and fail the run —
an anchor that quietly stopped matching is a test nobody is proving any more.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.normpath(os.path.join(HERE, os.pardir))
DEFAULT_SRC = os.path.join("bin", "tk-contract")
TEST_MODULE = "test_tk_contract"
CLASSES = ("TestDeterminism", "TestFleetDivisor", "TestCeilings", "TestRoleTable",
           "TestBlockContent")

MUTATIONS = [
    # --- the fleet divisor, and the two ceilings ---------------------------
    ("the fleet divisor is read and then ignored",
     'f"so this run\'s share is at most {local // fleet} at a time.")',
     'f"so this run\'s share is at most {local} at a time.")',
     ["TestFleetDivisor.test_the_fleet_divides_the_local_ceiling"]),

    ("a share that rounds to none is rounded up to one instead",
     "    elif local // fleet == 0:", "    elif False:",
     ["TestFleetDivisor.test_a_fleet_wider_than_the_ceiling_dispatches_none"]),

    ("the fleet divides the cloud ceiling too",
     'lines.append(f"- Cloud subagents: at most {cloud} at a time. The fleet divisor never "',
     'lines.append(f"- Cloud subagents: at most {cloud // (fleet or 1)} at a time. '
     'The fleet divisor never "',
     ["TestFleetDivisor.test_the_fleet_does_not_divide_the_cloud_ceiling"]),

    ("--fleet accepts a fleet of none",
     "    if int(raw) < 1:", "    if int(raw) < 0:",
     ["TestFleetDivisor.test_a_fleet_that_is_not_a_positive_whole_number_is_refused"]),

    ("--fleet accepts what is not a whole number",
     '    if not re.fullmatch(r"[0-9]+", raw):', "    if False:",
     ["TestFleetDivisor.test_a_fleet_that_is_not_a_positive_whole_number_is_refused"]),

    ("an absent local ceiling gets a default the bin invented",
     "    local = site.ceilings.get(LOCAL_KEY)", "    local = site.ceilings.get(LOCAL_KEY, 3)",
     ["TestCeilings.test_an_absent_ceiling_is_stated_absent_never_invented"]),

    ("an absent cloud ceiling gets a default the bin invented",
     "    cloud = site.ceilings.get(CLOUD_KEY)", "    cloud = site.ceilings.get(CLOUD_KEY, 4)",
     ["TestCeilings.test_an_absent_ceiling_is_stated_absent_never_invented"]),

    ("the local ceiling is a literal in the bin instead of the file's value",
     'lines.append(f"- Local subagents: at most {local} at a time. No fleet divisor was "',
     'lines.append(f"- Local subagents: at most 6 at a time. No fleet divisor was "',
     ["TestCeilings.test_the_ceilings_are_read_from_the_file_not_from_the_bin"]),

    ("this machine's identity is a literal in the bin",
     'f"   remote sandbox would not share. You were dispatched from `{site.identity}`.",',
     '"   remote sandbox would not share. You were dispatched from `alpha`.",',
     ["TestCeilings.test_the_identity_in_the_block_comes_from_the_file"]),

    # --- the site file: absent is not the same as defective ----------------
    ("a missing site file is reported as a defective one",
     "    if site is None:", "    if False:",
     ["TestCeilings.test_no_site_file_asks_for_one_and_shows_the_format"]),

    ("a defective site file is reported as a missing one",
     "    except tk_site.SiteError as e:\n        fail(str(e))",
     "    except tk_site.SiteError as e:\n        fail(tk_site.missing_file_message())",
     ["TestCeilings.test_a_defective_site_file_names_the_defect_instead"]),

    # --- the role table is the single source -------------------------------
    ("the row is a copy the bin carries",
     "    for row in roles:\n        if row.role == name:\n            return row",
     "    for row in roles:\n        if row.role == name:\n"
     '            return Role(name, "parent", "session", "local", row.note)',
     ["TestRoleTable.test_the_row_is_read_from_the_table"]),

    ("a role absent from the table gets a silent default",
     '    raise PolicyError(\n'
     '        f"the role table declares no role {name!r}. It carries: "',
     "    return roles[0]\n"
     '    raise PolicyError(\n'
     '        f"the role table declares no role {name!r}. It carries: "',
     ["TestRoleTable.test_an_unknown_role_is_refused_with_the_roles_that_exist"]),

    ("a schema this parser cannot read is parsed anyway",
     "            if m.group(1) != SCHEMA:", "            if False:",
     ["TestRoleTable.test_a_schema_it_cannot_read_fails_loud"]),

    ("a value outside the closed vocabulary is accepted",
     "            if value not in allowed:", "            if False:",
     ["TestRoleTable.test_a_value_outside_the_vocabulary_is_a_defect_not_a_default"]),

    ("the header is not checked, so a reordered column swaps two values",
     "    if tuple(header) != COLUMNS:", "    if False:",
     ["TestRoleTable.test_a_reordered_header_is_refused"]),

    ("the alignment row is not checked, so a table missing it loses its first role",
     "    if len(align) != len(COLUMNS) or not all(ALIGN_RE.match(c) for c in align):",
     "    if False:",
     ["TestRoleTable.test_a_missing_alignment_row_is_refused_not_skipped"]),

    ("a row short of a cell is read anyway",
     "        if len(cells) != len(COLUMNS):", "        if False:",
     ["TestRoleTable.test_a_row_short_of_a_cell_is_refused"]),

    ("a row with no role cell is kept",
     "        if not row.role:", "        if False:",
     ["TestRoleTable.test_an_empty_role_cell_is_refused"]),

    ("a duplicate role is accepted and the first one wins silently",
     "        if row.role in seen:", "        if False:",
     ["TestRoleTable.test_a_duplicate_role_is_refused"]),

    ("an empty note passes as a deliberate silence",
     "        if not row.note:", "        if False:",
     ["TestRoleTable.test_an_empty_note_is_refused"]),

    ("the note is parsed instead of emitted verbatim",
     'f"Note: {row.note}",', 'f"Note: {row.note.split(chr(8212))[0].strip()}",',
     ["TestRoleTable.test_the_note_is_emitted_verbatim"]),

    ("the markers stop bounding the table, so a draft row in the prose is a role",
     '    rows = [(n + 1, lines[n]) for n in range(start + 1, end) '
     'if lines[n].lstrip().startswith("|")]',
     '    rows = [(n + 1, lines[n]) for n in range(0, len(lines)) '
     'if lines[n].lstrip().startswith("|")]',
     ["TestRoleTable.test_a_row_outside_the_markers_is_not_a_role"]),

    ("a table that never closes is read to the end of the file",
     "    if end is None:", "    if False:",
     ["TestRoleTable.test_a_table_that_never_closes_is_refused"]),

    ("a file with no table at all is parsed anyway",
     "    if start is None:", "    if False:",
     ["TestRoleTable.test_no_table_at_all_is_refused"]),

    ("a misspelt marker is reported as no table at all",
     "if OPEN_LOOSE in text else \"\")", "if False else \"\")",
     ["TestRoleTable.test_a_misspelt_marker_says_so_instead_of_just_not_finding_it"]),

    ("a table with a header and nothing else is read past its rows",
     "    if len(rows) < 3:", "    if False:",
     ["TestRoleTable.test_a_table_with_no_role_in_it_is_refused"]),

    ("an unreadable table comes back as a traceback instead of a diagnosis",
     "    except OSError as e:\n        fail(f\"the role table {args.policy} cannot be read",
     "    except ZeroDivisionError as e:\n        fail(f\"the role table {args.policy} "
     "cannot be read",
     ["TestRoleTable.test_a_table_that_cannot_be_read_is_refused_not_defaulted"]),

    ("a table that is not UTF-8 comes back as a traceback",
     "    except UnicodeDecodeError as e:\n        fail(f\"the role table {args.policy} "
     "is not valid UTF-8",
     "    except ZeroDivisionError as e:\n        fail(f\"the role table {args.policy} "
     "is not valid UTF-8",
     ["TestRoleTable.test_a_table_that_is_not_utf8_is_refused"]),

    ("--fleet gains a default, so a run without one no longer gets the whole ceiling",
     '    p.add_argument("--fleet", type=fleet_size, default=None,',
     '    p.add_argument("--fleet", type=fleet_size, default=2,',
     ["TestFleetDivisor.test_without_a_fleet_the_whole_ceiling_is_this_run_s"]),

    ("a table path that does not exist is reported as a defective file",
     "    if not os.path.exists(args.policy):", "    if False:",
     ["TestRoleTable.test_a_table_that_is_not_there_is_refused_not_defaulted"]),

    ("the plain-file guard goes, and a table that is a pipe HANGS the run",
     "    if not os.path.isfile(args.policy):", "    if False:",
     ["TestRoleTable.test_a_table_that_is_not_a_plain_file_is_refused",
      "TestRoleTable.test_a_table_that_is_a_pipe_does_not_hang"]),

    ("a byte order mark on the opening marker hides the whole table",
     '            text = f.read().replace("\\ufeff", "")', "            text = f.read()",
     ["TestRoleTable.test_a_byte_order_mark_does_not_hide_the_table"]),

    ("the default table is looked for somewhere it is not",
     '    os.path.join(BIN_DIR, os.pardir, "reference", "subagent-policy.md"))',
     '    os.path.join(BIN_DIR, os.pardir, "references", "subagent-policy.md"))',
     ["TestRoleTable.test_the_default_table_is_the_one_beside_the_bin"]),

    # --- determinism, and the four rules the block exists to carry ---------
    ("the block stops being byte-stable between two identical runs",
     'lines.append("- Quota is ONE window across both venues. A cloud run buys RAM, '
     'not quota, "',
     'lines.append(f"- Quota is ONE window across both venues ({os.getpid()}). '
     'A cloud run buys RAM, not quota, "',
     ["TestDeterminism.test_same_input_gives_the_same_bytes"]),

    ("the cwd leaks into the block",
     '        f"- the site file `{site.path}` — this machine, and its ceilings;",',
     '        f"- the site file `{site.path}` in {os.getcwd()} — this machine, '
     'and its ceilings;",',
     ["TestDeterminism.test_the_cwd_does_not_leak_into_the_block"]),

    ("the block stops saying that an empty return is a failure",
     '        "An EMPTY return is a failure that reads as success: '
     'the orchestrator gets no error",',
     '        "Return when the work is done.",',
     ["TestBlockContent.test_it_says_an_empty_return_is_a_failure"]),

    ("the block asks where you ran instead of for a venue signature",
     '        "2. **Your venue signature.** The working directory you resolved, '
     'plus a marker the",',
     '        "2. **Where you ran.** Say roughly where you ran, plus a marker the",',
     ["TestBlockContent.test_it_demands_the_venue_signature_and_says_who_reads_it"]),

    ("the block asks for a summary — the word the package flow reserves "
     "for what must NOT be believed",
     '        "1. **The work.** The artifact, the paths you touched, the finding, '
     'the verdict —",',
     '        "1. **The work.** A summary of the artifact, the paths, the finding, '
     'the verdict —",',
     ["TestBlockContent.test_it_never_calls_the_return_a_summary"]),

    ("the measured reading rule degrades into generic advice",
     '        "- **~85k went to reading source files raw.** A file above ~500 lines '
     'that you are",',
     '        "- **Read only what you need.** A file that you are",',
     ["TestBlockContent.test_it_carries_the_two_measured_reading_rules"]),

    ("the deviation line loses this role's own default",
     '        f"    {row.role}: {row.model}→<what actually ran> — reason",',
     '        "    <role>: <default>→<what actually ran> — reason",',
     ["TestBlockContent.test_it_asks_for_the_deviation_log_in_the_policy_s_format"]),

    ("the block loses the markers that let a consumer replace it",
     '        f"<!-- tk:contract schema=1 role={row.role} -->",',
     '        f"## contract for {row.role}",',
     ["TestBlockContent.test_the_block_is_delimited_so_it_can_be_replaced"]),
]


def run_suite(tk_dir, module, names):
    """The named tests, run from the (possibly mutated) tree's own tests dir."""
    tests = os.path.join(tk_dir, "tests")
    argv = [sys.executable, "-m", "unittest", "-v"] + [f"{module}.{n}" for n in names]
    return subprocess.run(argv, cwd=tests, capture_output=True, text=True)


def unproved(mutations, module, classes, tk_dir):
    """Tests that no entry names — the hole a green score cannot show you.

    A run reports `N/N killed` and means it: N is the number of mutants SOMEONE
    WROTE. A guard whose test nobody mutated is invisible to that number, and
    the suite reads as fully proved while one test is protecting nothing. So the
    tests are enumerated from the module itself and checked against the entries,
    rather than trusted to be in sync."""
    sys.path.insert(0, os.path.join(tk_dir, "tests"))
    module_obj = __import__(module)
    named = {name for entry in mutations for name in entry[3]}
    missing = []
    for cls_name in classes:
        cls = getattr(module_obj, cls_name)
        for attr in dir(cls):
            if attr.startswith("test_") and f"{cls_name}.{attr}" not in named:
                missing.append(f"{cls_name}.{attr}")
    return sorted(missing)


def run(mutations=MUTATIONS, module=TEST_MODULE, classes=CLASSES, tk_dir=TK_DIR,
        default_src=DEFAULT_SRC):
    """Replay every mutation. Returns the process exit code.

    The arguments are the seam: another suite passes its own list, its own test
    module and its own default source, and reuses everything below unchanged."""
    baseline = run_suite(tk_dir, module, list(classes))
    if baseline.returncode != 0:
        print("BASELINE IS RED — fix the suite before mutating it\n")
        print(baseline.stderr[-4000:])
        return 1
    print(f"baseline green ({module})\n")

    orphans = unproved(mutations, module, classes, tk_dir)
    for name in orphans:
        print(f"UNPROVED   {name} — no mutation entry names this test")
    if orphans:
        print()

    sources = {}
    for entry in mutations:
        rel = entry[4] if len(entry) > 4 else default_src
        if rel not in sources:
            with open(os.path.join(tk_dir, rel), encoding="utf-8") as f:
                sources[rel] = f.read()

    survived, unrunnable = [], []
    for entry in mutations:
        label, old, new, names = entry[:4]
        rel = entry[4] if len(entry) > 4 else default_src
        src = sources[rel]
        if src.count(old) != 1:
            unrunnable.append(f"{label} (anchor matched {src.count(old)}x, not once)")
            print(f"UNRUNNABLE {label}\n           anchor matched {src.count(old)}x, not once")
            continue
        tmp = tempfile.mkdtemp(prefix="tk-contract-mutation.")
        try:
            dst = os.path.join(tmp, "tk")
            shutil.copytree(tk_dir, dst)
            with open(os.path.join(dst, rel), "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
            # one test at a time: a batch that goes red says nothing about
            # WHICH of the named tests noticed, and a mutation is only proved
            # by the test that claims to prove it
            alive = [n for n in names if run_suite(dst, module, [n]).returncode == 0]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if alive:
            survived.append(f"{label} — survived: {', '.join(alive)}")
            print(f"SURVIVED   {label}\n           still green: {', '.join(alive)}")
        else:
            print(f"killed     {label}")

    print(f"\n{len(mutations) - len(survived) - len(unrunnable)}/{len(mutations)} killed"
          f", {len(orphans)} test(s) no entry proves")
    for line in survived + unrunnable + [f"UNPROVED {n}" for n in orphans]:
        print(f"  ! {line}")
    return 1 if survived or unrunnable or orphans else 0


if __name__ == "__main__":
    sys.exit(run())
