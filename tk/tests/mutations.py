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

KNOWN BLIND SPOT — vacuity at SUBTEST level. This harness reads a test's exit
status, and one falling subTest already reddens the whole test. So a test whose
subtests are individually vacuous still reports as "caught" as long as ONE of
them falls, and nothing here can see the others. Two live examples, both
annotated in the test that carries them:
TestRiskDeletion.test_the_reserved_word_is_case_and_space_tolerant (the `none`
form survives the case-tolerance mutation) and
TestCeilingScope.test_every_short_field_edit_passes_without_force (`--class`
survives the block-ceiling mutation, because swapping AUTONOMOUS for any other
class SHRINKS the item). Reading the failure list, not the tally, is what catches
these — which is why the PR body pastes the measured lines.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)
DEFAULT_SRC = os.path.join("bin", "tk-queue")
TEST_MODULE = "test_tk_queue"
# The other two sources this list anchors into, and the module whose tests prove
# them. They arrived with the twenty entries absorbed from `mutations_roster.py`
# (T119): one list, because a second harness existed only for the hardcoded
# module name below and for nothing else.
ROSTER = os.path.join("bin", "tk-roster")
SITE = os.path.join("bin", "tk_site.py")
ROSTER_TEST_MODULE = "test_tk_roster"
TEST_MODULES = (TEST_MODULE, ROSTER_TEST_MODULE)

sys.path.insert(0, HERE)
from mutations_tk_contract import (  # noqa: E402 (path above)
    load_module, misnamed, test_classes, unproved)

# ENTRIES THAT NAME A TEST WHICH DOES NOT EXIST. The defect is in the LIST, not
# in the suite: unittest answers a name it cannot load with a non-zero exit, and
# `run_suite` below reads non-zero as "the named test fell" — so a typo scored
# itself as coverage, which is worse than an uncovered guard. Such entries are
# excluded from the tally and reported apart, and this is the debt the list
# carries: a ceiling to LOWER as entries are repaired, never to raise. Measured
# 2026-09-05: nine entries name five tests renamed out from under them.
KNOWN_MISNAMED = 9

# TESTS NO ENTRY NAMES. A run prints `N/N caught` and means it — but N counts
# the mutants SOMEONE WROTE, so a test nobody mutated is invisible to that
# number, and the suite reads as fully proved while that test protects nothing.
# They are enumerated from the module and reported, and this is the debt the
# list carries: a ceiling to LOWER, never to raise. Measured 2026-09-05: 61 of
# the suite's 480 test methods. Triaging them is not this item's work; noticing
# a sixty-second one is.
KNOWN_UNPROVED = 61

# The same debt for the suite absorbed with the roster entries (T119), kept as
# its OWN number rather than folded into the one above. Folding would have
# RAISED a ceiling whose whole rule is that it only ever falls, and the two
# debts are not one: this one arrived with a harness that never had an orphan
# check at all. Measured 2026-09-05: 4 of test_tk_roster's 22 test methods.
KNOWN_UNPROVED_ROSTER = 4

# (label, old, new, [test names that must fail]) — plus an optional 5th element,
# the source file the anchor lives in, relative to tk/ (default: bin/tk-queue).
#
# `old` and `new` may each be a LIST of the same length, applied in order. A
# defect that two guards jointly prevent cannot be replayed one guard at a time:
# switch off the guard alone and the correct writer behind it still writes the
# right file, so nothing falls and the entry reports a survivor that is really a
# pair. The measured case is T169's anchor — `cmd_edit`'s readback REFUSES every
# mis-positioned class `write_class_segment` can produce, so the three position
# entries below exit 1 on the gate and the bad FILE their tests assert against is
# never written. Paired with the readback relaxed, the write lands and the file
# assertions are what kill. Both forms are kept: one proves the gate, one proves
# the position.
# The queue's guards are not all in one file any more: the site file's reader is
# a module of its own, because the sibling bins read the same file and a second
# parser for it would be a second answer to "which environments exist".
MUTATIONS = [
    ("T025 done/cancel/edit reject the displayed T-form again",
     'd.add_argument("id", type=parse_id)', 'd.add_argument("id", type=int)',
     ["TestPrefixedId.test_done_accepts_the_displayed_form"]),

    ("T025 cancel rejects the displayed T-form again",
     'c.add_argument("id", type=parse_id)', 'c.add_argument("id", type=int)',
     ["TestPrefixedId.test_cancel_and_edit_accept_it_too"]),

    ("T025 edit rejects the displayed T-form again",
     'e.add_argument("id", type=parse_id)', 'e.add_argument("id", type=int)',
     ["TestPrefixedId.test_cancel_and_edit_accept_it_too"]),

    ("T025 the ID grammar loosens to a prefix match (\"6x\" → 6)",
     "ID_INPUT_RE.fullmatch(raw)", "ID_INPUT_RE.match(raw)",
     ["TestPrefixedId.test_garbage_is_still_rejected"]),

    # named test is the DETERMINISTIC one. The race test in the same class covers
    # the same fix end to end, but it detects a lost update by timing and passes
    # by luck often enough that naming it here would report false survivors
    ("T060 the queue lock stops serializing",
     "    if fcntl is None:\n        # No flock", "    if True:\n        # No flock",
     ["TestConcurrency.test_a_second_writer_waits_for_the_lock"]),

    ("T060 the temp file goes back to a shared name",
     'fd, tmp = tempfile.mkstemp(dir=d, prefix=os.path.basename(path) + ".tk-queue.",\n'
     '                               suffix=".tmp")',
     'tmp = path + ".tk-queue.tmp"\n'
     '    fd = os.open(tmp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)',
     ["TestAtomicWrite.test_concurrent_writers_never_leave_a_mixed_or_truncated_file"]),

    ("T060 the rename publishes mkstemp's 0600 over the file's own mode",
     "        os.chmod(tmp, mode)", "        pass",
     ["TestAtomicWrite.test_the_rename_keeps_the_file_mode"]),

    ("T060 a miss reports the flat \"no open item\" again",
     "fail(missing_item_message(memdir, content, wanted_id))",
     'fail(f"no open item **T{wanted_id:03d}** in next-steps.md (see `tk-queue list`)")',
     ["TestMissingItemMessage"]),

    ("T064 the project tag is dropped on close",
     '        line += f" **Project:** {tag}."',
     '        pass',
     ["TestProjectTagInDoneLog.test_tag_reaches_the_done_log",
      "TestProjectTagInDoneLog.test_report_groups_by_tag_untagged_last"]),

    ("T064 --summary drops the tag (tag read from the title instead of the block)",
     '    tag = marker_value(block, "Project", PROJECT_TAG_VALUE_RE)',
     '    tag = marker_value(args.summary or item_title(block, limit=400), "Project",'
     " PROJECT_TAG_VALUE_RE)",
     ["TestProjectTagInDoneLog.test_tag_survives_summary_replacing_the_text"]),

    ("T064 report stops grouping by tag",
     '        if grouped is None:\n            print("\\n".join(lines))',
     '        if True:\n            print("\\n".join(lines))',
     ["TestProjectTagInDoneLog.test_report_groups_by_tag_untagged_last"]),

    ("T064/T065 the untagged group stops going last",
     "    order = (named if by_position else sorted(named)) + "
     "([None] if None in groups else [])",
     "    order = sorted(groups, key=lambda k: (k is not None, k or ''))",
     ["TestProjectTagInDoneLog.test_report_groups_by_tag_untagged_last"]),

    ("T064 the log tag is read from the whole entry, notes included",
     "    m = LOG_TAG_RE.search(entry_text.split(\"\\n\", 1)[0])",
     "    m = PROJECT_TAG_RE.search(entry_text)",
     ["TestProjectTagInDoneLog.test_a_note_quoting_the_marker_does_not_become_a_group"]),

    ("T065 add stops refusing an embedded marker",
     "    ensure_no_embedded_marker(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                              criterion=args.criterion, source=args.source,\n"
     "                              deferred=args.deferred)",
     "    pass",
     # NOT test_list_groups_by_the_project_that_was_passed: it adds clean text, so
     # it passes with the guard off. Listing it would claim a proof the run cannot make
     ["TestEmbeddedMarker.test_add_refuses_a_marker_in_the_text",
      "TestEmbeddedMarker.test_add_refuses_it_in_every_free_text_flag"]),

    ("T065 edit stops refusing an embedded marker",
     "    ensure_no_embedded_marker(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                              criterion=args.criterion, deferred=args.deferred)",
     "    pass",
     ["TestEmbeddedMarker.test_edit_refuses_a_marker_in_the_new_text"]),

    ("T065 close stops refusing an embedded marker",
     "    ensure_no_embedded_marker(summary=args.summary, outcome=outcome)",
     "    pass",
     ["TestEmbeddedMarker.test_close_refuses_a_marker_in_summary_and_outcome"]),

    ("T065 the guard's decision inverts (marker shape no longer matches)",
     'FIELD_MARKER_ANY_RE = re.compile(r"\\*\\*(" + ANY_FIELD + r"):\\*\\*")',
     'FIELD_MARKER_ANY_RE = re.compile(r"(?!x)(x)")',
     ["TestEmbeddedMarker.test_add_refuses_a_marker_in_the_text"]),

    # the opposite direction, which no other mutation covers: a guard that over-refuses
    # blocks legitimate prose, and only the false-positive test can see it
    ("T065 the guard broadens to the bare field name, refusing ordinary prose",
     'FIELD_MARKER_ANY_RE = re.compile(r"\\*\\*(" + ANY_FIELD + r"):\\*\\*")',
     'FIELD_MARKER_ANY_RE = re.compile(r"(" + ANY_FIELD + r")")',
     ["TestEmbeddedMarker.test_plain_prose_naming_the_fields_is_not_refused"]),

    ("T064/T060 an ID quoted in a --note or an outcome counts as closed again",
     "    return wanted_id in done_log_ids(memdir)",
     '    log = read(os.path.join(memdir, "done-log.md")) or ""\n'
     '    return re.search(r"\\bT%03d\\b" % wanted_id, log) is not None',
     ["TestMissingItemMessage.test_an_id_merely_quoted_in_the_log_is_not_closed"]),

    # --- T088: an ID is allocated at a POSITION, not wherever the text says it ---

    ("T088 allocation goes back to regexing the whole text of both files",
     '    open_items = read(os.path.join(memdir, "next-steps.md")) or ""\n'
     "    return max(ids_at(open_items, ITEM_ID_RE) | done_log_ids(memdir), default=0)",
     '    ids = set()\n'
     '    for name in ("next-steps.md", "done-log.md"):\n'
     '        content = read(os.path.join(memdir, name)) or ""\n'
     '        ids |= {int(m.group(1)) for m in re.finditer(r"\\bT(\\d{3,})\\b", content)}\n'
     "    return max(ids, default=0)",
     ["TestIdAllocationScope.test_a_note_quoting_an_id_does_not_burn_the_next_number",
      "TestIdAllocationScope.test_neither_a_summary_nor_an_item_text_burns_a_number",
      "TestIdAllocationScope.test_a_bold_id_inside_an_item_text_is_not_an_allocation",
      "TestIdAllocationScope.test_a_high_id_quoted_in_prose_does_not_jump_the_counter",
      "TestIdAllocationScope.test_a_prose_id_on_a_legacy_x_line_burns_nothing_on_either_side",
      "TestIdAllocationScope.test_the_diagnostic_stops_reading_a_prose_mention_as_an_allocation"]),

    ("T088 the item's ID may sit anywhere on its line, not at the marker",
     'ITEM_ID_RE = re.compile("^" + MARKER + DECOR + ID_SLOT, re.M)',
     'ITEM_ID_RE = re.compile("^" + MARKER + r".*" + ID_SLOT, re.M)',
     ["TestIdAllocationScope.test_a_bold_id_inside_an_item_text_is_not_an_allocation"]),

    # the two over-NARROWING directions: a position rule that stops seeing a real
    # allocation hands out an ID already in use — the very failure the whole-file
    # scan existed to prevent, and no test above can see it
    ("T088 open items stop counting as allocations",
     "    return max(ids_at(open_items, ITEM_ID_RE) | done_log_ids(memdir), default=0)",
     "    return max(done_log_ids(memdir), default=0)",
     ["TestIdAllocationScope.test_an_open_item_still_blocks_reuse_of_its_id"]),

    ("T088 done-log entries stop counting as allocations",
     'LOG_ID_RE = re.compile("^" + LOG_LINE + r"\\S+ — T([0-9]{3,})\\b", re.M)',
     'LOG_ID_RE = re.compile(r"(?!x)()x()")',
     ["TestIdAllocationScope.test_a_done_log_entry_still_blocks_reuse_of_its_id",
      "TestMissingItemMessage.test_a_genuinely_closed_id_is_still_recognised"]),

    ("T088 a legacy [x] line moved verbatim by migrate stops counting",
     "    return ids_at(read(os.path.join(memdir, \"done-log.md\")) or \"\", "
     "LOG_ID_RE, ITEM_ID_RE)",
     "    return ids_at(read(os.path.join(memdir, \"done-log.md\")) or \"\", LOG_ID_RE)",
     ["TestIdAllocationScope.test_a_legacy_x_line_moved_by_migrate_still_blocks_reuse"]),

    # --- review#4: the same LINE must answer the same before and after migrate ---

    ("review#4 the legacy [x] line goes back to a tolerant mid-line match",
     'ITEM_ID_RE = re.compile("^" + MARKER + DECOR + ID_SLOT, re.M)',
     'ITEM_ID_RE = re.compile("^" + MARKER + r".*?" + ID_SLOT, re.M)',
     ["TestIdAllocationScope.test_a_prose_id_on_a_legacy_x_line_burns_nothing_on_either_side"]),

    ("review#4 the ID slot stops requiring the bold",
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3,})(?:~~)?\\*\\*"',
     'ID_SLOT = r"\\*?\\*?(?:~~)?T([0-9]{3,})(?:~~)?\\*?\\*?"',
     ["TestIdAllocationScope.test_a_plain_t_number_at_the_head_is_not_the_item_s_id"]),

    # --- review#5: DECORATION before the ID, and the ID's own wrapping -------
    # The slot tolerated exactly ONE decoration (`~~`), so every other one made a
    # real allocation invisible — measured on a live queue, which carries
    # `- [x] ✅ **T020** — ...` today, and in isolation walked the counter
    # BACKWARDS against the pre-position-rule code (max_id 50 → 3).

    ("review#5 nothing may sit between the box and the bold (the emoji ghost)",
     'ITEM_ID_RE = re.compile("^" + MARKER + DECOR + ID_SLOT, re.M)',
     'ITEM_ID_RE = re.compile("^" + MARKER + ID_SLOT, re.M)',
     ["TestIdAllocationScope.test_decoration_before_the_id_is_still_an_allocation",
      "TestIdAllocationScope.test_decoration_before_the_id_counts_in_next_steps_too",
      "TestIdAllocationScope.test_decoration_counts_and_prose_does_not_in_the_same_file",
      "TestIdAllocationScope.test_a_struck_through_legacy_id_is_spent_on_either_side"]),

    ("review#5 the strikethrough INSIDE the bold stops counting (`**~~T012~~**`)",
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3,})(?:~~)?\\*\\*"',
     'ID_SLOT = r"\\*\\*T([0-9]{3,})\\*\\*"',
     ["TestIdAllocationScope."
      "test_a_bold_wrapped_strikethrough_id_is_spent_and_leaves_no_fragment"]),

    # the over-WIDENING direction, which no test above can see: a decoration slot
    # that admits words is the whole-file scan again, one line at a time
    ("review#5 DECOR admits words, so prose before the ID allocates again",
     'DECOR = r"[^\\w\\n]{0,%d}" % DECOR_MAX',
     'DECOR = r"[^\\n]{0,%d}" % (DECOR_MAX * 20)',
     ["TestIdAllocationScope."
      "test_a_prose_id_on_a_legacy_x_line_burns_nothing_on_either_side",
      "TestIdAllocationScope.test_decoration_counts_and_prose_does_not_in_the_same_file"]),

    ("review#5 the ID slot goes back to being read for one file only (box-aware)",
     'ITEM_ID_RE = re.compile("^" + MARKER + DECOR + ID_SLOT, re.M)',
     'ITEM_ID_RE = re.compile("^" + r"- \\[(x)\\] " + DECOR + ID_SLOT, re.M)',
     ["TestIdAllocationScope.test_an_open_box_parked_in_the_done_log_is_still_spent"]),

    # --- review#5: the ANCHOR and the WIDTH of both grammars -----------------

    ("review#5 the item marker stops being anchored to start of line",
     'ITEM_ID_RE = re.compile("^" + MARKER + DECOR + ID_SLOT, re.M)',
     'ITEM_ID_RE = re.compile(MARKER + DECOR + ID_SLOT, re.M)',
     ["TestIdAllocationScope."
      "test_the_marker_form_quoted_inside_an_item_text_is_not_an_allocation"]),

    ("review#5 the done-log line stops being anchored to start of line",
     'LOG_ID_RE = re.compile("^" + LOG_LINE + r"\\S+ — T([0-9]{3,})\\b", re.M)',
     'LOG_ID_RE = re.compile(LOG_LINE + r"\\S+ — T([0-9]{3,})\\b", re.M)',
     ["TestDoneLogLineGrammar.test_a_log_line_format_quoted_in_an_outcome_is_not_a_close"]),

    # ONE entry, because there is now ONE spelling: ID_RE is built from ID_SLOT,
    # so the same loosening reaches the allocator AND item_title. Spelled twice,
    # they were two mutants and could drift apart
    ("review#5 the ID width loosens to `+` (a bold `T7` becomes an id)",
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3,})(?:~~)?\\*\\*"',
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]+)(?:~~)?\\*\\*"',
     ["TestIdAllocationScope."
      "test_a_two_digit_bold_number_is_no_id_at_the_marker_nor_in_a_title"]),

    ("review#5 the done-log ID column loosens to `+`",
     'LOG_ID_RE = re.compile("^" + LOG_LINE + r"\\S+ — T([0-9]{3,})\\b", re.M)',
     'LOG_ID_RE = re.compile("^" + LOG_LINE + r"\\S+ — T([0-9]+)\\b", re.M)',
     ["TestDoneLogLineGrammar.test_a_two_digit_number_in_the_id_column_is_no_id"]),

    ("review#5 the closing bold becomes optional (an unclosed head gets an id)",
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3,})(?:~~)?\\*\\*"',
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3,})(?:~~)?(?:\\*\\*)?"',
     ["TestIdAllocationScope.test_an_unclosed_bold_carries_no_id"]),

    ("review#5 report respells the log line with \\d (Unicode digits sneak in)",
     '    entry = re.compile("^" + LOG_LINE + r".*(?:\\n  .*)*", re.M)',
     '    entry = re.compile(r"^- (\\d{4}-\\d{2}-\\d{2}) — .*(?:\\n  .*)*", re.M)',
     ["TestDoneLogLineGrammar.test_report_reads_the_date_column_in_ascii_digits_only"]),

    ("review#5 cmd_edit respells the canonical head instead of building it",
     "        head_m = CANONICAL_HEAD_RE.match(block)",
     '        head_m = re.match(r"- \\[ \\] \\*\\*T[0-9]{3,}\\*\\* — ", block)',
     ["TestCanonicalHead.test_a_decorated_head_is_still_editable"]),

    ("review#4 the done-log ID column only counts a FEITO close",
     'LOG_ID_RE = re.compile("^" + LOG_LINE + r"\\S+ — T([0-9]{3,})\\b", re.M)',
     'LOG_ID_RE = re.compile("^" + LOG_LINE + r"FEITO — T([0-9]{3,})\\b", re.M)',
     ["TestIdAllocationScope.test_a_cancelled_item_still_blocks_reuse_of_its_id"]),

    ("review#4 item_id goes back to searching the block's whole text",
     "    m = ITEM_ID_RE.match(text)\n"
     "    return int(m.group(2)) if m else None",
     "    m = ID_RE.search(text)\n"
     "    return int(m.group(1)) if m else None",
     ["TestIdAllocationScope.test_an_idless_item_quoting_a_bold_id_is_still_idless"]),


    ("T070 add writes a Risk line for the reserved word again",
     "    if args.risk and not clears_field(args.risk):", "    if args.risk:",
     ["TestRiskDeletion.test_add_writes_no_risk_line_for_the_reserved_word"]),

    ("T070 edit SETS Risk to the reserved word instead of deleting the field",
     '        if field in CLEARABLE and clears_field(flag):', "        if False:",
     ["TestRiskDeletion.test_edit_clears_the_risk_field",
      "TestRiskDeletion.test_the_surrounding_fields_survive_intact",
      "TestRiskDeletion.test_clearing_an_item_that_has_no_risk_is_a_no_op",
      "TestRiskDeletion.test_clearing_rewrites_the_real_field_not_prose_that_looks_like_one"]),

    ("T070 the reserved word stops tolerating case and surrounding blanks",
     '    return (value or "").strip().lower() == FIELD_CLEAR',
     '    return (value or "") == FIELD_CLEAR',
     ["TestRiskDeletion.test_the_reserved_word_is_case_and_space_tolerant"]),

    # the opposite direction: a clear-word that over-triggers makes Risk unwritable
    # rather than merely clearable, and only the false-positive test sees it
    ("T070 the reserved word swallows every Risk value",
     '    return (value or "").strip().lower() == FIELD_CLEAR',
     "    return bool(value)",
     ["TestRiskDeletion.test_a_real_risk_is_still_written_and_still_replaceable"]),

    ("T070 clearing leaves the separator blank dangling at end of line",
     "        if i == len(self.fields):", "        if False:",
     ["TestRiskDeletion.test_no_trailing_blank_is_left_when_risk_was_the_last_field"]),

    # the same repair in the other direction: too WIDE instead of absent
    ("review#2 the blank repair sweeps the whole block again, eating a hard break",
     "    item = parse_item(block)\n"
     "    item.drop_field(item.field_at(segment.start()))\n"
     "    return render_item(item)",
     "    item = parse_item(block)\n"
     "    item.fields.remove(item.field_at(segment.start()))\n"
     '    return re.sub(r"[ \\t]+(?=\\n|\\Z)", "", render_item(item))',
     ["TestRiskDeletion.test_a_hard_break_elsewhere_in_the_block_survives"]),

    # the block-ceiling exemption (T071) is only safe because the field ceiling
    # bounds what a field edit can write — without it, the exemption IS the bypass
    ("review#1 edit stops measuring field values (the reported bypass)",
     "    check_field_ceilings(args.force, effort=args.effort, risk=args.risk,\n"
     "                         criterion=args.criterion, project=args.project,\n"
     "                         deferred=args.deferred)",
     "    pass",
     # NOT test_the_bypass_cannot_push_the_item_past_the_block_ceiling: now that the
     # block rule covers the free-text fields, a 910-char --criterion is refused by
     # the BLOCK ceiling even with this guard off. Listing it claimed a proof the run
     # could not make — and it showed up as a SURVIVOR the first time it ran
     ["TestCeilingScope.test_a_field_value_over_its_ceiling_is_refused"]),

    ("review#1 add stops measuring field values",
     "    check_field_ceilings(args.force, effort=args.effort, risk=args.risk,\n"
     "                         criterion=args.criterion, project=args.project, "
     "source=args.source,\n"
     "                         deferred=args.deferred, repo=args.repo)",
     "    pass",
     ["TestCeilingScope.test_add_measures_field_values_too"]),

    ("T072 a mutating command stops naming the queue it writes",
     '        print(f"tk-queue: queue: {memdir}", file=sys.stderr)', "        pass",
     ["TestTargetQueueAnnounced.test_every_mutating_command_names_the_memdir_on_stderr",
      "TestTargetQueueAnnounced.test_the_announced_dir_is_the_one_actually_written"]),

    ("T072 the announcement lands on stdout, where callers parse the output",
     '        print(f"tk-queue: queue: {memdir}", file=sys.stderr)',
     '        print(f"tk-queue: queue: {memdir}")',
     ["TestTargetQueueAnnounced.test_it_goes_to_stderr_and_never_pollutes_stdout"]),

    ("T072 a reader takes the write lock too",
     'READERS = frozenset(("list", "report", "pack"))', "READERS = frozenset()",
     ["TestTargetQueueAnnounced."
      "test_the_readers_of_one_queue_name_it_too_and_report_stays_silent"]),

    ("T215 the readers of one queue go back to naming nothing",
     '    memdir = None if args.cmd == "report" else memory_dir(args.dir)',
     "    memdir = None if args.cmd in READERS else memory_dir(args.dir)",
     ["TestTargetQueueAnnounced."
      "test_the_readers_of_one_queue_name_it_too_and_report_stays_silent"]),

    # over-trigger direction: `report` sweeps every project's queue, so a single
    # dir named on it is a queue it does not read
    ("T215 report announces one queue out of the many it sweeps",
     '    memdir = None if args.cmd == "report" else memory_dir(args.dir)',
     "    memdir = memory_dir(args.dir)",
     ["TestTargetQueueAnnounced."
      "test_the_readers_of_one_queue_name_it_too_and_report_stays_silent"]),
    # --- review#2: the real field is the one in the CHAIN ------------------

    ("review#2 the real field is the LAST marker in the block again (note eaten)",
     "        found = real_fields(new, field)",
     '        found = list(re.finditer(r"\\*\\*(?:" + FIELD_VARIANTS[field] + '
     'r"):\\*\\*[^*\\n]*", new))[-1:]',
     ["TestFieldChain.test_clearing_hits_the_real_field_and_spares_the_note",
      "TestFieldChain.test_setting_hits_the_real_field_and_spares_the_note"]),

    ("T065/review#2 the real field is the FIRST marker in the block again (prose eaten)",
     "        found = real_fields(new, field)",
     '        found = list(re.finditer(r"\\*\\*(?:" + FIELD_VARIANTS[field] + '
     'r"):\\*\\*[^*\\n]*", new))[:1]',
     ["TestEmbeddedMarker.test_edit_rewrites_the_real_field_not_prose_that_looks_like_one",
      "TestFieldChain.test_a_marker_before_the_fields_is_still_prose",
      "TestRiskDeletion.test_clearing_rewrites_the_real_field_not_prose_that_looks_like_one"]),

    ("review#2 the chain admits prose (the period discriminator goes away)",
     '        ends_field = (line[seg[1]:seg[2]].rstrip().endswith(".")\n'
     '                      or canonical_field(seg[0]) == "Source")',
     "        ends_field = True",
     ["TestEmbeddedMarker.test_edit_rewrites_the_real_field_not_prose_that_looks_like_one",
      "TestFieldChain.test_a_marker_before_the_fields_is_still_prose"]),

    ("review#2 the chain stops at Source (fields appended after it become unreachable)",
     '                      or canonical_field(seg[0]) == "Source")',
     "                      or False)",
     ["TestFieldChain.test_a_field_appended_after_source_stays_editable"]),

    ("review#2 a marker only outside the chain is silently written instead of refused",
     '        if not found and re.search(r"\\*\\*(?:" + FIELD_VARIANTS[field] + '
     'r"):\\*\\*", new):',
     "        if False:",
     ["TestFieldChain.test_a_marker_only_outside_the_chain_is_refused_not_guessed"]),

    # over-refusal, the direction the tests above cannot see: a guard that fires on
    # every edit makes the fields unwritable instead of merely un-guessable
    ("review#2 the outside-the-chain guard fires on every edit",
     "        if not found and re.search(",
     "        if re.search(",
     ["TestRiskDeletion.test_a_real_risk_is_still_written_and_still_replaceable"]),

    ("review#2 a duplicated field in the chain is guessed instead of refused",
     "        if len(in_chain) > 1:", "        if False:",
     ["TestFieldChain.test_an_ambiguous_chain_is_refused_not_guessed"]),

    # --- review#2: which flags the BLOCK ceiling covers --------------------

    ("T071 the block ceiling gates a SHORT field edit again",
     "    if any(getattr(args, f, None) for f in FREE_TEXT_FLAGS) and len(new) > len(block):",
     "    if len(new) > len(block):",
     ["TestCeilingScope.test_every_short_field_edit_passes_without_force"]),

    ("review#2 the block ceiling stops covering the free-text fields (combining bypass)",
     "    if any(getattr(args, f, None) for f in FREE_TEXT_FLAGS) and len(new) > len(block):",
     "    if args.text and len(new) > len(block):",
     ["TestCeilingScope.test_combining_free_text_fields_cannot_cross_the_block_ceiling",
      "TestCeilingScope.test_repeated_field_edits_cannot_grow_the_item_without_limit",
      "TestCeilingScope.test_a_free_text_field_edit_is_measured_against_the_block"]),

    ("T071 a --text edit stops being measured against the block ceiling",
     "    if any(getattr(args, f, None) for f in FREE_TEXT_FLAGS) and len(new) > len(block):",
     "    if False:",
     ["TestCeilingScope.test_a_text_edit_over_the_ceiling_is_still_refused",
      "TestCeilingScope.test_a_text_edit_growing_an_already_oversized_item_is_refused"]),

    # --- the field ceiling, restructured by nature ------------------------

    ("review#1 the field ceiling over-triggers, refusing every value",
     "        if len(val) > limit:", "        if val:",
     ["TestCeilingScope.test_a_field_value_under_its_ceiling_still_passes",
      "TestCloseFieldCeilings.test_force_raises_it_and_an_ordinary_close_is_untouched"]),

    ("review#2 the short/prose split collapses (short fields get the prose ceiling)",
     "        if name in SHORT_FLAGS:", "        if False:",
     ["TestCeilingScope.test_a_field_value_over_its_ceiling_is_refused"]),

    ("review#1 --force stops raising the field ceiling",
     "            limit, forced = (FIELD_CEILING_FORCED if force\n"
     "                             else FIELD_CEILING), FIELD_CEILING_FORCED",
     "            limit, forced = FIELD_CEILING, FIELD_CEILING_FORCED",
     ["TestCeilingScope.test_force_raises_the_field_ceiling",
      "TestCloseFieldCeilings.test_force_raises_it_and_an_ordinary_close_is_untouched"]),

    # --- review#3: the close flags -----------------------------------------

    ("review#3 done/cancel stop measuring their flags",
     "    check_field_ceilings(args.force, **{marker_flag: outcome},\n"
     "                         summary=args.summary, note=args.note)",
     "    pass",
     ["TestCloseFieldCeilings.test_done_measures_how_summary_and_note",
      "TestCloseFieldCeilings.test_cancel_measures_why"]),

    # --- T119: the DECISION class may not be reached by omission ------------

    ("T119 add stops demanding a deferral for the DECISION class",
     "    if args.classe == DEFERRABLE_CLASS and (args.deferred is None or "
     "clears_field(args.deferred)):\n        fail(deferral_gate_message(\"add\"))",
     "    pass",
     ["TestDecisionDeferralGate."
      "test_add_decision_without_a_deferral_is_refused_and_names_both_paths",
      "TestDecisionDeferralGate.test_the_reserved_clear_word_is_no_justification_either"]),

    ("T119 the reserved clear word passes as a justification (a fieldless DECISION)",
     "    if args.classe == DEFERRABLE_CLASS and (args.deferred is None or "
     "clears_field(args.deferred)):",
     "    if args.classe == DEFERRABLE_CLASS and args.deferred is None:",
     ["TestDecisionDeferralGate.test_the_reserved_clear_word_is_no_justification_either"]),

    # over-trigger: a gate that fires on every class stops the queue rather than
    # the silent deferral, and only the false-positive test sees it
    ("T119 the gate fires on every class, not just DECISION",
     "    if args.classe == DEFERRABLE_CLASS and (args.deferred is None or "
     "clears_field(args.deferred)):",
     "    if args.deferred is None or clears_field(args.deferred):",
     ["TestDecisionDeferralGate.test_the_other_classes_are_untouched_by_the_gate"]),

    ("T119 an empty justification satisfies the flag again",
     "    if args.deferred is not None:\n"
     "        # the flag was typed: an empty justification is a deferral nobody can read,\n"
     "        # and argparse's own check only proves the flag was there\n"
     "        ensure_filled(deferred=args.deferred)",
     "    pass",
     ["TestDecisionDeferralGate.test_the_justification_may_not_be_blank"]),

    ("T119 add accepts a deferral on a class that is not DECISION",
     "    if args.deferred is not None and args.classe != DEFERRABLE_CLASS:",
     "    if False:",
     ["TestDecisionDeferralGate.test_a_deferral_without_the_decision_class_is_refused"]),

    ("T119 the deferral never reaches the item",
     '    if args.deferred and not clears_field(args.deferred):\n'
     '        fields.append(f"**Deferred:** {args.deferred}.")',
     "    pass",
     ["TestDecisionDeferralGate.test_a_deferral_reaches_the_item"]),

    ("T119 edit stops gating the change to DECISION (the two-command bypass)",
     "    if args.classe == DEFERRABLE_CLASS and not (setting or (has and not clearing)):\n"
     '        fail(deferral_gate_message("edit"))',
     "    pass",
     ["TestDecisionDeferralGate.test_edit_to_decision_passes_the_same_gate"]),

    ("T119 edit's gate stops seeing the deferral already on the item",
     "    has = seg is not None", "    has = False",
     ["TestDecisionDeferralGate.test_a_deferral_already_on_the_item_satisfies_the_gate"]),

    # over-trigger on edit: a gate on the item's CURRENT class makes every legacy
    # DECISION item uneditable — the direction no bypass test can see
    ("T119 edit's gate fires on the item's class, not on the change to it",
     "    if args.classe == DEFERRABLE_CLASS and not (setting or (has and not clearing)):",
     "    if result_class == DEFERRABLE_CLASS and not (setting or (has and not clearing)):",
     ["TestDecisionDeferralGate.test_a_legacy_decision_item_stays_editable"]),

    ("T119 the deferral can be cleared while the class stays DECISION",
     "    if clearing and result_class == DEFERRABLE_CLASS:",
     "    if False:",
     ["TestDecisionDeferralGate."
      "test_the_deferral_cannot_be_dropped_while_the_item_stays_a_decision"]),

    ("T119 a deferral survives the class that justified it (the stale field)",
     "    if args.deferred is None and args.classe and args.classe != DEFERRABLE_CLASS "
     "and has:",
     "    if False:",
     ["TestDecisionDeferralGate.test_leaving_the_decision_class_takes_the_deferral_with_it"]),

    ("T119 Deferred stops being clearable, so leaving the class WRITES 'none'",
     'CLEARABLE = frozenset(("Risk", "Deferred", "Env", "Blocked-by"))',
     'CLEARABLE = frozenset(("Risk", "Env", "Blocked-by"))',
     ["TestDecisionDeferralGate.test_leaving_the_decision_class_takes_the_deferral_with_it"]),

    ("T119 add stops measuring the justification against the field ceiling",
     "                         criterion=args.criterion, project=args.project, "
     "source=args.source,\n"
     "                         deferred=args.deferred, repo=args.repo)",
     "                         criterion=args.criterion, project=args.project, "
     "source=args.source, repo=args.repo)",
     ["TestDecisionDeferralGate.test_the_justification_is_measured_against_the_field_ceiling"]),

    ("T119 edit stops measuring the justification against the field ceiling",
     "                         criterion=args.criterion, project=args.project,\n"
     "                         deferred=args.deferred)",
     "                         criterion=args.criterion, project=args.project)",
     ["TestDecisionDeferralGate.test_the_justification_is_measured_against_the_field_ceiling"]),

    # --- T119: priority is the file's order, and `bump` is how it moves ------

    ("T119 bump appends at the end instead of the top",
     "    at = dest.start() if dest else len(without)", "    at = len(without)",
     ["TestBump.test_bump_moves_the_item_to_the_top_and_list_follows",
      "TestBump.test_the_other_items_keep_their_relative_order"]),

    ("T119 bump copies the item instead of moving it",
     "    without = excise(content, block, start)", "    without = content",
     ["TestBump.test_the_item_is_moved_whole_and_not_duplicated"]),

    ("T119 bumping the top item rewrites the file anyway",
     "    if first and first.start() == start:", "    if False:",
     ["TestBump.test_bumping_the_top_item_leaves_the_file_byte_identical"]),

    ("T119 edit accepts a deferral on an item that is not a DECISION",
     "    if setting and result_class != DEFERRABLE_CLASS:", "    if False:",
     ["TestDecisionDeferralGate."
      "test_edit_refuses_a_deferral_on_an_item_that_is_not_a_decision"]),

    ("T119 the typo'd class reaches the deferral gate before it is validated",
     "    if args.classe and args.classe not in CLASSES:\n"
     "        fail(f\"--class must be one of {', '.join(CLASSES)}\")\n"
     "    deferred_flag = deferral_for_edit(args, block)",
     "    deferred_flag = deferral_for_edit(args, block)",
     ["TestDecisionDeferralGate.test_a_typo_in_the_class_is_answered_before_the_gate"]),

    ("T119 bump lands above the frontmatter instead of above the first item",
     "    at = dest.start() if dest else len(without)", "    at = 0",
     ["TestBump.test_the_whole_file_comes_out_exactly_as_the_move_implies"]),

    ("T119 bump glues the moved item to the one it now precedes",
     '    moved = block if block.endswith("\\n\\n") or not tail else block + "\\n"',
     "    moved = block",
     ["TestBump.test_the_whole_file_comes_out_exactly_as_the_move_implies"]),

    ("T119 bump acts without checking the item is really open",
     "    content, block, start = find_open_item(memdir, args.id)\n"
     "    label = item_label(block)\n"
     '    path = os.path.join(memdir, "next-steps.md")',
     '    path = os.path.join(memdir, "next-steps.md")\n'
     "    content = read(path) or \"\"\n"
     '    block, start = next(((t, 0) for k, t in split_blocks(content)\n'
     '                         if k == "item-open" and item_id(t) == args.id), ("", 0))\n'
     "    label = item_label(block)",
     ["TestBump.test_an_unknown_id_is_diagnosed_and_nothing_moves"]),

    ("T119 list orders its groups alphabetically, so a bump is invisible",
     "                           by_position=True)",
     "                           )",
     ["TestBump.test_a_bump_shows_in_list_on_a_tagged_queue_too"]),

    # the announcement used to be this mutation's observable; since T215 every
    # command but `report` names its queue, reader or not, so the LOCK is what
    # tells the two sides apart and the test that watches it is the proof
    ("T119 bump counts as a reader, so it takes no lock",
     'READERS = frozenset(("list", "report", "pack"))',
     'READERS = frozenset(("list", "report", "pack", "bump"))',
     ["TestConcurrency.test_bump_waits_for_the_lock_like_every_other_writer"]),

    # --- 2nd pair of eyes: the free-text guards, ON THE NEW FLAG --------------
    # Wiring `deferred=` into a generic checker is not proof that the checker sees
    # it: each kwarg below was dropped on its own, and the whole suite stayed green.

    ("2ª review add stops measuring the justification for newlines",
     "    ensure_single_line(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                       criterion=args.criterion, source=args.source, "
     "project=args.project,\n"
     "                       deferred=args.deferred)",
     "    ensure_single_line(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                       criterion=args.criterion, source=args.source, "
     "project=args.project)",
     ["TestDecisionDeferralGate."
      "test_the_justification_goes_through_the_free_text_guards_on_add"]),

    ("2ª review add stops refusing a field marker inside the justification",
     "                              criterion=args.criterion, source=args.source,\n"
     "                              deferred=args.deferred)",
     "                              criterion=args.criterion, source=args.source)",
     ["TestDecisionDeferralGate."
      "test_the_justification_goes_through_the_free_text_guards_on_add"]),

    ("2ª review edit stops refusing a blank justification",
     "    if args.deferred is not None:\n        ensure_filled(deferred=args.deferred)",
     "    pass",
     ["TestDecisionDeferralGate."
      "test_the_justification_goes_through_the_free_text_guards_on_edit"]),

    ("2ª review edit stops measuring the justification for newlines and markers",
     "    ensure_no_embedded_marker(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                              criterion=args.criterion, deferred=args.deferred)",
     "    ensure_no_embedded_marker(text=args.text, effort=args.effort, risk=args.risk,\n"
     "                              criterion=args.criterion)",
     ["TestDecisionDeferralGate."
      "test_the_justification_goes_through_the_free_text_guards_on_edit"]),

    # --- 2nd pair of eyes: prose absorbed into the field chain ---------------

    # one position rule, two gates: prose absorbed into the chain satisfies the
    # deferral gate in one direction and gets DELETED by `release` in the other
    ("2ª review a field anywhere in the chain counts, so prose satisfies the gate",
     '    return [m for i, m in enumerate(chain) if names[i] == field and i >= lo]',
     '    return [m for i, m in enumerate(chain) if names[i] == field]',
     ["TestDecisionDeferralGate."
      "test_prose_that_looks_like_a_deferral_never_satisfies_the_gate",
      "TestClaim.test_prose_ending_in_a_period_before_the_fields_is_not_a_claim"]),

    ("2ª review the stray marker is ignored instead of refused (prose gets deleted)",
     "    if stray and (args.classe or args.deferred is not None):", "    if False:",
     ["TestDecisionDeferralGate."
      "test_prose_that_looks_like_a_deferral_never_satisfies_the_gate"]),

    # the over-refusal direction: a guard that fires on every edit of such an item
    # makes it uneditable, which is worse than the shape it protects against
    ("2ª review the stray guard fires even when the edit never touches the deferral",
     "    if stray and (args.classe or args.deferred is not None):", "    if stray:",
     ["TestDecisionDeferralGate.test_an_edit_that_never_consults_the_deferral_stays_allowed"]),

    # --- T121: `list` reads the class from the chain, like the gate ----------

    ("T121 `list` reads the class from the whole block again (prose beats the field)",
     '    if real_fields(block, "Class"):\n        return chain_class(block)',
     '    if False:\n        return chain_class(block)',
     ["TestListReadsTheClassFromTheChain."
      "test_a_class_named_only_in_PROSE_is_not_the_one_list_shows",
      "TestListReadsTheClassFromTheChain."
      "test_list_and_pack_no_longer_disagree_about_the_same_item",
      "TestListReadsTheClassFromTheChain."
      "test_a_class_the_GATE_calls_ambiguous_is_shown_as_unknown_not_guessed"]),

    # the over-correction direction, and the one a naive fix takes: reading the
    # chain ALONE shows every unfolded legacy item with no class at all
    ("T121 `list` reads the chain ALONE, so a legacy item loses its class",
     '    if real_fields(block, "Class"):\n'
     '        return chain_class(block)\n'
     '    return marker_value(block, "Class", CLASS_VALUE_RE)',
     "    return chain_class(block)",
     ["TestListReadsTheClassFromTheChain."
      "test_a_legacy_item_with_its_fields_OFF_the_first_line_still_shows_its_class"]),

    # --- T121: prose wearing a real field's NAME -----------------------------

    # the locator goes back to reading the chain RAW, which is what `edit` did
    # before: a segment the item's own sentence opens is written, or deleted
    ("T121 the edit locator reads the chain raw again (quoted prose eaten)",
     "        found = real_fields(new, field)", "        found = in_chain",
     ["TestProseWearingAFieldName.test_setting_a_field_named_only_in_prose_is_refused",
      "TestProseWearingAFieldName.test_CLEARING_a_field_named_only_in_prose_is_refused"]),

    # the off-by-one in the other direction: Class anchors the chain AT its own
    # segment, so treating it like every other field locks `--class` out of every
    # canonical item — the over-refusal this rule must not buy
    ("T121 the anchor excludes the **Class:** it is anchored on",
     '    lo = names.index("Class") + (0 if field == "Class" else 1)',
     '    lo = names.index("Class") + 1',
     ["TestProseWearingAFieldName."
      "test_the_anchor_does_not_move_the_fields_of_an_ordinary_item"]),

    # the ambiguity COUNT is deliberately not positional: an item that quotes the
    # marker AND carries the real field is refused, not silently resolved
    ("T121 the ambiguity count becomes positional (a quoted marker stops counting)",
     "        if len(in_chain) > 1:", "        if len(found) > 1:",
     ["TestFieldChain.test_an_ambiguous_chain_is_refused_not_guessed"]),

    # --- 2nd pair of eyes: an item's TEXT is not its ADDRESS ------------------

    ("2ª review the block is addressed by its TEXT again (a quoted copy wins)",
     "    return content, found[0][0], found[0][1]",
     "    return content, found[0][0], content.index(found[0][0])",
     ["TestBlockAddressing.test_done_closes_the_real_item_and_spares_the_quoted_copy",
      "TestBlockAddressing.test_bump_moves_the_real_item_and_leaves_no_phantom",
      "TestBlockAddressing.test_edit_rewrites_the_real_item_and_not_the_quotation"]),

    # --- re-check of the FIX: the corruption the fix itself shipped -----------

    # the shadow can no longer live INSIDE clear_field_segment (its offsets are
    # local names), so the defect is put back where it still can: the call site
    ("re-check the clearing branch shadows the item's offset in the FILE",
     "            if found:\n"
     "                new = clear_field_segment(new, found[0])",
     "            if found:\n"
     "                start, end = found[0].span()\n"
     "                new = clear_field_segment(new, found[0])",
     ["TestClearingKeepsTheFileIntact.test_clearing_a_risk_rewrites_only_that_field",
      "TestClearingKeepsTheFileIntact.test_clearing_a_deferral_rewrites_only_that_field"]),

    ("re-check the gate reads the class the loose way `list` displays it",
     "    result_class = args.classe or chain_class(block)",
     '    result_class = args.classe or marker_value(block, "Class", CLASS_VALUE_RE)',
     ["TestDecisionDeferralGate.test_a_class_named_only_in_prose_does_not_open_the_gate"]),

    ("re-check an ambiguous class in the chain is guessed instead of refused",
     "    if len(found) != 1:\n        return None",
     "    if not found:\n        return None",
     ["TestDecisionDeferralGate.test_a_class_named_only_in_prose_does_not_open_the_gate"]),

    # the rule now lives in real_fields, where the WRITER reads it too — which is
    # the review#3 finding: the gates applied it and `edit` did not
    # the OLD body, verbatim, not `if False` — with the early return merely
    # switched off, `names.index("Class")` raises on the very population the
    # mutation is about, and a command that CRASHES exits 1 like the refusal
    # does: the deferral test then passed and reported this guard as protected
    ("review#3 a chain with no **Class:** anchors the whole chain again (prose eaten)",
     '    if "Class" not in names:\n        return []\n'
     '    lo = names.index("Class") + (0 if field == "Class" else 1)',
     '    lo = 0\n'
     '    if "Class" in names:\n'
     '        lo = names.index("Class") + (0 if field == "Class" else 1)',
     ["TestDecisionDeferralGate.test_a_chain_with_no_class_carries_no_deferral_to_find",
      "TestAClassLessChainIsNotAField.test_setting_a_field_on_a_class_less_item_is_refused",
      "TestAClassLessChainIsNotAField.test_CLEARING_a_field_on_a_class_less_item_is_refused",
      "TestAClassLessChainIsNotAField."
      "test_a_field_the_class_less_item_really_carries_is_refused_too",
      "TestAClassLessChainIsNotAField."
      "test_the_refusal_does_not_offer_a_remedy_that_is_a_dead_end"]),

    # the message, on its own: the generic one sends the caller looking for a
    # **Class:** the item has not got
    # the anchor carries the fail() line under it, and that is not decoration: a
    # second guard with the SAME condition was added one branch to the right, and
    # this entry went UNRUNNABLE — proving nothing, silently — until each anchor
    # named the refusal it belongs to
    ("review#3 the class-less refusal borrows the generic message",
     '            if field != "Class" and not real_fields(new, "Class"):\n                fail(f"{label} names no **Class:** in its field chain, so nothing in that "',
     '            if False:\n                fail(f"{label} names no **Class:** in its field chain, so nothing in that "',
     ["TestAClassLessChainIsNotAField.test_setting_a_field_on_a_class_less_item_is_refused",
      "TestAClassLessChainIsNotAField.test_CLEARING_a_field_on_a_class_less_item_is_refused",
      "TestAClassLessChainIsNotAField."
      "test_a_field_the_class_less_item_really_carries_is_refused_too",
      "TestAClassLessChainIsNotAField."
      "test_the_refusal_does_not_offer_a_remedy_that_is_a_dead_end"]),

    # the over-refusal direction, and the one the old fallback was written for:
    # a field the item does not carry at all is APPENDED, and `--class` on a
    # class-less item is exactly that append
    ("review#3 a field the item does not carry at all is refused instead of appended",
     '        if not found and re.search(r"\\*\\*(?:" + FIELD_VARIANTS[field] + r"):\\*\\*", new):',
     "        if not found:",
     ["TestAClassLessChainIsNotAField.test_a_class_less_item_can_still_be_GIVEN_a_class"]),

    ("re-check the stray refusal drops its --deferred arm",
     "    if stray and (args.classe or args.deferred is not None):",
     "    if stray and args.classe:",
     ["TestDecisionDeferralGate.test_the_stray_refusal_fires_for_a_bare_deferred_too"]),

    # --- T120: the Env field, and the site file that says what an Env may be ---

    ("T120 an env outside the roster is accepted (the phantom environment)",
     "    if value not in site.environments:", "    if False:",
     ["TestEnvField.test_add_refuses_a_value_outside_the_roster",
      "TestEnvField.test_edit_refuses_it_too"]),

    ("T120 the roster match stops being exact about case",
     "    if value not in site.environments:",
     "    if value.lower() not in [e.lower() for e in site.environments]:",
     ["TestEnvField.test_a_case_difference_is_a_different_name"]),

    ("T120 the roster match loosens to a prefix",
     "    if value not in site.environments:",
     "    if not any(e.startswith(value) for e in site.environments):",
     ["TestEnvField.test_a_prefix_of_a_roster_name_is_not_that_name"]),

    ("T120 a missing site file stops refusing the flag",
     '    if site is None:\n        fail("--env: " + tk_site.missing_file_message())',
     "    if site is None:\n        return",
     ["TestEnvField.test_no_site_file_refuses_the_flag_and_says_what_to_create"]),

    # the over-refusal direction: DELETING the field names no environment, so a
    # machine with no site file at all must still be able to un-pin an item
    ("T120 the reserved clear word is validated against the roster too",
     "    if value is None or clears_field(value):\n        return",
     "    if value is None:\n        return",
     ["TestEnvField.test_clearing_needs_no_site_file_at_all",
      "TestEnvField.test_add_writes_no_field_for_the_reserved_word"]),

    ("T120 add stops validating the env",
     '    validate_env(args.env)\n    # the gate HANDS BACK',
     "    # the gate HANDS BACK",
     ["TestEnvField.test_add_refuses_a_value_outside_the_roster"]),

    ("T120 edit stops validating the env",
     "    validate_env(args.env)\n    # before the deferral gate",
     "    # before the deferral gate",
     ["TestEnvField.test_edit_refuses_it_too"]),

    ("T120 add writes an Env line for the reserved clear word",
     "    if args.env and not clears_field(args.env):", "    if args.env:",
     ["TestEnvField.test_add_writes_no_field_for_the_reserved_word"]),

    ("T120 the field moves out of the position the package filter reads",
     ['    if args.env and not clears_field(args.env):\n'
      '        fields.append(f"**Env:** {args.env}.")\n'
      '    # the third field',
      '    fields.append(f"**Criterion:** {args.criterion}.")'],
     ['    # the third field',
      '    fields.append(f"**Criterion:** {args.criterion}.")\n'
      '    if args.env and not clears_field(args.env):\n'
      '        fields.append(f"**Env:** {args.env}.")'],
     ["TestEnvField.test_add_writes_the_field_where_the_readers_look_for_it"]),

    # the neighbouring gate field, which the assertion above only sees because the
    # test passes --risk too: with it omitted the two could swap and nothing fell
    ("T120 Env and Risk swap places in the composed item",
     '    if args.risk and not clears_field(args.risk):\n'
     '        fields.append(f"**Risk:** {args.risk}.")\n'
     '    # beside Risk: the two fields that decide whether this item can be picked up\n'
     '    # unattended, and where. Absent = it runs wherever the queue lives\n'
     '    if args.env and not clears_field(args.env):\n'
     '        fields.append(f"**Env:** {args.env}.")',
     '    if args.env and not clears_field(args.env):\n'
     '        fields.append(f"**Env:** {args.env}.")\n'
     '    if args.risk and not clears_field(args.risk):\n'
     '        fields.append(f"**Risk:** {args.risk}.")',
     ["TestEnvField.test_add_writes_the_field_where_the_readers_look_for_it"]),

    ("T120 site a missing file is read as a defective one instead of as absent",
     "    if not os.path.exists(path):\n        return None", "    if False:\n        return None",
     ["TestEnvField.test_no_site_file_refuses_the_flag_and_says_what_to_create"],
     "bin/tk_site.py"),

    ("T120 Env stops being a field the readers know (it leaves FIELD_VARIANTS)",
     '    "Env": r"(?:Env|Ambiente)",', '    "Env": r"(?!x)x",',
     ["TestEnvField.test_edit_sets_the_field_and_then_REPLACES_it",
      "TestEnvField.test_a_marker_only_outside_the_chain_is_refused_not_guessed"]),

    ("T120 Env stops being clearable (the stale pin nobody can remove)",
     'CLEARABLE = frozenset(("Risk", "Deferred", "Env", "Blocked-by"))',
     'CLEARABLE = frozenset(("Risk", "Deferred", "Blocked-by"))',
     ["TestEnvField.test_the_reserved_word_clears_the_field_and_leaves_the_file_intact",
      "TestEnvField.test_clearing_needs_no_site_file_at_all"]),

    ("T120 edit stops writing the field at all",
     "             (args.risk, \"Risk\"), (args.env, \"Env\"),",
     '             (args.risk, "Risk"),',
     ["TestEnvField.test_edit_sets_the_field_and_then_REPLACES_it"]),

    # Env is bounded by the roster, so it answers to the short fields' rule: a
    # legacy oversized item must stay taggable without --force (T071)
    ("T120 tagging an item with an Env is measured against the block ceiling",
     'FREE_TEXT_FLAGS = ("text", "criterion", "risk", "deferred")',
     'FREE_TEXT_FLAGS = ("text", "criterion", "risk", "deferred", "env")',
     ["TestEnvField.test_tagging_a_legacy_oversized_item_needs_no_force"]),

    # --- T120: the site file's own guards (a different source file) ----------

    ("T120 site a line that is not `key = value` is skipped instead of refused",
     "        if not sep:", "        if False:",
     ["TestEnvField.test_a_line_that_is_not_key_value_is_refused_with_its_number"],
     "bin/tk_site.py"),

    ("T120 site a duplicate key silently wins with the last line",
     "        if key in pairs:", "        if False:",
     ["TestEnvField.test_a_duplicate_key_is_refused"],
     "bin/tk_site.py"),

    ("T120 site a missing required key is not reported",
     "        if key not in pairs:\n            raise SiteError(missing_key_message(path, key, pairs))",
     "        if False:\n            raise SiteError(missing_key_message(path, key, pairs))",
     ["TestEnvField.test_an_absent_identity_is_refused",
      "TestEnvField.test_a_mistyped_roster_key_is_refused_and_the_keys_present_are_listed"],
     "bin/tk_site.py"),

    ("T120 site the message stops listing the keys the file does carry",
     '    have = ", ".join(sorted(keys)) or "(no keys at all)"',
     '    have = "(not listed)"',
     ["TestEnvField.test_a_mistyped_roster_key_is_refused_and_the_keys_present_are_listed"],
     "bin/tk_site.py"),

    ("T120 site an empty roster passes as a roster",
     "    if not names:", "    if False:",
     ["TestEnvField.test_an_empty_roster_is_refused_like_an_absent_one"],
     "bin/tk_site.py"),

    ("T120 site the reserved clear word is allowed as an environment name",
     "        if name == RESERVED_NAME:", "        if False:",
     ["TestEnvField.test_the_reserved_clear_word_cannot_be_an_environment"],
     "bin/tk_site.py"),

    ("T120 site a malformed environment name is allowed",
     "        if not NAME_RE.match(name):", "        if False:",
     ["TestEnvField.test_a_malformed_roster_entry_is_refused"],
     "bin/tk_site.py"),

    ("T120 site the name loses its length bound",
     'NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}\\Z")',
     'NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]*\\Z")',
     ["TestEnvField.test_a_malformed_roster_entry_is_refused"],
     "bin/tk_site.py"),

    ("T120 site the machine may sit outside its own roster (nothing is local)",
     "    if identity not in names:", "    if False:",
     ["TestEnvField.test_an_identity_outside_its_own_roster_is_refused"],
     "bin/tk_site.py"),

    ("T120 site a ceiling that is not a number passes",
     '        if not re.fullmatch(r"[0-9]+", value):', "        if False:",
     ["TestEnvField.test_a_ceiling_that_is_not_a_number_is_refused"],
     "bin/tk_site.py"),

    ("T120 site a ceiling of zero passes",
     "        if int(value) < 1:", "        if False:",
     ["TestEnvField.test_a_ceiling_of_zero_is_refused"],
     "bin/tk_site.py"),

    # the two over-refusal directions: a file the sibling bins must be able to
    # extend, and ceilings that a machine which runs no fleet never writes
    ("T120 site an unknown key becomes fatal (no sibling bin may extend the file)",
     "    for key in REQUIRED:",
     "    for key in set(pairs) - set(REQUIRED) - set(CEILINGS):\n"
     "        raise SiteError(f'{path}: unknown key {key!r}')\n"
     "    for key in REQUIRED:",
     ["TestEnvField.test_comments_blank_lines_and_unknown_keys_are_tolerated"],
     "bin/tk_site.py"),

    # a defect does not have to be in the file's TEXT: a site file that is a
    # directory, or one byte that is not UTF-8, never reaches the parser at all.
    #
    # NO ENTRY for tk_site.load's `except OSError`, deliberately, and this note is
    # the entry's place. Once the regular-file check went in front of the open(),
    # every failure a test can CREATE is intercepted before it — a directory, a
    # FIFO, a socket, a device. What is left for that clause is permission denied
    # (the suite cannot produce it: the container runs as root, and root bypasses
    # the mode bits) and the file vanishing between the check and the open (no
    # hook to drive it). Measured, not assumed: with the clause disabled, the
    # whole suite stays green. It stays in the source because neither case is
    # hypothetical for a reader who is not root, and because a traceback on a
    # permission-denied site file is the exact failure this group of guards
    # exists to prevent. An entry naming a test that falls for another reason
    # would be worse than this gap: it would report a proof nobody made.
    ("T120 site a byte that is not UTF-8 crashes instead of being reported",
     "    except UnicodeDecodeError as e:", "    except ZeroDivisionError as e:",
     ["TestEnvField.test_a_file_that_cannot_be_READ_is_reported_and_not_crashed"],
     "bin/tk_site.py"),

    ("T120 site a BOM is glued to the following key (that key reads as absent)",
     '            text = f.read().replace("﻿", "")', "            text = f.read()",
     ["TestEnvField.test_a_byte_order_mark_does_not_swallow_a_key"],
     "bin/tk_site.py"),

    # the half `utf-8-sig` would have missed: it strips exactly one BOM, at the
    # very start, so the doubled and mid-file placements put the bug straight back
    ("T120 site only the FIRST leading BOM is stripped",
     '            text = f.read().replace("﻿", "")',
     '            text = f.read().replace("﻿", "", 1)',
     ["TestEnvField.test_a_byte_order_mark_does_not_swallow_a_key"],
     "bin/tk_site.py"),

    # open() on a FIFO does not raise, it BLOCKS — the guards above never fire and
    # the session stops with nothing on screen
    ("T120 site a file that is not a plain file is opened anyway (the FIFO hang)",
     "    if not os.path.isfile(path):", "    if False:",
     ["TestEnvField.test_a_site_file_that_is_not_a_plain_file_is_refused_and_never_HANGS"],
     "bin/tk_site.py"),

    ("T120 site a trailing comment becomes part of the value",
     '        line = raw.split("#", 1)[0].strip()', "        line = raw.strip()",
     ["TestEnvField.test_comments_blank_lines_and_unknown_keys_are_tolerated"],
     "bin/tk_site.py"),

    ("T120 site the whitespace around a value is kept",
     "        pairs[key] = value.strip()", "        pairs[key] = value",
     ["TestEnvField.test_comments_blank_lines_and_unknown_keys_are_tolerated"],
     "bin/tk_site.py"),

    # a defect in a hand-written file must come back as a DIAGNOSIS: a traceback
    # names a line of Python, and the reader has to fix a line of THEIR file
    ("T120 a bad site file crashes instead of being reported",
     "    try:\n        site = tk_site.load()\n    except tk_site.SiteError as e:\n"
     "        fail(str(e))\n    if site is None:",
     "    site = tk_site.load()\n    if site is None:",
     ["TestEnvField.test_an_absent_identity_is_refused"]),

    ("T120 site the ceilings become mandatory",
     "        if key not in pairs:\n            continue",
     "        if key not in pairs:\n            raise SiteError(missing_key_message(path, key, pairs))",
     ["TestEnvField.test_the_ceilings_are_optional"],
     "bin/tk_site.py"),

    ("2ª review edit/claim/release splice by search-and-replace again",
     "    return content[:start] + new + content[start + len(block):]",
     "    return content.replace(block, new, 1)",
     ["TestBlockAddressing.test_edit_rewrites_the_real_item_and_not_the_quotation"]),

    # --- T121: the claim, and everything that must not be able to take it ----

    ("T121 a second claim is let through (two sessions hold the same item)",
     '    if held is not None:\n'
     '        fail(f"{label} is already {claim_mark(*claim_value(held))}. '
     'Nothing was "',
     '    if False:\n'
     '        fail(f"{label} is already {claim_mark(*claim_value(held))}. '
     'Nothing was "',
     ["TestClaim.test_a_second_claim_is_refused_naming_the_owner_and_the_moment",
      "TestClaim.test_the_same_owner_cannot_reclaim_it_either",
      "TestClaim.test_a_claim_that_does_not_parse_still_holds_the_item"]),

    # the refusal is the whole product of the guard: "already claimed" with no name
    # tells the caller nothing to act on, and no session to go ask
    ("T121 the refusal stops naming the owner and the moment",
     '        fail(f"{label} is already {claim_mark(*claim_value(held))}. '
     'Nothing was "',
     '        fail(f"{label} is already claimed. Nothing was "',
     ["TestClaim.test_a_second_claim_is_refused_naming_the_owner_and_the_moment",
      "TestClaim.test_a_claim_that_does_not_parse_still_holds_the_item"]),

    ("T121 a claim that does not parse is reported as somebody unnamed",
     "    return segment.value.strip(), None",
     '    return "somebody", None',
     ["TestClaim.test_a_claim_that_does_not_parse_still_holds_the_item"]),

    ("T121 the claim is appended to the BLOCK, landing outside the field chain",
     "    new = append_to_first_line(\n"
     '        block, f"**Claimed:** {args.owner}{CLAIM_SINCE}{stamp}.")',
     '    new = block.rstrip("\\n") + f" **Claimed:** {args.owner}{CLAIM_SINCE}{stamp}."',
     ["TestClaim.test_the_claim_lands_in_the_chain_on_an_item_with_a_continuation_line"]),

    ("T121 a **Claimed:** marker the position rule will not read is guessed",
     "    if markers > (1 if seg else 0):", "    if False:",
     ["TestClaim.test_a_marker_only_outside_the_chain_is_refused_not_guessed",
      "TestClaim.test_prose_ending_in_a_period_before_the_fields_is_not_a_claim"]),

    # the write site has to know the READ site's position rule: without this the
    # item comes back held in the file, shown FREE by `list`, and unreleasable
    ("T121 a claim is written without checking the reader finds it back",
     "    if len(claim_readback(new)) != 1:", "    if False:",
     ["TestClaim.test_an_item_whose_chain_has_no_class_refuses_the_claim",
      "TestClaim.test_an_item_whose_fields_sit_off_the_first_line_is_told_how_to_fold_them",
      "TestClaim.test_a_last_field_missing_its_period_refuses_the_claim_and_names_it"]),

    # the proxy question three fixes asked instead: it passes on the item below,
    # because appending the claim CHANGES the chain it is asked about
    ("T121 the gate asks the chain it READ instead of the one it would WRITE",
     "    if len(claim_readback(new)) != 1:",
     '    if not any(f.canonical == "Class" for f in field_chain(block)):',
     ["TestClaim.test_a_last_field_missing_its_period_refuses_the_claim_and_names_it"]),

    # a refusal that prescribes a command which is ITSELF refused is a dead end: for
    # the continuation-line shape `edit --class` is refused too, and for the missing
    # period it repairs nothing
    ("T121/T126 an item with NO class at all is classified as one whose fields moved",
     '    if not markers(block, "Class"):\n        return CLASS_SHAPE_NONE',
     "    if False:\n        return CLASS_SHAPE_NONE",
     ["TestClaim.test_an_item_whose_chain_has_no_class_refuses_the_claim",
      "TestPack.test_no_class_at_all_is_named_and_the_CLASS_repair_works"]),

    ("T121/T126 the class shape stops discriminating: everything is 'no class'",
     '    if not markers(block, "Class"):\n        return CLASS_SHAPE_NONE',
     "    if True:\n        return CLASS_SHAPE_NONE",
     ["TestClaim.test_a_last_field_missing_its_period_refuses_the_claim_and_names_it",
      "TestPack.test_a_class_off_the_first_line_is_named_and_the_FOLD_repair_works"]),

    # WRITING a claim needs a chain that can hold one; READING one does not. A
    # release that demanded a host would refuse a diagnosis about a claim the item
    # does not even have
    ("T121 release demands a host it does not need",
     "    held = claim_segment(block)\n    if held is None:",
     '    if not any(f.canonical == "Class" for f in field_chain(block)):\n'
     '        fail(f"{label} cannot hold a claim")\n'
     "    held = claim_segment(block)\n    if held is None:",
     ["TestClaim.test_release_on_a_chainless_item_with_no_marker_is_still_an_honest_no_op"]),

    # the order of two refusals: only the stray one is terminal, and preempting it
    # printed a remedy that MUTATED the file and left the real refusal standing
    ("T121 the missing-host refusal preempts the terminal stray one",
     "    held = claim_segment(block)\n    if held is not None:",
     '    if not any(f.canonical == "Class" for f in field_chain(block)):\n'
     '        fail(f"{label}: give it a class first: `tk-queue edit '
     '{label} --class AUTONOMOUS`")\n'
     "    held = claim_segment(block)\n    if held is not None:",
     ["TestClaim.test_a_stray_marker_is_answered_BEFORE_the_missing_host"]),

    ("T121 an ambiguously claimed item is displayed as FREE",
     '    return "claimed ambiguously — `tk-queue claim` says why" if segs else None',
     "    return None",
     ["TestClaim.test_list_never_shows_an_ambiguously_claimed_item_as_free"]),

    # "the chain has no Class" is BROADER than "the fields are elsewhere": it also
    # catches an item whose fields are on line 1 and whose Class merely lost its period
    ("T121/T126 the fold shape is decided by the CHAIN, not by where the marker is",
     '    if not markers(block.split("\\n", 1)[0], "Class"):\n'
     "        return CLASS_SHAPE_OFF_LINE",
     '    if not any(f.canonical == "Class" for f in field_chain(block)):\n'
     "        return CLASS_SHAPE_OFF_LINE",
     ["TestClaim.test_the_refusal_names_the_field_that_BREAKS_the_chain_and_a_reachable_fix",
      "TestPack.test_a_chain_that_never_reaches_the_class_is_named_as_that"]),

    ("T121 the refusal names where the chain STARTS instead of where it stops",
     "    before = [seg for seg in field_segments(line) if seg[1] < chain[0].start()]\n"
     "    return canonical_field(before[-1][0]) if before else None",
     "    return chain[-1].canonical",
     ["TestClaim.test_the_refusal_names_where_the_chain_STOPS_not_where_it_starts"]),

    # the message went back to DIAGNOSING the break and prescribing a per-field
    # repair — wrong for a gap of prose, for period-exempt Source, and refused
    # outright on a duplicated field, a non-DECISION deferral or an Env with no site
    ("T121 the broken-chain refusal guesses the cause and prescribes a per-field edit",
     '    return head + (f"The unbroken run of fields ending that line stops at "\n'
     '                   f"**{chain_breaker(candidate)}:** and never reaches **Class:**, so a "\n'
     '                   "claim cannot be positioned after it. The usual causes are a field "\n'
     '                   "value that does not end in a PERIOD — the period is what tells a field "\n'
     '                   "from prose — and prose sitting between two fields. Which one it is, "\n'
     '                   "this message does not guess: close the item with `cancel` and re-add it "\n'
     '                   "clean. No per-field `edit` repairs this reliably; several are refused "\n'
     '                   "on the very field at fault.")',
     '    return head + (f"**{chain_breaker(candidate)}:** does not end in a PERIOD. Rewrite "\n'
     '                   f"it: `tk-queue edit {label} --effort \\"<value>\\"`.")',
     ["TestClaim.test_a_broken_chain_is_told_WHERE_it_stops_and_never_guesses_why"]),

    ("T121 two claims in the chain are guessed (the first wins) instead of refused",
     "    if len(segs) > 1:\n        fail(f\"{label} carries {len(segs)} **Claimed:**",
     "    if False:\n        fail(f\"{label} carries {len(segs)} **Claimed:**",
     ["TestClaim.test_two_claim_fields_in_the_chain_are_refused_as_ambiguous"]),

    ("T121 Claimed stops being a field the readers know (it leaves FIELD_VARIANTS)",
     '    "Claimed": r"(?:Claimed|Posse)",', '    "Claimed": r"(?!x)x",',
     ["TestClaim.test_a_second_claim_is_refused_naming_the_owner_and_the_moment",
      "TestClaim.test_list_marks_the_claimed_item_and_only_that_one",
      "TestClaim.test_the_marker_shape_is_refused_in_free_text"]),

    ("T121 the owner's shape stops being validated",
     '    if not OWNER_RE.match(name or ""):', "    if False:",
     ["TestClaim.test_a_malformed_owner_is_refused",
      "TestClaim.test_an_empty_owner_is_refused"]),

    # the over-refusal direction: a gate that fires on every name makes the command
    # unusable, and no refusal test can see it
    ("T121 the owner gate refuses every name",
     '    if not OWNER_RE.match(name or ""):', "    if True:",
     ["TestClaim.test_an_ordinary_session_label_is_still_accepted"]),

    ("T121 the reserved clear word is accepted as an owner",
     "    if clears_field(name):", "    if False:",
     ["TestClaim.test_the_reserved_clear_word_cannot_be_an_owner"]),

    ("T121 the claim is stamped with the date only (no time, no UTC)",
     '    return datetime.datetime.now(datetime.timezone.utc).strftime'
     '("%Y-%m-%dT%H:%M:%SZ")',
     "    return datetime.date.today().isoformat()",
     ["TestClaim.test_the_moment_is_recorded_to_the_second_and_in_UTC"]),

    # T071 in the other direction: a bounded field measured against the BLOCK
    # ceiling makes a legacy oversized item unclaimable without --force
    ("T121 claiming is measured against the block ceiling",
     "    splice_item(memdir, content, block, start, new)\n"
     '    print(f"{label} claimed by {args.owner} ({stamp})")',
     "    check_ceiling(new, False)\n"
     "    splice_item(memdir, content, block, start, new)\n"
     '    print(f"{label} claimed by {args.owner} ({stamp})")',
     ["TestClaim.test_claiming_a_legacy_oversized_item_needs_no_force"]),

    ("T121 release splices the field out without the removal-site repair",
     "    splice_item(memdir, content, block, start, clear_field_segment(block, held))",
     '    splice_item(memdir, content, block, start, '
     'block.replace(held.group(0), "", 1))',
     ["TestClaim.test_release_gives_the_item_back_and_leaves_the_file_INTACT",
      "TestClaim.test_a_claim_that_does_not_parse_can_still_be_released"]),

    ("T121 release reports a release it did not perform",
     '        print(f"{label} carries no claim — nothing to release")',
     '        print(f"{label} released")',
     ["TestClaim.test_releasing_an_unclaimed_item_says_so_and_changes_nothing"]),

    ("T121 release stops naming the claim it dropped (a silent steal)",
     '    print(f"{label} released — it was {mark}")',
     '    print(f"{label} released")',
     ["TestClaim.test_release_names_the_claim_it_dropped"]),

    ("T121 list stops showing the mark",
     '+ (f"  [{mark}]" if mark else "")',
     '+ ""',
     ["TestClaim.test_list_marks_the_claimed_item_and_only_that_one"]),

    # the two-command bypass: a flag that can WRITE this field takes an item
    # somebody else holds, which is what `claim` refuses in one command
    ("T121 edit gains a --claimed flag",
     '    e.add_argument("--project", help="assign/change the project tag")',
     '    e.add_argument("--project", help="assign/change the project tag")\n'
     '    e.add_argument("--claimed")',
     ["TestClaim.test_edit_cannot_set_a_claim"]),

    ("T121 the close carries the item's fields, so the claim reaches the done-log",
     "    text = args.summary or item_title(block, limit=400)",
     "    text = args.summary or block.strip()",
     ["TestClaim.test_done_takes_the_claim_with_the_item",
      "TestClaim.test_cancel_takes_the_claim_with_the_item"]),

    # --- T126: pack — every exclusion rule, and the one that must NOT exist ---

    ("T126 pack stops filtering by class, so the package takes every open item",
     "    if cls != \"AUTONOMOUS\":\n"
     "        return pack_classless_reason(block) if cls is None else (f\"class is {cls}\", None)",
     "    if False:\n"
     "        return pack_classless_reason(block) if cls is None else (f\"class is {cls}\", None)",
     ["TestPack.test_every_class_but_AUTONOMOUS_is_excluded_by_name"]),

    # over-trigger: a class filter that excludes everything empties the package,
    # and only the test asserting the legitimate item sees it
    ("T126 pack excludes every class, AUTONOMOUS included",
     "    if cls != \"AUTONOMOUS\":", "    if cls or True:",
     ["TestPack.test_an_eligible_item_carries_its_id_effort_and_text"]),

    # the loose reader `list` uses: leftmost marker in the whole block, prose
    # included. It drops an AUTONOMOUS item out of every package over a class word
    # quoted in its own text
    ("T126 pack reads the class the way `list` displays it, not from the chain",
     "    cls = chain_class(block)",
     "    cls = (lambda m: m.group(1) if m else None)(CLASS_VALUE_RE.search(block))",
     ["TestPack.test_a_class_QUOTED_IN_PROSE_does_not_decide_the_package"]),

    ("T126 pack guesses a class where the chain names two",
     '    found = [f for f in field_chain(block) if f.canonical == "Class"]\n'
     "    if len(found) > 1:",
     '    found = [f for f in field_chain(block) if f.canonical == "Class"]\n'
     "    if False:",
     ["TestPack.test_two_classes_in_the_chain_are_ambiguous_not_guessed"]),

    # the shape each message maps to: the classification above is shared, the mapping
    # from shape to line is not
    ("T126 the package maps two of the three class shapes to the wrong line",
     '        return "**Class:** sits off the first line, where no gate reads it", REPAIR_FOLD',
     '        return "no **Class:** field", REPAIR_CLASSLESS',
     ["TestPack.test_a_class_off_the_first_line_is_named_and_the_FOLD_repair_works"]),

    # the remedy printed for a broken chain has to be one `cancel` ACCEPTS: without
    # `--why` argparse refuses it, and the line is a dead end dressed as an answer
    ("T126 the cancel remedy drops the flag the command requires",
     'REPAIR_CANCEL = ("a chain no gate can read: `tk-queue cancel <id> --why \\"<why>\\"` + re-add "',
     'REPAIR_CANCEL = ("a chain no gate can read: `tk-queue cancel <id>` + re-add "',
     ["TestPack.test_the_CANCEL_repair_is_printed_and_the_command_ACCEPTS_it"]),

    # the AC itself: the shape a skill's prose reads, documented where the script
    # carries it — and asserted against a real run, so it cannot drift
    ("T126 the output format leaves the help",
     "                   epilog=PACK_FORMAT,\n", "",
     ["TestPack.test_the_output_format_is_documented_in_the_help"]),

    ("T126 the documented sample drifts from what the command prints",
     'PACK_SAMPLE = """eligible (4 of 8, in queue order):',
     'PACK_SAMPLE = """eligible (4 of 8, in file order):',
     ["TestPack.test_the_documented_sample_IS_what_the_command_prints"]),

    # --- the Risk rule -------------------------------------------------------

    ("T126 pack packages an item carrying a Risk line",
     '    if field["Risk"] is not None:\n'
     '        return "Risk: " + field_value(field["Risk"]), None',
     "    if False:\n"
     '        return "Risk: " + field_value(field["Risk"]), None',
     ["TestPack.test_a_Risk_excludes_the_item_and_the_reason_carries_the_LINE"]),

    # the reason without the VALUE: the verdict alone sends the reader back to the
    # file for the one line they re-triage the item from
    ("T126 the Risk reason drops the line it read",
     '        return "Risk: " + field_value(field["Risk"]), None',
     '        return "carries a Risk", None',
     ["TestPack.test_a_Risk_excludes_the_item_and_the_reason_carries_the_LINE"]),

    ("T126 the value reader eats every trailing period, not the field terminator",
     "    return re.sub(r\"\\.\\Z\", \"\", body).strip()",
     "    return body.rstrip(\".\").strip()",
     ["TestPack.test_only_the_field_terminator_is_stripped_off_the_value"]),

    # a marker the position rule may not read is not thereby harmless: passing the
    # item dispatches, unattended, something that may carry a Risk or another
    # machine's Env
    ("T126 a marker no gate may read is treated as no field at all",
     "        if markers > len(segs):", "        if False:",
     ["TestPack.test_a_Risk_marker_no_gate_may_read_still_excludes_the_item",
      "TestPack.test_an_Env_marker_no_gate_may_read_still_excludes_the_item"]),

    ("T126 pack guesses a value where the chain names two",
     "        if len(segs) > 1:\n"
     '            return (f"{len(segs)} **{name}:** fields in the chain, so its value is "',
     "        if False:\n"
     '            return (f"{len(segs)} **{name}:** fields in the chain, so its value is "',
     ["TestPack.test_two_Env_fields_are_ambiguous_not_guessed"]),

    # --- the Env rule --------------------------------------------------------

    ("T126 pack packages an item bound to another machine",
     "        if value != identity:", "        if False:",
     ["TestPack.test_an_item_bound_to_ANOTHER_machine_is_out_naming_BOTH_names"]),

    # over-trigger: an Env rule that never matches the local identity excludes every
    # item that names WHERE it runs, including the ones that name this machine
    ("T126 an item bound to THIS machine is excluded too",
     "        if value != identity:", "        if value or True:",
     ["TestPack.test_an_item_bound_to_this_machine_is_eligible"]),

    ("T126 a missing site file becomes a refusal instead of an empty roster",
     "    return site.identity if site else None",
     "    if site is None:\n"
     "        fail(\"pack: \" + tk_site.missing_file_message())\n"
     "    return site.identity",
     ["TestPack.test_with_no_site_file_an_Env_is_foreign_and_no_Env_is_local"]),

    ("T126 a site file that exists and is BROKEN is read as an absent one",
     "    except tk_site.SiteError as e:\n"
     "        fail(str(e))\n"
     "    return site.identity if site else None",
     "    except tk_site.SiteError:\n"
     "        return None\n"
     "    return site.identity if site else None",
     ["TestPack.test_a_site_file_that_EXISTS_and_is_broken_is_refused_verbatim"]),

    # the same rule in two places: the writer already refuses a value outside the
    # roster, and the day the roster changes this one starts refusing items that
    # were already in the file
    ("T126 pack revalidates the Env against the roster on the way out",
     '        value = field_value(field["Env"])\n'
     "        if value != identity:",
     '        value = field_value(field["Env"])\n'
     "        validate_env(value)\n"
     "        if value != identity:",
     ["TestPack.test_the_roster_is_NOT_revalidated_on_the_way_out"]),

    # unquoted, a field a hand-edit left empty prints "Env is , this machine is X"
    ("T126 the Env value is printed unquoted, so an empty one reads as no value",
     '            return f"Env is {value!r}, {where}", None',
     '            return f"Env is {value}, {where}", None',
     ["TestPack.test_an_EMPTY_Env_reads_as_an_empty_value_and_not_as_no_value"]),

    # --- the claim rule ------------------------------------------------------

    ("T126 pack packages an item a sibling session is holding",
     "    mark = displayed_claim(block)\n"
     "    if mark:", "    mark = displayed_claim(block)\n"
     "    if False:",
     ["TestPack.test_a_claimed_item_is_out_and_the_line_says_who_holds_it",
      "TestPack.test_the_RELEASE_repair_is_printed_and_gives_the_item_back"]),

    ("T126 a Claimed marker no gate may read is read as a free item",
     "    if qualified_fields(block, \"Claimed\")[1]:", "    if False:",
     ["TestPack.test_a_Claimed_marker_no_gate_may_read_still_excludes_the_item",
      "TestPack.test_one_malformed_item_does_not_stop_the_others"]),

    # --- the ID rule, and its POSITION in the order --------------------------

    ("T126 pack packages an item no command can close by ID",
     "    if iid is None:\n"
     "        return \"no ID\", REPAIR_MIGRATE",
     "    if False:\n"
     "        return \"no ID\", REPAIR_MIGRATE",
     ["TestPack.test_an_item_with_no_ID_is_not_packaged_and_MIGRATE_repairs_it"]),

    # the order IS the contract: the first rule that applies is the reason printed,
    # and asked first this one hides the class of every legacy ID-less item
    ("T126 the missing ID is asked before the class instead of last",
     "    cls = chain_class(block)",
     "    if iid is None:\n"
     "        return \"no ID\", REPAIR_MIGRATE\n"
     "    cls = chain_class(block)",
     ["TestPack.test_the_missing_ID_is_asked_LAST_not_first"]),

    # --- the rule that must NOT be here --------------------------------------
    # `--deferred` is refused on every class but DECISION and leaving that class
    # drops it, so no path through this CLI makes an AUTONOMOUS item carrying one.
    # Re-asserting the invariant here is the second place, and the second place rots
    ("T126 pack re-reads the deferral the writer already guarantees",
     "    mark = displayed_claim(block)",
     "    if qualified_fields(block, \"Deferred\")[0]:\n"
     "        return \"carries a Deferred\", None\n"
     "    mark = displayed_claim(block)",
     ["TestPack.test_a_Deferred_field_decides_NOTHING_here"]),

    # --- the two lists, and the shape a skill's prose reads ------------------

    ("T126 pack sorts the package instead of keeping the queue's order",
     "    total = len(eligible) + len(excluded)",
     "    eligible.sort()\n    total = len(eligible) + len(excluded)",
     ["TestPack.test_the_eligible_follow_the_queues_own_order",
      "TestPack.test_bump_moves_an_item_to_the_top_of_the_package_too"]),

    ("T126 pack packages the items already closed",
     '        if kind != "item-open":\n            continue\n        iid = item_id(text)\n'
     "        # the item's own spelling, from item_label:",
     '        if kind == "other":\n            continue\n        iid = item_id(text)\n'
     "        # the item's own spelling, from item_label:",
     ["TestPack.test_a_checked_item_is_not_a_candidate"]),

    ("T126 the repair is repeated once per item instead of once per shape",
     "        if repair and repair not in repairs:", "        if repair:",
     ["TestPack.test_a_repair_is_printed_ONCE_however_many_items_need_it"]),

    ("T126 an unreadable Effort raises instead of answering '?'",
     "    if len(segs) != 1 or markers > len(segs):\n"
     '        return "?"', "    if False:\n"
     '        return "?"',
     ["TestPack.test_an_unreadable_Effort_does_not_cost_the_item_its_place"]),

    # the observable moved with T215: naming the queue no longer tells a reader
    # from a writer, since every command but `report` names it — the LOCK does
    ("T126 pack stops being a reader, so it queues behind a writer",
     "READERS = frozenset((\"list\", \"report\", \"pack\"))",
     "READERS = frozenset((\"list\", \"report\"))",
     ["TestConcurrency.test_pack_reads_straight_through_a_held_lock"]),

    # --- T122 handoff: the briefing that lives and dies with the item --------
    ("T122 the write gate asks a PROXY instead of the composed briefing",
     "    if heads != composed:", "    if heads != heads:",
     ["TestHandoffCreation.test_a_heading_inside_a_value_is_refused_and_the_remedy_runs",
      "TestHandoffCreation.test_a_level_one_heading_inside_a_value_is_refused_too"]),

    ("T122 an empty mandatory field composes a briefing nobody filled",
     "    blank = [h for h, body in got[1:] if not body]",
     "    blank = [h for h, body in got[1:] if body is None]",
     ["TestHandoffCreation.test_a_mandatory_field_with_no_text_is_refused_and_the_remedy_runs",
      "TestHandoffCreation.test_the_blockers_field_is_mandatory_too"]),

    ("T122 a blank MANDATORY field is dropped from the file, so the gate never sees it",
     "        if not body and not mandatory:", "        if not body:",
     ["TestHandoffCreation.test_a_mandatory_field_with_no_text_is_refused_and_the_remedy_runs"]),

    ("T122 **Blockers and notes** stops being mandatory",
     '    ("blockers", "Blockers and notes", True),',
     '    ("blockers", "Blockers and notes", False),',
     ["TestHandoffCreation.test_the_blockers_field_is_mandatory_too"]),

    ("T122 sub-structure inside a field is framed like a field",
     'HANDOFF_HEADING_RE = re.compile(r"^#{1,2} .*$", re.M)',
     'HANDOFF_HEADING_RE = re.compile(r"^#+ .*$", re.M)',
     ["TestHandoffCreation.test_a_deeper_heading_is_sub_structure_and_passes"]),

    ("T122 the briefing's fate is read from the queue BEFORE the close, not after",
     "    handoff_collect(memdir, excise(content, block, start),",
     "    handoff_collect(memdir, content,",
     ["TestHandoffLifecycle.test_done_removes_the_briefing_in_the_same_command",
      "TestHandoffLifecycle.test_cancel_removes_it_too"]),

    ("T122 a campaign's briefing is never a candidate, so the last item leaves it orphaned",
     "    return handoff_refs(block) | ({iid} if iid is not None else set())",
     "    return {iid} if iid is not None else set()",
     ["TestHandoffLifecycle.test_a_campaign_briefing_outlives_its_anchor_and_dies_with_the_last_item"]),

    ("T122 the item's OWN briefing is not a candidate",
     "    return handoff_refs(block) | ({iid} if iid is not None else set())",
     "    return handoff_refs(block)",
     ["TestHandoffLifecycle.test_cancel_removes_it_too"]),

    ("T122 a CLOSED item still counts as reaching the briefing, so it is kept forever",
     '        if kind != "item-open":\n            continue\n        iid = item_id(text)\n'
     '        if iid == n or n in handoff_refs(text):',
     '        if kind == "other":\n            continue\n        iid = item_id(text)\n'
     '        if iid == n or n in handoff_refs(text):',
     ["TestHandoffLifecycle.test_a_TICKED_sibling_no_longer_holds_the_briefing_open"]),

    ("T122 the existence check is inverted: an existing briefing is skipped",
     "        if not os.path.exists(handoff_path(memdir, n)):",
     "        if os.path.exists(handoff_path(memdir, n)):",
     ["TestHandoffLifecycle.test_done_removes_the_briefing_in_the_same_command",
      "TestHandoffLifecycle.test_a_pointer_to_a_briefing_that_was_never_written_closes_cleanly"]),

    ("T122 an overwrite reports itself as a first write",
     "    existed = os.path.exists(path)", "    existed = False",
     ["TestHandoffCreation.test_writing_it_again_overwrites_and_never_accumulates"]),

    ("T122 the discovery-path warning fires even when the item DOES point at it",
     "    if args.id not in handoff_refs(block):", "    if args.id not in set():",
     ["TestHandoffCreation.test_the_missing_pointer_warning_names_a_remedy_that_runs"]),

    ("T122 a link the writer did not zero-pad is invisible, and the close DELETES a "
     "briefing another item still points at",
     'HANDOFF_REF_RE = re.compile(r"\\[\\[handoff-T([0-9]+)\\]\\]")',
     'HANDOFF_REF_RE = re.compile(r"\\[\\[handoff-T([0-9]{3,})\\]\\]")',
     ["TestHandoffLifecycle.test_a_link_without_the_writers_zero_padding_still_holds"]),

    ("T122 the collection stops asking whether the file is OURS",
     "        if not handoff_ours(memdir, n):", "        if handoff_ours(memdir, n):",
     ["TestHandoffLifecycle.test_a_file_this_command_did_not_write_is_never_deleted",
      "TestHandoffLifecycle.test_done_removes_the_briefing_in_the_same_command"]),

    ("T122 the ownership header is asked without the writer's zero-padding",
     '            return f.readline().startswith(f"# Handoff T{n:03d}")',
     '            return f.readline().startswith(f"# Handoff T{n}")',
     ["TestHandoffLifecycle.test_done_removes_the_briefing_in_the_same_command"]),

    ("T122 an UNREADABLE file counts as ours, so a directory reaches os.remove",
     "    except OSError:\n        return False", "    except OSError:\n        return True",
     ["TestHandoffLifecycle.test_a_DIRECTORY_at_the_briefing_name_does_not_fail_the_close"]),

    ("T122 --force stops overriding the write guard, so the remedy is a dead end",
     "    if existed and not handoff_ours(memdir, args.id) and not args.force:",
     "    if existed and not handoff_ours(memdir, args.id):",
     ["TestHandoffCreation.test_writing_over_a_file_this_command_did_not_write_is_refused"]),

    ("T122 the write guard fires on OUR briefing and spares the stranger's file",
     "    if existed and not handoff_ours(memdir, args.id) and not args.force:",
     "    if existed and handoff_ours(memdir, args.id) and not args.force:",
     ["TestHandoffCreation.test_rewriting_OUR_own_briefing_needs_no_force",
      "TestHandoffCreation.test_writing_over_a_file_this_command_did_not_write_is_refused"]),

    ("T122 an unnumbered open item is dropped from the holders (a wrong DELETE)",
     '            out.append(f"T{iid:03d}" if iid is not None else "an unnumbered item")',
     '            out.append(f"T{iid:03d}") if iid is not None else None',
     ["TestHandoffLifecycle.test_an_UNNUMBERED_open_item_holds_the_briefing_it_points_at"]),

    ("T122 an unnumbered holder is formatted as an ID and crashes an applied close",
     '            out.append(f"T{iid:03d}" if iid is not None else "an unnumbered item")',
     '            out.append(f"T{iid:03d}")',
     ["TestHandoffLifecycle.test_an_UNNUMBERED_open_item_holds_the_briefing_it_points_at"]),

    ("T122 the OWNER is recognised only by a pointer it was never forced to write",
     "        if iid == n or n in handoff_refs(text):", "        if n in handoff_refs(text):",
     ["TestHandoffLifecycle.test_the_OWNER_holds_its_briefing_even_when_it_never_points_at_it"]),

    ("T122 the empty-field refusal reads as a singular whatever the count",
     '        verb = "carries" if len(empty) == 1 else "carry"', '        verb = "carries"',
     ["TestHandoffCreation.test_TWO_empty_fields_read_as_a_plural"]),

    ("T122 the two-field remedy is printed as a LIST argparse refuses",
     "        remedy = \" \".join(f'{f} \"none\"' for f in empty)",
     "        remedy = ', '.join(empty) + ' \"none\"'",
     ["TestHandoffCreation.test_TWO_empty_fields_still_print_ONE_runnable_remedy"]),

    ("T122 the pointer remedy stops carrying the --force the ceiling demands",
     '        forced = " --force" if len(block) + len(link) + 1 > CEILING else ""',
     '        forced = ""',
     ["TestHandoffCreation.test_the_remedy_never_truncates_the_item_it_rewrites"]),

    ("T122 an ABSENT optional field writes an empty section instead of none",
     "        if not body and not mandatory:", "        if not body and mandatory:",
     ["TestHandoffCreation.test_an_absent_optional_field_writes_no_section_at_all"]),

    ("T122 the documented format drops out of the help",
     "                        epilog=HANDOFF_FORMAT,", "                        epilog=None,",
     ["TestHandoffCreation.test_the_help_embeds_that_same_sample"]),

    ("T122 the documented sample drifts from what the command writes",
     "## Blockers and notes\n\nnone\n\"\"\"", "## Blockers e notas\n\nnone\n\"\"\"",
     ["TestHandoffCreation.test_the_documented_sample_is_what_the_command_actually_writes"]),

    ("T122 a ref is only read at the start of a line, so one quoted in prose is invisible",
     'HANDOFF_REF_RE = re.compile(r"\\[\\[handoff-T([0-9]+)\\]\\]")',
     'HANDOFF_REF_RE = re.compile(r"^\\[\\[handoff-T([0-9]+)\\]\\]", re.M)',
     ["TestHandoffLifecycle.test_a_ref_quoted_in_prose_only_DELAYS_the_collection"]),

    ("T122 `edit` stops collecting the briefing it dropped the last pointer to",
     "    dropped = handoff_refs(block) - handoff_refs(new)",
     "    dropped = handoff_refs(new) - handoff_refs(block)",
     ["TestHandoffLifecycle.test_edit_collects_a_briefing_it_stops_pointing_at",
      "TestHandoffLifecycle.test_an_IMPLICIT_deferred_clear_still_collects_the_pointer_it_dropped"]),

    ("T122 `edit` collects a briefing another OPEN item still points at",
     "        handoff_collect(memdir, splice(content, block, start, new), dropped)",
     "        handoff_collect(memdir, content, dropped)",
     ["TestHandoffLifecycle.test_edit_keeps_a_briefing_another_item_still_points_at"]),

    ("T122 `migrate` closes items and leaves their briefings behind",
     "        ids |= handoff_candidates(item_id(text), text)", "        ids |= set()",
     ["TestHandoffLifecycle.test_migrate_collects_the_briefing_of_what_it_closes"]),

    ("T122 the printed remedy is not quoted for a shell",
     "f\"{shlex.quote(fixed)}{forced}`.\", file=sys.stderr)",
     "f\"{fixed}{forced}`.\", file=sys.stderr)",
     ["TestHandoffCreation.test_the_missing_pointer_warning_names_a_remedy_that_runs"]),

    ("T122 the remedy prints an ABBREVIATED copy of the text it tells you to write back",
     '        fixed = f"{item_title(block, limit=10 ** 6)} {link}"',
     '        fixed = f"{item_title(block, limit=400)} {link}"',
     ["TestHandoffCreation.test_the_remedy_never_truncates_the_item_it_rewrites"]),

    ("BOM read() lets one at the head through to the `^`-anchored grammars again",
     ['        return data.decode("utf-8-sig")',
      '    f"{BOM}*" + r"-[ \\t" + INVISIBLE_BLANKS + r"]\\[( |x)\\][ \\t" '
      '+ INVISIBLE_BLANKS + r"]"'],
     ['        return data.decode("utf-8")',
      '    r"-[ \\t" + INVISIBLE_BLANKS + r"]\\[( |x)\\][ \\t" '
      '+ INVISIBLE_BLANKS + r"]"'],
     ["TestByteOrderMark.test_the_first_item_is_neither_hidden_nor_blamed_on_a_concurrent_writer",
      "TestByteOrderMark.test_the_hidden_items_id_is_never_handed_out_twice",
      "TestByteOrderMark.test_a_bom_in_the_done_log_keeps_its_first_entry_allocated"]),
     # NOT test_a_bom_further_INTO_the_file_is_left_alone: it passes with the
     # defect restored, by construction — it guards the OPPOSITE direction, and
     # naming it here would claim a proof this run cannot make

    # the other direction, which no mutation above covers: a strip that reaches
    # PAST the head silently edits the user's own text
    ("BOM the strip reaches past the head, into the user's own text",
     '        return normalize_source(f.read(), os.path.basename(path))',
     '        return normalize_source(f.read(), os.path.basename(path)).replace(BOM, "")',
     ["TestByteOrderMark.test_a_bom_further_INTO_the_file_is_left_alone"]),

    ("ID the label is rebuilt from the parsed number, so T0001 prints as T001 again",
     '    m = ITEM_ID_RE.match(text)\n    return ("T" + m.group(2)) if m else "----"',
     '    iid = item_id(text)\n    return f"T{iid:03d}" if iid else "----"',
     ["TestIdSpelling.test_list_prints_each_item_under_its_own_spelling",
      "TestIdSpelling.test_pack_reads_the_id_the_way_list_does"]),
     # NOT the two allocation tests: the display is not what they measure, and
     # naming a test that passes here would claim a proof this run cannot make

    # the WRONG fix for the collision, and the reason the repair had to stay in
    # the display: capping the width hides T0001 from the allocator, which hands
    # its number out again — and breaks T1000 the day IDs reach four digits
    ("ID the slot hard-caps the width at three digits",
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3,})(?:~~)?\\*\\*"',
     'ID_SLOT = r"\\*\\*(?:~~)?T([0-9]{3})(?:~~)?\\*\\*"',
     ["TestIdSpelling.test_a_wide_spelling_is_still_an_allocated_id",
      "TestIdSpelling.test_a_four_digit_id_is_canonical_and_is_not_capped"]),

    # the guard's own boundary, not the whole warning: a pair stops counting as
    # ambiguous and the silence is back, while a triple would still warn
    ("ID two open items under one number go back to being resolved in silence",
     "    if len(found) > 1:\n        print(ambiguous_id_message(",
     "    if len(found) > 2:\n        print(ambiguous_id_message(",
     ["TestAmbiguousId.test_edit_says_which_occurrence_it_acted_on_and_still_acts",
      "TestAmbiguousId.test_the_warning_sits_where_the_ID_is_RESOLVED_not_in_edit",
      "TestAmbiguousId.test_a_wide_spelling_is_the_same_ambiguity"]),

    ("ID every resolution warns, ambiguous or not",
     "    if len(found) > 1:\n        print(ambiguous_id_message(",
     "    if len(found) >= 1:\n        print(ambiguous_id_message(",
     ["TestAmbiguousId.test_an_ID_carried_by_ONE_item_is_not_warned_about"]),

    ("ID `list` stops marking a duplicated ID (only a triple would count)",
     "ids.count(i) > 1", "ids.count(i) > 2",
     ["TestAmbiguousId.test_list_marks_every_row_under_a_duplicated_id"]),

    ("ID `list` marks every row as duplicated, which marks nothing",
     "ids.count(i) > 1", "ids.count(i) > 0",
     ["TestAmbiguousId.test_list_marks_every_row_under_a_duplicated_id",
      "TestAmbiguousId.test_an_ID_carried_by_ONE_item_is_not_warned_about"]),

    # --- T121 `migrate` folds a chain that sits off the first line ----------
    # The defect itself: `migrate` was the command documented as the repair for
    # legacy shapes and folded nothing, so 31 of 155 real open items stayed
    # invisible to every gate. NOT named here are the three tests that pass with
    # the fold off by construction — the canonical queue, the item with no field
    # at all, and the second-run no-op, which is a no-op either way
    ("T121 `migrate` folds nothing again: the fields stay off the first line",
     "            new, refusal = fold_chain_onto_first_line(text)",
     "            new, refusal = None, None",
     ["TestMigrateFold.test_the_legacy_shape_is_folded_and_the_prose_survives_it",
      "TestMigrateFold.test_after_the_fold_pack_claim_and_edit_all_reach_the_item",
      "TestMigrateFold.test_a_chain_spread_over_TWO_continuation_lines_is_folded_too",
      "TestMigrateFold.test_an_idless_legacy_item_is_folded_AND_numbered_in_one_pass",
      "TestMigrateFold.test_the_two_populations_are_separated_in_ONE_run",
      "TestMigrateFold.test_a_marker_whose_value_sits_on_the_NEXT_line_is_left_and_REPORTED",
      "TestMigrateFold.test_a_NOTE_line_after_the_field_line_is_left_and_REPORTED",
      "TestMigrateFold.test_a_marker_in_the_item_s_OWN_PROSE_is_left_and_REPORTED",
      "TestMigrateFold.test_a_marker_that_forms_no_chain_at_all_is_left_and_REPORTED"]),

    # the readback: the fold may RELOCATE a chain, never CONSTRUCT one. Off, the
    # command joins the lines anyway and writes a field the item never carried.
    # NOT named: the marker-whose-value-is-on-the-next-line test. That shape is
    # refused one guard earlier (its last line opens mid-value, so it carries no
    # field RUN), so it passes with this one off — naming it would claim a proof
    # this run cannot make. The pair below is what decides that shape
    ("T121 the fold stops asking the reader what the folded line gives back",
     "    if ([seg.rstrip() for seg in run]\n"
     "            != [f.text.rstrip() for f in chain]):",
     "    if False:",
     ["TestMigrateFold.test_a_marker_in_the_item_s_OWN_PROSE_is_left_and_REPORTED"]),

    # the block whose lines carry no field RUN, joined blindly and returned — the
    # decision the `not run` refusal and the readback make TOGETHER, and the only
    # one that answers the marker-and-value-on-different-lines shape. The join
    # itself still runs: what is switched off is the rule, not the step
    ("T121 the fold trusts the join on a block it can read no field run out of",
     "    if not run:\n        return None, FOLD_REFUSAL",
     "    if not run:\n        return (\" \".join(ln.strip() for ln in lines)\n"
     "                + block[len(block.rstrip(\"\\n\")):]), None",
     ["TestMigrateFold.test_a_marker_whose_value_sits_on_the_NEXT_line_is_left_and_REPORTED",
      "TestMigrateFold.test_a_NOTE_line_after_the_field_line_is_left_and_REPORTED",
      "TestMigrateFold.test_a_marker_that_forms_no_chain_at_all_is_left_and_REPORTED"]),

    # the whitespace half of that comparison, on its own: a chain WRAPPED over two
    # continuation lines is whole, and refusing it repairs an item the fold could lift
    ("T121 the readback counts the blank at a line joint as a changed value",
     "    if ([seg.rstrip() for seg in run]\n"
     "            != [f.text.rstrip() for f in chain]):",
     "    if [seg for seg in run] != [f.text for f in chain]:",
     ["TestMigrateFold.test_a_chain_spread_over_TWO_continuation_lines_is_folded_too"]),

    # a fold that lifts nothing still rewrites the user's line and reports it as
    # repaired — the one direction a data-rewriting command may never take
    ("T121 an item whose lines carry no field RUN is folded anyway",
     "    if not run:\n        return None, FOLD_REFUSAL",
     "    if False:\n        return None, FOLD_REFUSAL",
     ["TestMigrateFold.test_a_marker_that_forms_no_chain_at_all_is_left_and_REPORTED"]),

    # the weaker question the guard deliberately does not ask: "does ANY chain end
    # the first line" answers YES for a **Class:** whose value sits on the next one,
    # and that item — the shape the repairs text calls unfoldable — is passed over
    # in SILENCE, which is the outcome the report exists to prevent
    ("T121 the skip asks for any chain instead of one that reaches the class",
     "    if chain_class(block) is not None:", "    if field_chain(block):",
     ["TestMigrateFold.test_a_marker_whose_value_sits_on_the_NEXT_line_is_left_and_REPORTED"]),

    ("T121 an item with no field off the first line is dragged into the fold's report",
     "    if not fields_off_first_line(block):", "    if False:",
     ["TestMigrateFold.test_an_item_with_no_field_at_all_is_neither_folded_nor_reported"]),

    # the two report lines, each on its own: silence about what was rewritten, and
    # silence about what was left, are different failures of the same command
    ("T121 the fold rewrites the file and says nothing about it",
     "    if folded:\n        print(", "    if False:\n        print(",
     ["TestMigrateFold.test_the_legacy_shape_is_folded_and_the_prose_survives_it",
      "TestMigrateFold.test_an_idless_legacy_item_is_folded_AND_numbered_in_one_pass",
      "TestMigrateFold.test_the_two_populations_are_separated_in_ONE_run"]),

    ("T121 the items the fold could NOT lift go unreported (silent partial success)",
     "    if left_alone:\n        for why, labels in group_by_reason(left_alone):",
     "    if False:\n        for why, labels in group_by_reason(left_alone):",
     ["TestMigrateFold.test_a_marker_whose_value_sits_on_the_NEXT_line_is_left_and_REPORTED",
      "TestMigrateFold.test_a_NOTE_line_after_the_field_line_is_left_and_REPORTED",
      "TestMigrateFold.test_a_marker_in_the_item_s_OWN_PROSE_is_left_and_REPORTED",
      "TestMigrateFold.test_a_marker_that_forms_no_chain_at_all_is_left_and_REPORTED",
      "TestMigrateFold.test_the_two_populations_are_separated_in_ONE_run"]),

    # the ORDER inside the loop: read before the ID is assigned, the label of an
    # item that gained both is `----`, which names no item the caller can act on
    ("T121 the report reads the label before `migrate` assigns the ID",
     "            if item_id(text) is None:\n"
     "                nid += 1\n"
     '                text = text.replace("- [ ] ", f"- [ ] **T{nid:03d}** — ", 1)\n'
     "            if new is not None:\n"
     "                folded.append(item_label(text))\n"
     "            elif refusal:\n"
     "                left_alone.append((item_label(text), refusal))",
     "            if new is not None:\n"
     "                folded.append(item_label(text))\n"
     "            elif refusal:\n"
     "                left_alone.append((item_label(text), refusal))\n"
     "            if item_id(text) is None:\n"
     "                nid += 1\n"
     '                text = text.replace("- [ ] ", f"- [ ] **T{nid:03d}** — ", 1)',
     ["TestMigrateFold.test_an_idless_legacy_item_is_folded_AND_numbered_in_one_pass"]),

    # --- review#3: the fold flattened the item's MARKDOWN -------------------
    # It joined every line of the block into one and read only the field segments
    # back, so 8 of the 11 items it folded across the real queues lost their list
    # or their line breaks and were reported as folded. Each entry below puts one
    # half of the repair back.

    # the defect itself: every intervening line absorbed, bullets included
    ("review#3 the fold absorbs every line between the head and the chain",
     "    j = 1\n    while j < first and not opens_a_block(lines, j):\n        j += 1",
     "    j = first",
     ["TestFoldKeepsTheItemsMarkdown."
      "test_a_bulleted_list_between_the_head_and_the_chain_survives_the_fold",
      "TestFoldKeepsTheItemsMarkdown.test_the_gates_reach_an_item_folded_AROUND_its_list",
      "TestFoldKeepsTheItemsMarkdown.test_prose_that_wraps_AFTER_a_block_is_not_lifted_over_it",
      "TestFoldKeepsTheItemsMarkdown."
      "test_both_populations_fold_in_ONE_run_each_keeping_its_own_shape"]),

    # the classifier stops asking CommonMark's block-start set. Nothing is
    # flattened even so — the absorption audit refuses the item instead, because a
    # bullet does not open the way a wrapped sentence opens — which is the whole
    # point of the default having changed direction
    ("review#3 a line that opens a block is joinable like any other",
     "    if BLOCK_START_RE.match(stripped):\n        return True",
     "    if False:\n        return True",
     ["TestFoldKeepsTheItemsMarkdown."
      "test_a_bulleted_list_between_the_head_and_the_chain_survives_the_fold",
      "TestFoldKeepsTheItemsMarkdown.test_the_gates_reach_an_item_folded_AROUND_its_list",
      "TestFoldKeepsTheItemsMarkdown.test_prose_that_wraps_AFTER_a_block_is_not_lifted_over_it"]),

    # the same rule read out of the regex: with the bullet arm gone the fold stops
    # seeing a list, and the item comes back refused instead of folded around it
    ("review#3 a bullet stops opening a Markdown block",
     "      [-*+][ \\t]           # a bullet",
     "      (?!)                 # a bullet",
     ["TestFoldKeepsTheItemsMarkdown."
      "test_a_bulleted_list_between_the_head_and_the_chain_survives_the_fold",
      "TestFoldKeepsTheItemsMarkdown.test_the_gates_reach_an_item_folded_AROUND_its_list",
      "TestFoldKeepsTheItemsMarkdown.test_prose_that_wraps_AFTER_a_block_is_not_lifted_over_it",
      "TestFoldKeepsTheItemsMarkdown."
      "test_a_marker_stranded_on_a_BLOCK_line_is_left_and_REPORTED"]),

    # the other direction, and the expensive one: 7 of those 8 items are a
    # hard-wrapped sentence, which Markdown renders identically joined. Kept as
    # its own line, the chain lands inside the unclosed parenthesis the wrap left
    ("review#3 nothing is absorbed, so a wrapped sentence is cut by the chain",
     "    while j < first and not opens_a_block(lines, j):",
     "    while j < first and False:",
     ["TestFoldKeepsTheItemsMarkdown.test_a_hard_wrapped_sentence_is_still_absorbed_into_the_head",
      "TestFoldKeepsTheItemsMarkdown."
      "test_both_populations_fold_in_ONE_run_each_keeping_its_own_shape",
      "TestMigrateFold.test_the_legacy_shape_is_folded_and_the_prose_survives_it",
      "TestMigrateFold.test_after_the_fold_pack_claim_and_edit_all_reach_the_item",
      "TestMigrateFold.test_the_frontmatter_headings_and_the_done_log_move_stay_intact",
      "TestMigrateFold.test_the_two_populations_are_separated_in_ONE_run"]),

    # the lines that stay, stripped on the way through: the structure survives and
    # the NESTING does not, which is the half a block-level check cannot see
    ("review#3 the lines that stay are re-indented on the way through",
     "    kept = lines[j:first]", "    kept = [ln.strip() for ln in lines[j:first]]",
     ["TestFoldKeepsTheItemsMarkdown."
      "test_a_bulleted_list_between_the_head_and_the_chain_survives_the_fold"]),

    # half a chain lifted leaves an item that reads as repaired and is not
    ("review#3 the fold lifts half a chain, leaving a marker off the first line",
     '    if markers("\\n".join(kept)):\n        return None, FOLD_SPLIT_REFUSAL',
     '    if False:\n        return None, FOLD_SPLIT_REFUSAL',
     ["TestFoldKeepsTheItemsMarkdown."
      "test_a_marker_stranded_on_a_BLOCK_line_is_left_and_REPORTED"]),

    # the report gained a second reason, and a reader repairs the shape the
    # sentence names — melted into one line it sends them after the wrong thing
    ("review#3 both refusals are reported under the same reason",
     "        grouped.setdefault(why, []).append(label)",
     "        grouped.setdefault(FOLD_REFUSAL, []).append(label)",
     ["TestFoldKeepsTheItemsMarkdown.test_the_two_refusals_are_reported_under_their_OWN_reasons",
      "TestFoldKeepsTheItemsMarkdown."
      "test_a_marker_stranded_on_a_BLOCK_line_is_left_and_REPORTED"]),

    # --- review#3: T000 is an ID -------------------------------------------
    # the mark is guarded `is not None` because `dup` IS the id, and 0 is falsy.
    # Correct since it was written, and untested: T000 appeared nowhere in the
    # suite, so the truthy spelling left all 9 tests of the owning classes green
    ("review#3 the duplicate mark is dropped for the one ID that is falsy (T000)",
     '            + (f"  [{AMBIGUOUS_MARK % dup}]" if dup is not None else ""))',
     '            + (f"  [{AMBIGUOUS_MARK % dup}]" if dup else ""))',
     ["TestTheZeroIdIsStillAnId.test_two_items_under_T000_are_both_marked_as_duplicates"]),

    ("T122 a briefing is written for an item that is not open (an orphan at birth)",
     "    content, block, start = find_open_item(memdir, args.id)\n    values = {dest:",
     '    content, block, start = "", "", 0\n    values = {dest:',
     ["TestHandoffCreation.test_an_item_that_is_not_open_gets_no_briefing"]),

    # --- T121: the NAME an item gets back is read off its own block ---------
    # `int("0001") == 1`, so a label rebuilt from the number typed is the label of
    # a DIFFERENT item. Each entry below puts one command's re-rendering back.

    ("T121 the done-log LINE records a re-rendered ID (the durable record)",
     '    line = f"- {today} — {marker} — {label} {text} — {outcome}"',
     '    line = f"- {today} — {marker} — T{args.id:03d} {text} — {outcome}"',
     ["TestResolvedItemKeepsItsOwnSpelling.test_the_done_log_records_the_item_under_its_own_spelling",
      "TestResolvedItemKeepsItsOwnSpelling.test_cancel_writes_the_same_name_into_the_log"]),

    ("T121 done/cancel name the item by the number typed, not by the block",
     "    label = item_label(block)\n"
     "    ensure_single_line(outcome=outcome, summary=args.summary)",
     '    label = f"T{args.id:03d}"\n'
     "    ensure_single_line(outcome=outcome, summary=args.summary)",
     ["TestResolvedItemKeepsItsOwnSpelling.test_the_done_log_records_the_item_under_its_own_spelling",
      "TestResolvedItemKeepsItsOwnSpelling.test_cancel_writes_the_same_name_into_the_log"]),

    # the refusal that HANDS OVER A COMMAND: a remedy addressed to T001 while the
    # item is T0001 rewrites another item, and --text eats its prose
    ("T121 the claim refusal names a re-rendered ID in the remedy it prints",
     '    label = item_label(block)\n    head = (f"{label} cannot hold a claim',
     '    label = f"T{item_id(block):03d}"\n    head = (f"{label} cannot hold a claim',
     ["TestResolvedItemKeepsItsOwnSpelling.test_the_refusal_names_the_item_and_its_remedy_addresses_that_item",
      "TestResolvedItemKeepsItsOwnSpelling.test_the_old_remedy_was_a_command_about_a_DIFFERENT_open_item"]),

    ("T121 the ambiguous and stray claim refusals name a re-rendered ID",
     '    label = item_label(block)\n    segs, markers = qualified_fields(block, "Claimed")',
     '    label = f"T{item_id(block):03d}"\n'
     '    segs, markers = qualified_fields(block, "Claimed")',
     ["TestResolvedItemKeepsItsOwnSpelling.test_the_ambiguous_and_stray_claim_refusals_name_the_item"]),

    ("T121 edit reports a re-rendered ID",
     "    label = item_label(block)\n    ensure_single_line(text=args.text",
     '    label = f"T{args.id:03d}"\n    ensure_single_line(text=args.text',
     ["TestResolvedItemKeepsItsOwnSpelling.test_edit_reports_the_item_it_rewrote"]),

    ("T121 claim reports a re-rendered ID",
     "    label = item_label(block)\n    held = claim_segment(block)",
     '    label = f"T{args.id:03d}"\n    held = claim_segment(block)',
     ["TestResolvedItemKeepsItsOwnSpelling.test_claim_release_and_bump_name_the_item_they_touched"]),

    ("T121 release reports a re-rendered ID",
     "    label = item_label(block)\n    # No host check here",
     '    label = f"T{args.id:03d}"\n    # No host check here',
     ["TestResolvedItemKeepsItsOwnSpelling.test_claim_release_and_bump_name_the_item_they_touched"]),

    ("T121 bump reports a re-rendered ID",
     '    label = item_label(block)\n    path = os.path.join(memdir, "next-steps.md")',
     '    label = f"T{args.id:03d}"\n'
     '    path = os.path.join(memdir, "next-steps.md")',
     ["TestResolvedItemKeepsItsOwnSpelling.test_claim_release_and_bump_name_the_item_they_touched"]),

    ("T121 the deferral gate names a re-rendered ID",
     "    label = item_label(block)\n    setting = args.deferred is not None",
     '    label = f"T{args.id:03d}"\n    setting = args.deferred is not None',
     ["TestResolvedItemKeepsItsOwnSpelling.test_the_deferral_refusal_names_the_item"]),

    # the one branch of missing_item_message that HAS a block: `migrate` moves a
    # ticked line VERBATIM, so the log will carry that spelling and no other
    ("T121 the already-ticked branch names a re-rendered ID",
     '            return (f"{item_label(text)} is in next-steps.md but already ticked [x]',
     '            return (f"{label} is in next-steps.md but already ticked [x]',
     ["TestResolvedItemKeepsItsOwnSpelling.test_an_item_already_ticked_is_named_by_its_own_spelling"]),
    # --- review#4: the classifier's DEFAULT was the destructive direction ---
    # The enumeration was the whole guard and its default was ABSORB, so every
    # shape not on it reproduced the flattening — and the structure readback
    # re-asked the enumeration's own question, so it agreed. Each entry below puts
    # back one arm of the repair.

    # the audit itself: with it off, the shape reading is again the only vote, and
    # a shape nobody enumerated is absorbed exactly as before
    ("review#4 an unrecognised shape is absorbed again (the absorption audit is off)",
     "    refusal = absorption_audit(lines, j)\n    if refusal:\n        return None, refusal",
     "    refusal = None\n    if refusal:\n        return None, refusal",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated.test_a_shape_no_one_enumerated_is_REFUSED_and_not_flattened",
      "TestFoldFailsSafeOnShapesNobodyEnumerated.test_a_shape_no_one_enumerated_that_OPENS_like_prose_is_refused_too",
      "TestFoldFailsSafeOnShapesNobodyEnumerated.test_the_two_verdicts_land_in_ONE_run_without_touching_each_other"]),

    # the geometry arm alone: every break becomes wide enough, so a line the
    # author chose to break reads as one a wrapper made
    # the named test CHANGED with T168, and the harness is why: METADATA_LINE_RE
    # began refusing the `chave: valor` fixture on its own, so the old test passed
    # with the geometry switched off and this entry reported SURVIVED. Two guards
    # over one incident, the second masking the first. The fixture named now is
    # reached by no rule but geometry
    ("review#4 the geometry stops distinguishing an author's break from a wrapper's",
     "WRAP_COLUMN_FLOOR = 72", "WRAP_COLUMN_FLOOR = 0",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated."
      "test_the_GEOMETRY_alone_refuses_a_line_no_other_rule_reaches"]),

    # the opening arm alone: `!!!` opens like a sentence again
    ("review#4 any character may open a hard-wrapped line",
     "        if not (opener.isalnum() or opener in PROSE_OPENERS\n"
     '                or unicodedata.category(opener) == "So"):\n'
     "            return FOLD_PROSE_REFUSAL",
     "        if False:\n            return FOLD_PROSE_REFUSAL",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated.test_a_shape_no_one_enumerated_is_REFUSED_and_not_flattened",
      "TestFoldFailsSafeOnShapesNobodyEnumerated.test_the_two_verdicts_land_in_ONE_run_without_touching_each_other"]),

    # T168 — the metadata arm, switched off: `chave: valor` under a FULL line is
    # licensed by geometry and by its letter opener, so with this rule gone the
    # line is joined into the head and the item reported as folded
    ("T168 a `chave: valor` line is hard-wrapped prose again",
     "        if METADATA_LINE_RE.match(stripped) and len(stripped) <= WRAP_COLUMN_FLOOR:\n"
     "            return FOLD_PROSE_REFUSAL",
     "        if False:\n            return FOLD_PROSE_REFUSAL",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated."
      "test_a_metadata_line_under_a_FULL_line_is_refused_and_not_flattened"]),

    # and from the over-refusal side: drop what must follow the colon, and a URL
    # or a clock time inside a wrapped sentence reads as a metadata key
    ("T168 the metadata rule stops reading the character after the colon",
     r'METADATA_LINE_RE = re.compile(r"\A[^\W\d_][\w-]{0,31}:(?:[ \t]|\Z)")',
     r'METADATA_LINE_RE = re.compile(r"\A[^\W\d_][\w-]{0,31}:")',
     ["TestFoldFailsSafeOnShapesNobodyEnumerated."
      "test_a_colon_that_prose_really_uses_does_not_trip_the_metadata_rule"]),

    # T168 — the width condition dropped: the SHAPE alone decides again, and a
    # wrapped sentence resuming `wiki: ` at 92 columns is refused as metadata.
    # Measured on a real item before this shipped, not imagined
    ("T168 a word and a colon are enough to call a line metadata",
     "        if METADATA_LINE_RE.match(stripped) and len(stripped) <= WRAP_COLUMN_FLOOR:",
     "        if METADATA_LINE_RE.match(stripped):",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated."
      "test_a_wrapped_line_that_merely_resumes_with_a_word_and_a_colon_is_prose"]),

    # the opening arm, from the other side: an emoji and a wiki link stop reading
    # as prose, and the population the fold exists to serve is refused wholesale
    ("review#4 only a letter or a digit may open a hard-wrapped line",
     "        if not (opener.isalnum() or opener in PROSE_OPENERS\n"
     '                or unicodedata.category(opener) == "So"):',
     "        if not opener.isalnum():",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated.test_the_hard_wrapped_population_is_still_absorbed_whole",
      "TestFoldFailsSafeOnShapesNobodyEnumerated.test_the_two_verdicts_land_in_ONE_run_without_touching_each_other"]),

    # one shape per entry, because each is a separate reading of the corpus and a
    # separate way to be wrong. The setext arm degrades to a REFUSAL rather than a
    # flattening — the layered default working — and the fold-around is still lost
    ("review#4 a setext underline is a paragraph continuation again",
     "    if SETEXT_UNDERLINE_RE.match(stripped) or REFERENCE_DEF_RE.match(stripped):",
     "    if REFERENCE_DEF_RE.match(stripped):",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated.test_each_shape_the_join_used_to_flatten_keeps_its_own_lines"]),

    # this one really is flattened: `[` opens prose in the real queues (a wiki
    # link), so no other arm catches a link reference or a footnote definition
    ("review#4 a link reference and a footnote definition are prose again",
     "    if SETEXT_UNDERLINE_RE.match(stripped) or REFERENCE_DEF_RE.match(stripped):",
     "    if SETEXT_UNDERLINE_RE.match(stripped):",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated.test_each_shape_the_join_used_to_flatten_keeps_its_own_lines"]),

    # and this one too: a table head row opens with a letter like any sentence,
    # and only the delimiter row BELOW it says otherwise
    ("review#4 a table head row without a leading pipe is prose again",
     '    return "|" in stripped and bool(TABLE_DELIMITER_RE.match(nxt.strip()))',
     "    return False",
     ["TestFoldFailsSafeOnShapesNobodyEnumerated.test_each_shape_the_join_used_to_flatten_keeps_its_own_lines",
      "TestFoldFailsSafeOnShapesNobodyEnumerated.test_the_gates_reach_an_item_folded_around_a_table_written_without_pipes"]),

    # the lookahead is what makes the rule a TABLE rule and not a "line with a
    # pipe" rule: without it a sentence carrying a pipe stops being prose
    ("review#4 any line with a pipe in it opens a table",
     '    return "|" in stripped and bool(TABLE_DELIMITER_RE.match(nxt.strip()))',
     '    return "|" in stripped',
     ["TestFoldFailsSafeOnShapesNobodyEnumerated."
      "test_a_wrapped_sentence_that_merely_carries_a_pipe_is_not_a_table"]),

    # --- review#4: a field appended to a class-less item reaches no reader --
    ("review#4 a field is appended where the position rule can never read it",
     '            if field != "Class" and not real_fields(new, "Class"):\n                fail(f"{label} names no **Class:** in its field chain, so an appended "',
     '            if False:\n                fail(f"{label} names no **Class:** in its field chain, so an appended "',
     ["TestAFieldAppendedBeforeTheAnchorIsRefused.test_setting_a_field_on_a_class_less_item_is_refused",
      "TestAFieldAppendedBeforeTheAnchorIsRefused.test_the_file_and_the_reader_no_longer_disagree_about_the_field",
      "TestAFieldAppendedBeforeTheAnchorIsRefused.test_every_field_that_is_APPENDED_is_covered_not_only_effort",
      "TestAFieldAppendedBeforeTheAnchorIsRefused.test_the_remedy_the_refusal_PRINTS_runs_and_lets_the_field_through"]),

    # the exemption --class depends on: it is the flag that GIVES the anchor, and
    # a rule that refused it would lock the repair out of its own population
    ("review#4 the rule swallows --class, the one flag that gives the anchor",
     '            if field != "Class" and not real_fields(new, "Class"):\n                fail(f"{label} names no **Class:** in its field chain, so an appended "',
     '            if not real_fields(new, "Class"):\n                fail(f"{label} names no **Class:** in its field chain, so an appended "',
     ["TestAFieldAppendedBeforeTheAnchorIsRefused.test_class_first_in_ONE_call_lands_the_field_inside_the_chain",
      "TestAFieldAppendedBeforeTheAnchorIsRefused.test_the_remedy_the_refusal_PRINTS_runs_and_lets_the_field_through"]),

    # --- T169: where the class anchor LANDS ---------------------------------
    # The anchor is what real_fields measures from, so writing it at the end of
    # the line strands every field already there. Each entry below is one of the
    # positions that shipped or was tried, and the tests read the FILE.
    ("T169 the class goes back to the END of the line, behind the fields already there",
     "    item.insert_field(0, segment)\n    return render_item(item), promoted",
     "    item.append_field(segment)\n    return render_item(item), promoted",
     ["TestTheClassLandsAheadOfTheChain.test_the_anchor_goes_ahead_of_the_fields_already_on_the_line",
      "TestTheClassLandsAheadOfTheChain.test_the_repaired_item_is_what_add_would_have_written",
      "TestTheClassLandsAheadOfTheChain."
      "test_the_whole_trap_from_the_continuation_line_through_packs_own_remedy",
      "TestTheClassLandsAheadOfTheChain.test_a_field_already_on_the_line_is_WRITABLE_after_the_repair",
      "TestAClassLessChainIsNotAField.test_a_class_less_item_can_still_be_GIVEN_a_class"]),

    # "before the LAST field" is the near miss: it reads as ahead of the chain and
    # is not, and everything from the run's head up to it stays unreadable
    ("T169 the class lands after the first field instead of ahead of the run",
     "    item.insert_field(0, segment)", "    item.insert_field(1, segment)",
     ["TestTheClassLandsAheadOfTheChain.test_the_anchor_goes_ahead_of_the_fields_already_on_the_line",
      "TestTheClassLandsAheadOfTheChain.test_the_repaired_item_is_what_add_would_have_written",
      "TestTheClassLandsAheadOfTheChain.test_a_field_already_on_the_line_is_WRITABLE_after_the_repair"]),

    # the period is what tells a field segment from prose, so a class written
    # without one breaks the chain AT the anchor — the readback is what refuses it
    ("T169 the class segment is written without its period",
     '    segment = f"**Class:** {value}."', '    segment = f"**Class:** {value}"',
     ["TestTheClassLandsAheadOfTheChain.test_the_anchor_goes_ahead_of_the_fields_already_on_the_line",
      "TestTheClassLandsAheadOfTheChain.test_the_repaired_item_is_what_add_would_have_written"]),

    # an item with nothing on the line has nothing to sit ahead of: the over-refusal
    # direction, and the population --class was written for
    ("T169 an item with no chain gets its class inserted at the head of an empty run",
     "    if not item.fields:\n"
     "        return append_to_first_line(block, segment), []",
     "    if False:\n"
     "        return append_to_first_line(block, segment), []",
     ["TestTheClassLandsAheadOfTheChain.test_an_item_with_no_chain_still_gets_its_class_APPENDED",
      "TestAFieldAppendedBeforeTheAnchorIsRefused."
      "test_the_remedy_the_refusal_PRINTS_runs_and_lets_the_field_through"]),

    # --- T169 review: the file the readback keeps out of existence ------------
    # The three entries above all exit 1 on cmd_edit's readback, so the FILE their
    # tests assert against is never written and what they prove is the GATE. Paired
    # with the readback relaxed to a set comparison — which is exactly the
    # relaxation a later reader would call harmless — the write lands and the file
    # assertions are what kill. That pairing is also the only thing that makes the
    # readback's own EXACTNESS load-bearing: relaxed on its own, behind a correct
    # writer, nothing falls.
    ("T169 the class at the END of the line, with the readback relaxed to a set",
     ["    item.insert_field(0, segment)\n    return render_item(item), promoted",
      '                if back != ["Class"] + promoted or chain_class(candidate) != flag:'],
     ["    item.append_field(segment)\n    return render_item(item), promoted",
      '                if sorted(back) != sorted(["Class"] + promoted) '
      'or chain_class(candidate) != flag:'],
     ["TestTheClassLandsAheadOfTheChain.test_the_anchor_goes_ahead_of_the_fields_already_on_the_line",
      "TestTheClassLandsAheadOfTheChain."
      "test_the_anchor_lands_where_add_puts_it_and_the_item_is_not_identical",
      "TestTheClassLandsAheadOfTheChain.test_a_field_already_on_the_line_is_WRITABLE_after_the_repair"]),

    ("T169 the class after the first field, with the readback relaxed to a set",
     ["    item.insert_field(0, segment)",
      '                if back != ["Class"] + promoted or chain_class(candidate) != flag:'],
     ["    item.insert_field(1, segment)",
      '                if sorted(back) != sorted(["Class"] + promoted) '
      'or chain_class(candidate) != flag:'],
     ["TestTheClassLandsAheadOfTheChain.test_the_anchor_goes_ahead_of_the_fields_already_on_the_line",
      "TestTheClassLandsAheadOfTheChain."
      "test_the_anchor_lands_where_add_puts_it_and_the_item_is_not_identical",
      "TestTheClassLandsAheadOfTheChain.test_a_field_already_on_the_line_is_WRITABLE_after_the_repair"]),

    # --- T169 review CRITICAL: the anchor promotes, the same call destroys ----
    # Every segment the anchor makes readable is a real field for the rest of the
    # flag loop, so a later flag in the SAME command rewrites it — measured rc 0
    # both ways on one item: `--project tk` overwrote four words of the title,
    # `--risk none` deleted the imitating segment whole.
    ("T169 review: a promoted run is left to the rest of the same call",
     "                if promoted and others:",
     "                if False and promoted and others:",
     ["TestTheClassLandsAheadOfTheChain.test_a_promotion_ENDS_the_call_instead_of_feeding_the_next_flag",
      "TestTheClassLandsAheadOfTheChain.test_the_refusals_remedy_runs_and_the_two_commands_land_the_field"]),

    # the over-refusal direction: the class ALONE is what repairs this population,
    # so a rule that refused it would lock the repair out of its own items
    ("T169 review: the refusal swallows `--class` on its own",
     "                if promoted and others:",
     "                if promoted:",
     ["TestTheClassLandsAheadOfTheChain.test_the_class_alone_is_still_taken_by_the_same_item",
      "TestTheClassLandsAheadOfTheChain.test_the_promotion_is_ANNOUNCED_and_names_the_segments"]),

    # --- T169 review HIGH: the fold has to come before the class -------------
    # With no chain on the first line the anchor is APPENDED there, the item's real
    # fields stay on the continuation line, and the anchor then stops `migrate`
    # from folding them — `pack` printed the class as the repair and listed the
    # item eligible with Effort `?` afterwards.
    ("T169 review: the class is written on an item whose fields are off the line",
     "                if fields_off_first_line(new):",
     "                if False:",
     ["TestTheClassLandsAheadOfTheChain.test_a_class_less_item_still_UNFOLDED_is_refused_and_told_the_order",
      "TestTheClassLandsAheadOfTheChain.test_an_item_whose_note_merely_QUOTES_a_marker_is_covered_too"]),

    # a remedy printed for the wrong shape is a dead end printed as an answer, and
    # this list's whole reason for existing is that a skill reads it and runs it
    ("T169 review: pack prints the class repair before the fold",
     "        if fields_off_first_line(block):\n"
     '            return ("no **Class:** field, and its fields sit off the first line",\n'
     "                    REPAIR_FOLD_THEN_CLASS)",
     "        if False:\n"
     '            return ("no **Class:** field, and its fields sit off the first line",\n'
     "                    REPAIR_FOLD_THEN_CLASS)",
     ["TestTheClassLandsAheadOfTheChain.test_a_class_less_item_still_UNFOLDED_is_refused_and_told_the_order"]),

    ("T169 review: the claim's diagnosis prescribes a class that is refused",
     "        if fields_off_first_line(block):\n"
     "            # the class alone is REFUSED on this item (cmd_edit), and it would be",
     "        if False:\n"
     "            # the class alone is REFUSED on this item (cmd_edit), and it would be",
     ["TestTheClassLandsAheadOfTheChain.test_the_claims_diagnosis_names_the_fold_before_the_class"]),

    # compose, check, act — the order the rest of this file keeps. Printed ahead of
    # the write, the warning announced a promotion `check_ceiling` then refused.
    # The write itself STAYS: a mutation that deleted the splice would redden the
    # whole class and prove nothing about the ORDER, which is the rule here
    ("T169 review: the promotion warning goes back ahead of the write",
     "                new = candidate\n"
     "                promoted_names = promoted\n"
     "                continue",
     "                new = candidate\n"
     "                promoted_names = promoted\n"
     "                if promoted:\n"
     '                    names = ", ".join(f"**{n}:**" for n in promoted)\n'
     '                    print(f"tk-queue: warning: {label} already ended its first "\n'
     '                          f"line with {names}, so the class went AHEAD of that "\n'
     '                          "run.", file=sys.stderr)\n'
     "                continue",
     ["TestTheClassLandsAheadOfTheChain.test_the_promotion_warning_waits_for_the_write_to_commit"]),

    # the promotion is the PRICE of the position, and a price nobody is told about
    # is the silence this slice was opened to close
    ("T169 the segments the anchor promoted go unannounced",
     "    if promoted_names:\n"
     '        names = ", ".join(f"**{n}:**" for n in promoted_names)',
     "    if False:\n"
     '        names = ", ".join(f"**{n}:**" for n in promoted_names)',
     ["TestTheClassLandsAheadOfTheChain.test_the_promotion_is_ANNOUNCED_and_names_the_segments"]),

    # --- review#5: the setext protection only looked at the underline -------
    # The underline was kept and the TITLE above it — which the underline
    # retroactively makes a heading — was absorbed, so the item came out with its
    # heading text merged into unrelated prose and the underline orphaned. The
    # repair is the table-head lookahead read from the other side.
    ("review#5 the line a setext underline promotes is prose again",
     "    if SETEXT_UNDERLINE_RE.match(nxt.strip()):\n"
     "        return True                      # this line is the heading that underlines",
     "    if False:\n"
     "        return True                      # this line is the heading that underlines",
     ["TestASetextTitleIsKeptWithItsUnderline."
      "test_the_title_the_underline_promotes_keeps_its_own_line",
      "TestASetextTitleIsKeptWithItsUnderline."
      "test_the_gates_reach_the_item_folded_around_the_heading"]),

    # the over-refusal direction, which the arm above cannot reach: what makes
    # this a SETEXT rule and not a "there is a line below" rule is the shape of
    # that line. Without it every wrapped sentence stops being absorbed, and the
    # fold loses the population it exists for
    ("review#5 any non-blank line below makes this one a heading",
     "    if SETEXT_UNDERLINE_RE.match(nxt.strip()):",
     "    if nxt.strip():",
     ["TestASetextTitleIsKeptWithItsUnderline."
      "test_an_ordinary_hard_wrapped_line_is_STILL_absorbed",
      "TestASetextTitleIsKeptWithItsUnderline."
      "test_the_whole_hard_wrapped_population_is_still_absorbed_whole",
      "TestFoldFailsSafeOnShapesNobodyEnumerated."
      "test_the_hard_wrapped_population_is_still_absorbed_whole"]),

    # --- review#5: `--<field> none` on a class-less item printed success -----
    ("review#5 a clear on a class-less item reports success and writes nothing",
     '            if not real_fields(new, "Class"):\n'
     '                fail(f"{label} names no **Class:** in its field chain, so no segment of "',
     '            if False:\n'
     '                fail(f"{label} names no **Class:** in its field chain, so no segment of "',
     ["TestClearingOnAClassLessItemIsRefused.test_every_clearable_flag_is_refused_and_says_so",
      "TestClearingOnAClassLessItemIsRefused."
      "test_the_remedy_the_refusal_PRINTS_runs_and_leaves_the_item_anchored"]),

    # the over-refusal direction: a rule that reached the ANCHORED item would take
    # the clearing command away from every item `add` ever wrote
    ("review#5 the clear is refused on every item, anchored or not",
     '            if not real_fields(new, "Class"):',
     "            if True:",
     ["TestClearingOnAClassLessItemIsRefused.test_an_anchored_item_still_CLEARS_the_field_it_carries",
      "TestRiskDeletion.test_edit_clears_the_risk_field",
      "TestClearingKeepsTheFileIntact.test_clearing_a_risk_rewrites_only_that_field"]),
    # --- T172: provenance fields, and the lane the package reads from them ---
    ("T172 the ref shape loosens to a prefix match (\"repo#1x\" is accepted)",
     '    if not REF_RE.fullmatch(value):\n        fail(f"--{flag} {value!r} is not a forge',
     '    if not REF_RE.match(value):\n        fail(f"--{flag} {value!r} is not a forge',
     ["TestProvenanceFields.test_a_value_outside_the_ref_shape_is_refused"]),

    ("T172 the ref shape is not checked at all",
     '    args.ticket = validate_ref("ticket", args.ticket)\n'
     '    args.spec = validate_ref("spec", args.spec)',
     "    pass",
     ["TestProvenanceFields.test_a_value_outside_the_ref_shape_is_refused"]),

    ("T172 the two fields are dropped on the way into the item",
     '    for flag, field in ((args.ticket, "Ticket"), (args.spec, "Spec"),\n'
     '                        (args.repo, "Repo")):\n'
     '        if flag:\n'
     '            fields.append(f"**{field}:** {flag}.")',
     "    pass",
     ["TestProvenanceFields.test_both_fields_are_written_at_the_writers_position",
      "TestProvenanceFields.test_the_values_round_trip_byte_for_byte",
      "TestProvenanceFields.test_the_flags_are_independent"]),

    # the OTHER direction of the same writer: a field written whether or not the
    # caller asked for one gives every item a provenance nobody recorded
    ("T172 an absent flag writes the field anyway",
     "        if flag:\n"
     '            fields.append(f"**{field}:** {flag}.")',
     '        fields.append(f"**{field}:** {flag}.")',
     ["TestProvenanceFields.test_an_add_without_the_flags_writes_the_item_of_today",
      "TestProvenanceFields.test_the_flags_are_independent"]),

    # --- T300: the lane address is the one field of the group an edit rewrites ---
    ("T300 the spec flag leaves the edit loop, so it writes nothing",
     '             (args.project, "Project"), (deferred_flag, "Deferred"),',
     '             (args.project, "Project"), (deferred_flag, "Deferred"))\n    _ = (',
     ["TestTheSpecIsTheOneEditableFieldOfItsGroup."
      "test_the_field_is_written_on_an_item_that_carried_none",
      "TestTheSpecIsTheOneEditableFieldOfItsGroup."
      "test_the_field_is_REWRITTEN_and_the_old_value_is_gone",
      "TestTheSpecIsTheOneEditableFieldOfItsGroup."
      "test_the_value_is_stored_in_the_one_spelling"]),

    ("T300 the edit door stores the caller's own spelling, ungated",
     '    args.spec = validate_ref("spec", args.spec)\n'
     "    new = block",
     "    new = block",
     ["TestTheSpecIsTheOneEditableFieldOfItsGroup."
      "test_a_value_outside_the_ref_shape_is_refused_and_writes_nothing",
      "TestTheSpecIsTheOneEditableFieldOfItsGroup."
      "test_the_value_is_stored_in_the_one_spelling"]),

    # over-trigger direction: the relaxation spreads to the fields it was
    # deliberately NOT granted to, and a ticket re-pointed at another issue is
    # the work of another issue
    ("T300 the relaxation spreads to Ticket, which is provenance and add-only",
     '    e.add_argument("--project", help="assign/change the project tag")\n',
     '    e.add_argument("--project", help="assign/change the project tag")\n'
     '    e.add_argument("--ticket")\n',
     ["TestTheSpecIsTheOneEditableFieldOfItsGroup."
      "test_the_other_two_fields_of_the_group_still_have_no_flag"]),

    ("T172 the lane column leaves the package listing",
     '            eligible.append(f"{label}  {pack_effort(text):<12}  "\n'
     '                            f"{lanes[n]:<20}  {item_title(text)}"',
     '            eligible.append(f"{label}  {pack_effort(text):<12}  {item_title(text)}"',
     ["TestPackLane.test_an_item_with_no_spec_is_avulso",
      "TestPackLane.test_two_tickets_of_one_spec_share_the_accumulated_lane",
      "TestPack.test_an_eligible_item_carries_its_id_effort_and_text",
      "TestPack.test_the_documented_sample_IS_what_the_command_prints"]),

    # RE-ANCHORED by T271, which moved this rule: `next()` over the queue's
    # order became `max()` over the ticket count, so the direction this entry
    # switches is no longer "the first ticket" but the TIE-BREAK — the half of
    # the old rule that survived the rewrite
    ("T271 a tie goes to the LAST spec in queue order instead of the first",
     "    taken = max(contenders, key=lambda ref: tickets[ref], default=None)",
     "    taken = max(reversed(contenders), key=lambda ref: tickets[ref], default=None)",
     ["TestPackLane.test_a_TIE_on_ticket_count_is_broken_by_QUEUE_ORDER"]),

    ("T172 the floor goes, so a lone spec becomes a SECOND lane and is excluded",
     "        elif ref is not None and tickets[ref] >= SPEC_LANE_FLOOR:",
     "        elif ref is not None and tickets[ref] >= 1:",
     ["TestPackLane.test_no_spec_reaching_the_floor_leaves_every_ticket_avulso",
      "TestPackLane.test_a_spec_under_the_floor_does_not_take_the_lane_it_cannot_use"]),

    # the floor turned into a FILTER — the direction that drops the lone ticket
    # out of a package it belongs in, which is what "lane, not exclusion" names
    ("T172 no ticket ever reaches the accumulated lane",
     "        elif ref is not None and ref == taken:\n"
     "            lanes[n] = LANE_SPEC % taken",
     "        elif False:\n"
     "            lanes[n] = LANE_SPEC % taken",
     ["TestPackLane.test_two_tickets_of_one_spec_share_the_accumulated_lane",
      "TestPackLane.test_the_documented_sample_IS_what_the_command_prints"]),

    ("T172 a second spec keeps a lane of its own instead of leaving the package",
     "            pushed[n] = LANE_TAKEN % (taken, ref)",
     "            lanes[n] = LANE_SPEC % ref",
     ["TestPackLane.test_tickets_of_a_SECOND_spec_leave_with_the_exact_reason",
      "TestPackLane.test_a_TIE_on_ticket_count_is_broken_by_QUEUE_ORDER",
      "TestPackLane.test_the_documented_sample_IS_what_the_command_prints"]),

    # The test this named before T271 stopped falling for it, and the entry was
    # VACUOUS for one run: with the lane going to the deepest spec, dropping the
    # floor here still elects the two-ticket spec over the lone one, so the case
    # that put a lone FIRST spec against a fuller second one no longer separates
    # the two readings. The queue that does is the one where NO spec reaches the
    # floor — there `max()` hands the lane to a spec that may not hold one.
    ("T172 the lane goes to any spec that has a ticket, floor or no floor",
     "    contenders = [ref for _, ref in specs\n"
     "                  if ref is not None and ref not in under_way\n"
     "                  and tickets[ref] >= SPEC_LANE_FLOOR]",
     "    contenders = [ref for _, ref in specs\n"
     "                  if ref is not None and ref not in under_way]",
     ["TestPackLane.test_no_spec_reaching_the_floor_leaves_every_ticket_avulso"]),

    ("T172 the lane is decided over EVERY item, not the candidates only",
     "    lanes, pushed = pack_lanes(candidates, under_way)",
     "    lanes, pushed = pack_lanes([(l, t) for l, t, _ in rows], under_way)",
     ["TestPackLane.test_the_lane_is_decided_among_ELIGIBLE_items_only"]),

    # --- T249: the election has to know which spec is already being worked ---
    # Five guards, and each one measured a package that ran with no accumulated
    # lane while a second spec sat ready. The rung they defend is the same one
    # T172 wrote; what is new is the SOURCE of the fact — the caller's remote
    # check, which this command cannot make for itself.
    ("T249 the election ignores the specs the caller reported under way",
     "    contenders = [ref for _, ref in specs\n"
     "                  if ref is not None and ref not in under_way\n"
     "                  and tickets[ref] >= SPEC_LANE_FLOOR]",
     "    contenders = [ref for _, ref in specs\n"
     "                  if ref is not None\n"
     "                  and tickets[ref] >= SPEC_LANE_FLOOR]",
     ["TestPackLaneUnderWay.test_the_named_spec_loses_the_lane_and_the_next_one_takes_it"]),

    ("T249 a spec under way keeps its tickets in the package",
     "        if ref is not None and ref in under_way:\n"
     "            pushed[n] = LANE_UNDER_WAY % ref",
     "        if False:\n"
     "            pushed[n] = LANE_UNDER_WAY % ref",
     ["TestPackLaneUnderWay.test_the_named_spec_loses_the_lane_and_the_next_one_takes_it",
      "TestPackLaneUnderWay.test_a_lone_ticket_of_a_spec_under_way_leaves_TOO"]),

    # the floor read as a shield: under it the ticket goes out `avulso (<ref>)`,
    # which is the second pull request over the open branch's own work
    ("T249 the floor shields a lone ticket of a spec under way",
     "        if ref is not None and ref in under_way:",
     "        if ref is not None and ref in under_way and tickets[ref] >= SPEC_LANE_FLOOR:",
     ["TestPackLaneUnderWay.test_a_lone_ticket_of_a_spec_under_way_leaves_TOO",
      "TestPackLaneUnderWay.test_the_two_rungs_are_told_apart_by_their_value"]),

    ("T249 the rung stops saying WHICH source excluded the ticket",
     "            pushed[n] = LANE_UNDER_WAY % ref",
     "            pushed[n] = LANE_TAKEN % (ref, ref)",
     ["TestPackLaneUnderWay.test_the_named_spec_loses_the_lane_and_the_next_one_takes_it",
      "TestPackLaneUnderWay.test_the_two_rungs_are_told_apart_by_their_value"]),

    ("T249 the flag never reaches the election",
     "    lanes, pushed = pack_lanes(candidates, under_way)",
     "    lanes, pushed = pack_lanes(candidates)",
     ["TestPackLaneUnderWay.test_the_named_spec_loses_the_lane_and_the_next_one_takes_it",
      "TestPackLaneUnderWay.test_a_lone_ticket_of_a_spec_under_way_leaves_TOO"]),

    ("T249 the flag value is neither shape-checked nor canonicalised",
     '    under_way = frozenset(validate_ref("spec-under-way", v)\n'
     '                          for v in (args.spec_under_way or []))',
     "    under_way = frozenset(v\n"
     "                          for v in (args.spec_under_way or []))",
     ["TestPackLaneUnderWay.test_a_malformed_value_is_refused_the_way_spec_refuses_one",
      "TestPackLaneUnderWay.test_the_value_is_read_in_the_ONE_canonical_spelling"]),

    ("T249 only the LAST --spec-under-way counts, so the flag stops repeating",
     '    under_way = frozenset(validate_ref("spec-under-way", v)\n'
     '                          for v in (args.spec_under_way or []))',
     '    under_way = frozenset(validate_ref("spec-under-way", v)\n'
     "                          for v in (args.spec_under_way or [])[-1:])",
     ["TestPackLaneUnderWay.test_every_spec_under_way_leaves_a_package_of_avulsos"]),


    # --- T271: the deepest spec takes the lane, and the blocked ticket goes --
    ("T271 the lane goes to the first spec in order again, however few tickets",
     "    taken = max(contenders, key=lambda ref: tickets[ref], default=None)",
     "    taken = contenders[0] if contenders else None",
     ["TestPackLane.test_the_lane_goes_to_the_spec_with_the_MOST_tickets"]),

    ("T271 the lane goes to the SHALLOWEST spec",
     "    taken = max(contenders, key=lambda ref: tickets[ref], default=None)",
     "    taken = min(contenders, key=lambda ref: tickets[ref], default=None)",
     ["TestPackLane.test_the_lane_goes_to_the_spec_with_the_MOST_tickets"]),

    ("T271 the ticket the caller reported blocked stays in the package",
     '    ref = pack_ref(block, "Ticket") if blocked else None\n'
     "    if ref is not None and ref in blocked:",
     '    ref = pack_ref(block, "Ticket") if blocked else None\n'
     "    if False:",
     ["TestPackBlockedTicket.test_the_named_ticket_leaves_the_package_with_the_reason",
      "TestPackBlockedTicket.test_the_blocked_ticket_leaves_its_specs_COUNT_too"]),

    ("T271 the flag never reaches the ladder",
     "        verdict = pack_exclusion(iid, text, identity, open_ids, blocked)",
     "        verdict = pack_exclusion(iid, text, identity, open_ids)",
     ["TestPackBlockedTicket.test_the_named_ticket_leaves_the_package_with_the_reason",
      "TestPackBlockedTicket.test_the_blocked_ticket_leaves_its_specs_COUNT_too"]),

    ("T271 the flag value is neither shape-checked nor canonicalised",
     '    blocked = frozenset(validate_ref("blocked", v) for v in (args.blocked or []))',
     "    blocked = frozenset(v for v in (args.blocked or []))",
     ["TestPackBlockedTicket.test_a_malformed_value_is_refused_the_way_spec_refuses_one",
      "TestPackBlockedTicket.test_the_value_is_read_in_the_ONE_canonical_spelling"]),

    ("T271 only the LAST --blocked counts, so the flag stops repeating",
     '    blocked = frozenset(validate_ref("blocked", v) for v in (args.blocked or []))',
     '    blocked = frozenset(validate_ref("blocked", v) for v in (args.blocked or [])[-1:])',
     ["TestPackBlockedTicket.test_the_flag_repeats"]),

    ("T271 the reason stops naming the source of the fact",
     'TICKET_BLOCKED = "ticket %s is blocked on the forge; declared by --blocked"',
     'TICKET_BLOCKED = "ticket %s is blocked"',
     ["TestPackBlockedTicket.test_the_named_ticket_leaves_the_package_with_the_reason",
      "TestPackBlockedTicket.test_the_blocked_ticket_leaves_its_specs_COUNT_too"]),

    # the three over-trigger directions, each one a package emptied instead of
    # a ticket taken out of it
    ("T271 every item carrying a ticket leaves, named or not",
     "    if ref is not None and ref in blocked:",
     "    if ref is not None:",
     ["TestPackBlockedTicket.test_the_named_ticket_leaves_the_package_with_the_reason"]),

    ("T271 the rung reads the flag inverted, so every ticket NOT named leaves",
     '    ref = pack_ref(block, "Ticket") if blocked else None\n'
     "    if ref is not None and ref in blocked:",
     '    ref = pack_ref(block, "Ticket")\n'
     "    if ref is not None and ref not in blocked:",
     ["TestPackBlockedTicket.test_the_run_with_no_flag_is_what_it_has_always_been"]),

    ("T271 a **Ticket:** no reader may use costs the item its place",
     "    if ref is not None and ref in blocked:",
     "    if blocked and (ref in blocked or real_fields(block, \"Ticket\")):",
     ["TestPackBlockedTicket."
      "test_a_ticket_the_position_rule_cannot_read_is_not_excluded"]),

    # the prose half: a skill's orchestrator reads the election rule from here
    ("T271 the documented election goes back to queue order",
     "goes to the spec with the MOST tickets among the candidates, ties broken by QUEUE",
     "goes to the FIRST spec in QUEUE ORDER among the candidates, ties broken by QUEUE",
     ["TestPackBlockedTicket.test_the_flag_is_documented_in_the_help_the_skill_reads"]),

    ("T172 a ticket the taken lane pushed out is listed as eligible TOO",
     "        if verdict is None and n not in pushed:",
     "        if verdict is None:",
     ["TestPackLane.test_tickets_of_a_SECOND_spec_leave_with_the_exact_reason"]),

    ("T172 the new field names leave the grammar, so no reader knows them",
     '    "Ticket": r"Ticket",\n    "Spec": r"Spec",',
     "",
     ["TestPackLane.test_two_tickets_of_one_spec_share_the_accumulated_lane"]),

    # the position rule, at the writer's end: a provenance field composed BEFORE
    # the **Class:** the chain anchors at is a field no gate may read — the value
    # is in the file, the lane is not
    ("T172 the provenance fields are composed BEFORE the class they must follow",
     '    for flag, field in ((args.ticket, "Ticket"), (args.spec, "Spec"),\n'
     '                        (args.repo, "Repo")):\n'
     '        if flag:\n'
     '            fields.append(f"**{field}:** {flag}.")',
     '    for flag, field in ((args.ticket, "Ticket"), (args.spec, "Spec"),\n'
     '                        (args.repo, "Repo")):\n'
     '        if flag:\n'
     '            fields.insert(0, f"**{field}:** {flag}.")',
     ["TestProvenanceFields.test_both_fields_are_written_at_the_writers_position"]),
    # --- T172, round 1 of the lens campaign ----------------------------------
    ("T172 the lane is keyed by the LABEL again, which two items can share",
     "            candidates.append((len(rows) - 1, text))",
     "            candidates.append((label, text))",
     ["TestPackLane.test_a_duplicate_ID_never_costs_the_LANE_HOLDER_its_place"]),

    ("T172 the lane names only the issue number, so two repos collapse into one",
     "            lanes[n] = LANE_SPEC % taken",
     '            lanes[n] = LANE_SPEC % ("#" + taken.rpartition("#")[2])',
     ["TestPackLane.test_two_specs_sharing_an_issue_number_are_told_APART",
      "TestPackLane.test_the_documented_sample_IS_what_the_command_prints"]),

    ("T172 the exclusion reason drops this item's own spec",
     "            pushed[n] = LANE_TAKEN % (taken, ref)",
     '            pushed[n] = LANE_TAKEN % (taken.rpartition("#")[2], ref)',
     ["TestPackLane.test_two_specs_sharing_an_issue_number_are_told_APART",
      "TestPackLane.test_tickets_of_a_SECOND_spec_leave_with_the_exact_reason"]),

    ("T172 the ticket the PR closes stops coming back from the command",
     "                            + pack_closes(text) + pack_repo(text))",
     '                            + "" + pack_repo(text))',
     ["TestPackLane.test_the_TICKET_the_PR_closes_comes_back_from_the_command",
      "TestPackLane.test_the_documented_sample_IS_what_the_command_prints"]),

    # the other direction: a Ticket the position rule may not read must stay
    # SILENT — it decides no lane, so it may not cost the item its place
    ("T172 an unreadable Ticket is printed anyway",
     '    return f"  [{ref}]" if ref else "  [?]"',
     '    return f"  [{ref}]" if ref else ""',
     ["TestPackLane.test_a_TICKET_the_position_rule_cannot_read_is_MARKED_not_silent",
      "TestPackLane.test_a_TICKET_that_is_not_a_forge_reference_is_never_printed"]),

    # the position rule, proved THROUGH the one reader — the anchor-free version was
    # measured green against the whole suite before this test existed
    ("T172 the one reader drops the anchor, so prose in the chain is a field",
     "    segs = real_fields(block, field)\n    if len(segs) != 1:",
     "    segs = [f for f in field_chain(block)\n"
     "            if f.canonical == field]\n    if len(segs) != 1:",
     ["TestPackLane.test_the_ONE_reader_refuses_a_reference_quoted_before_the_ANCHOR"]),

    ("T172 the one reader reads the FIRST of two fields in the chain",
     "    segs = real_fields(block, field)\n    if len(segs) != 1:",
     "    segs = real_fields(block, field)\n    if not segs:",
     ["TestPackLane.test_a_TICKET_the_position_rule_cannot_read_is_MARKED_not_silent"]),

    ("T172 the [?] is decided by a whole-block search again",
     '    if not real_fields(block, "Ticket"):\n        return ""',
     '    if not FIELD_MARKER_RE["Ticket"].search(block):\n        return ""',
     ["TestPackLane.test_a_marker_QUOTED_IN_PROSE_earns_no_mark_at_all"]),

    ("T172 pack_closes asks the ambiguity itself, of the whole block",
     '    if not real_fields(block, "Ticket"):\n        return ""',
     '    if qualified_fields(block, "Ticket")[1] != 1:\n        return ""',
     ["TestPackLane.test_a_marker_QUOTED_IN_PROSE_does_not_hide_the_real_ticket"]),

    ("T172 the leading character of a repo name goes unbounded",
     'REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}#[0-9]{1,9}")',
     'REF_RE = re.compile(r"[A-Za-z0-9._-]{1,100}#[0-9]{1,9}")',
     ["TestProvenanceFields.test_a_value_outside_the_ref_shape_is_refused"]),

    ("T172 the issue number goes unbounded",
     'REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}#[0-9]{1,9}")',
     'REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}#[0-9]+")',
     ["TestProvenanceFields.test_a_value_outside_the_ref_shape_is_refused"]),

    ("T172 the repo-name length cap goes",
     'REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}#[0-9]{1,9}")',
     'REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*#[0-9]{1,9}")',
     ["TestProvenanceFields.test_a_value_outside_the_ref_shape_is_refused"]),
    # --- T172, round 2: the consolidation onto one form and one reader -------
    ("T172 the reference is stored as typed, so two spellings are two specs",
     '    args.ticket = validate_ref("ticket", args.ticket)',
     '    validate_ref("ticket", args.ticket)',
     ["TestPackLane.test_the_canonical_spelling_is_what_the_WRITER_stores"]),

    ("T172 the gate hands back nothing, so the writer stores nothing",
     '             "does not exist.")\n    return canonical_ref(value)',
     '             "does not exist.")\n    return value',
     ["TestPackLane.test_the_canonical_spelling_is_what_the_WRITER_stores"]),

    ("T172 the repo half keeps its case, so one repo counts as two",
     '    return f"{repo.lower()}#{int(number)}"', '    return f"{repo}#{int(number)}"',
     ["TestPackLane.test_two_SPELLINGS_of_one_reference_are_one_spec"]),

    ("T172 leading zeros survive, so one issue counts as two",
     '    return f"{repo.lower()}#{int(number)}"', '    return f"{repo.lower()}#{number}"',
     ["TestPackLane.test_two_SPELLINGS_of_one_reference_are_one_spec"]),

    ("T172 the one reader drops the shape, so the Ticket goes back ungated",
     "    return canonical_ref(value) if REF_RE.fullmatch(value) else None",
     "    return canonical_ref(value)",
     ["TestPackLane.test_a_TICKET_that_is_not_a_forge_reference_is_never_printed",
      "TestPackLane.test_the_read_side_shape_gate_refuses_a_PREFIX"]),

    ("T172 the one reader accepts a PREFIX again",
     "    return canonical_ref(value) if REF_RE.fullmatch(value) else None",
     "    return canonical_ref(value) if REF_RE.match(value) else None",
     ["TestPackLane.test_the_read_side_shape_gate_refuses_a_PREFIX"]),

    ("T172 the Spec's shape jumps back over the Risk it must not hide",
     '    if field["Risk"] is not None:\n'
     '        return "Risk: " + field_value(field["Risk"]), None',
     '    if field["Spec"] is not None and pack_ref(block, "Spec") is None:\n'
     '        return ("Spec is not a forge reference", REPAIR_CANCEL)\n'
     '    if field["Risk"] is not None:\n'
     '        return "Risk: " + field_value(field["Risk"]), None',
     ["TestPackLane.test_a_RISK_outranks_a_malformed_Spec_on_the_ladder"]),

    ("T172 a below-floor ticket stops naming its spec",
     "            lanes[n] = LANE_SOLO if ref is None else LANE_SOLO_SPEC % ref",
     "            lanes[n] = LANE_SOLO",
     ["TestPackLane.test_a_below_floor_ticket_still_NAMES_its_spec",
      "TestPackLane.test_the_documented_sample_IS_what_the_command_prints"]),
    # --- T172, round 4: provenance is read at the writer's position ONLY -----
    ("T172 a provenance marker in prose excludes the item, demoting its spec's lane",
     '    for name in ("Risk", "Env", "Blocked-by"):',
     '    for name in ("Risk", "Env", "Blocked-by", "Spec"):',
     ["TestPackLane.test_one_siblings_PROSE_never_demotes_a_whole_specs_lane",
      "TestPackLane.test_a_spec_QUOTED_IN_PROSE_leaves_the_item_AVULSO"]),

    ("T172 two Spec fields in the chain stop being reported as ambiguous",
     "    if len(spec_segs) > 1:", "    if False:",
     ["TestPackLane.test_two_Spec_fields_in_the_chain_are_ambiguous_not_guessed"]),

    ("T172 the Spec shape gate stops firing",
     '    if spec_segs and pack_ref(block, "Spec") is None:', "    if False:",
     ["TestPackLane.test_a_Spec_that_is_not_a_forge_reference_never_forms_a_LANE",
      "TestPackLane.test_the_read_side_shape_gate_refuses_a_PREFIX"]),

    # --- T172: `migrate --dry-run` writes nothing and reports everything ------
    ("T172 --dry-run writes the queue and the done-log anyway",
     "    save = (lambda _path, _text: None) if args.dry_run else write_atomic",
     "    save = write_atomic",
     # NOT test_the_real_run_after_the_preview_still_does_the_whole_job: with the
     # write restored the preview migrates the queue and the real run is a no-op on
     # an already-correct file, so that test passes. Naming it would claim a proof
     # this run cannot make. NOT the briefing test either — the collection has its
     # own guard, mutated below
     ["TestMigrateDryRun.test_the_preview_leaves_every_file_in_the_dir_byte_identical",
      "TestMigrateDryRun.test_the_done_log_this_run_would_CREATE_is_not_created",
      "TestMigrateDryRun.test_the_report_is_the_real_runs_report_character_for_character"]),

    ("T172 --dry-run collects (deletes) the briefing anyway",
     "        if not dry_run:\n            os.remove(handoff_path(memdir, n))",
     "        if True:\n            os.remove(handoff_path(memdir, n))",
     ["TestMigrateDryRun.test_the_briefing_the_report_calls_removed_is_still_on_disk",
      "TestMigrateDryRun.test_the_preview_leaves_every_file_in_the_dir_byte_identical"]),

    ("T172 the preview's banner lands on the stdout the caller compares",
     '"real `migrate` prints, on this queue, right now", file=sys.stderr)',
     '"real `migrate` prints, on this queue, right now")',
     ["TestMigrateDryRun.test_the_preview_announces_itself_on_stderr_and_never_on_stdout",
      "TestMigrateDryRun.test_the_report_is_the_real_runs_report_character_for_character"]),

    ("T172 --dry-run defaults ON, making every real `migrate` a silent no-op",
     'mg.add_argument("--dry-run", action="store_true",',
     'mg.add_argument("--dry-run", action="store_true", default=True,',
     ["TestMigrateDryRun.test_without_the_flag_migrate_writes_exactly_as_it_did",
      "TestMigrateFold.test_the_legacy_shape_is_folded_and_the_prose_survives_it"]),

    # the slice made an existing TRUE sentence false: before `--dry-run`, every
    # holder of the lock was a writer, so the timeout message could name one
    ("T172 the lock timeout goes back to accusing every holder of writing",
     '                         "\u2014 a concurrent command holds this queue: a writer, or a "\n'
     '                         "`migrate --dry-run` preview, which holds without writing. "\n'
     '                         "Nothing was changed; re-run `tk-queue list` and retry.")',
     '                         "\u2014 a concurrent session is writing this queue. Nothing was "\n'
     '                         "changed; re-run `tk-queue list` and retry.")',
     ["TestConcurrency.test_the_lock_timeout_does_not_accuse_the_holder_of_writing"]),

    # the banner is the one statement of this claim an operator reads, and round 2
    # of the campaign caught it denying the very file the preview leaves behind
    ("T172 the banner goes back to claiming nothing at all is written",
     '        print(f"tk-queue: --dry-run: writes {DRY_RUN_WRITES}. The report below is what a "',
     '        print(f"tk-queue: --dry-run: nothing is written — the report below is what a "',
     ["TestMigrateDryRun.test_the_preview_announces_itself_on_stderr_and_never_on_stdout"]),

    ("T172 `--help` stops deriving the enumeration, so the two sites can drift",
     '                    help=f"print the report a real run would print and write {DRY_RUN_WRITES}. "',
     '                    help=f"print the report a real run would print and write NOTHING. "',
     ["TestMigrateDryRun.test_the_help_carries_the_same_enumeration_as_the_banner"]),
    # --- T198: the repository the item's code lands in ----------------------
    # The gate is a WHITELIST, so a mutation LOOSENS one alternative rather than
    # deleting a refusal: what must not survive is an address shape reaching the
    # file that the list does not name. Each entry keeps the mutated source
    # PARSEABLE — a mutant that breaks the syntax is reported "caught" by every
    # test's import error, which is a false positive the round-2 lens measured on
    # the entry this one replaces.
    ("T198 the shape gate goes, so `origin` is a repository again",
     "    if not REPO_RE.fullmatch(value):",
     "    if False:",
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the shape loosens to a PREFIX, so junk behind an address passes",
     "    if not REPO_RE.fullmatch(value):",
     "    if not REPO_RE.match(value):",
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    # the http(s) alternative: the userinfo half is what a token rides in on
    ("T198 an http(s) URL takes a userinfo half again, so a token is stored",
     '    "https?://" + REPO_HOST + REPO_PORT + REPO_URL_PATH +      # the forge over HTTP',
     '    "https?://(?:[A-Za-z0-9._%-]+@)?" + REPO_HOST + REPO_PORT + REPO_URL_PATH +  # the forge over HTTP',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a URL path stops being ASCII, so an encoding smuggles a refused character",
     'REPO_URL_PATH = r"(?:/[A-Za-z0-9._-]+)+"',
     'REPO_URL_PATH = r"(?:/[^\\s]+)+"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a URL needs no path, so a bare host is a repository",
     '    "https?://" + REPO_HOST + REPO_PORT + REPO_URL_PATH +      # the forge over HTTP',
     '    "https?://" + REPO_HOST + REPO_PORT + "(?:" + REPO_URL_PATH + ")?" +   # the forge over HTTP',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the host loosens, so a bracketed IPv6 literal and worse pass",
     'REPO_HOST = r"[A-Za-z0-9][A-Za-z0-9.-]*"',
     'REPO_HOST = r"[^/]+"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    # the ssh alternatives: `git@` is a protocol name, and only that one
    ("T198 the ssh URL takes any user, not the protocol's own `git@`",
     '    "|ssh://git@" + REPO_HOST + REPO_PORT + REPO_URL_PATH +    # SSH, spelled as a URL',
     '    "|ssh://[A-Za-z0-9._-]+@" + REPO_HOST + REPO_PORT + REPO_URL_PATH +    # SSH, spelled as a URL',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the scp-like form takes any user half",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|[A-Za-z0-9._:-]+@" + REPO_HOST + ":/?[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"   # SSH, scp-like',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the scp-like path stops being ASCII, so the marker and bracket return",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|git@" + REPO_HOST + ":/?" + REPO_LOCAL + r"(?:/[A-Za-z0-9._-]+)*"   # SSH, scp-like',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    # the local-path alternatives, and the four characters they still refuse
    ("T198 a relative path is a repository again",
     '    "|/" + REPO_LOCAL +                                        # a POSIX absolute path',
     '    "|/?" + REPO_LOCAL +                                       # a POSIX absolute path',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the field marker becomes spellable inside a local path again",
     'REPO_LOCAL = "[^\\\\s*\\\\[\\\\]" + REPO_INVISIBLE + "]+"',
     'REPO_LOCAL = "[^\\\\s\\\\[\\\\]" + REPO_INVISIBLE + "]+"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a bracket splices a second group into the line `pack` composes",
     'REPO_LOCAL = "[^\\\\s*\\\\[\\\\]" + REPO_INVISIBLE + "]+"',
     'REPO_LOCAL = "[^\\\\s*" + REPO_INVISIBLE + "]+"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a blank, and so a newline, reaches the single line the chain lives on",
     'REPO_LOCAL = "[^\\\\s*\\\\[\\\\]" + REPO_INVISIBLE + "]+"',
     'REPO_LOCAL = "[^*\\\\[\\\\]" + REPO_INVISIBLE + "]+"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 an invisible character rides in a local path again",
     'REPO_LOCAL = "[^\\\\s*\\\\[\\\\]" + REPO_INVISIBLE + "]+"',
     'REPO_LOCAL = "[^\\\\s*\\\\[\\\\]]+"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a trailing '.' passes, and the value comes back a character short",
     "\n" + r'    r"(?<![./\\])"' + "\n)",
     "\n)",
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    # the other direction: a whitelist that narrows silently refuses real work, and
    # only the acceptance test can say so
    ("T198 the scp-like address stops being an address at all",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|(?!x)x"   # SSH, scp-like',
     ["TestRepoField.test_the_shapes_that_actually_occur_are_accepted"]),

    ("T198 a host loses its port, so a self-hosted forge stops being addressable",
     'REPO_PORT = r"(?::[0-9]{1,5})?"',
     'REPO_PORT = ""',
     ["TestRepoField.test_the_shapes_that_actually_occur_are_accepted"]),

    # --- T198, round 3: the edges the whitelist still had --------------------
    ("T198 the port returns to the scp-like branch, which cannot honour one",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|git@" + REPO_HOST + REPO_PORT + ":/?[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"   # SSH, scp-like',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a `~/` address is a repository again, and it means one per reader",
     '    "|/" + REPO_LOCAL +                                        # a POSIX absolute path',
     '    "|~?/" + REPO_LOCAL +                                      # a POSIX absolute path',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 a `.` or `..` segment passes, so one repository has two spellings",
     r'REPO_NO_DOT_SEG = r"(?![^\n]*[/\\]\.{1,2}[/\\])"',
     r'REPO_NO_DOT_SEG = ""',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the dot-segment rule stops seeing the Windows separator",
     r'REPO_NO_DOT_SEG = r"(?![^\n]*[/\\]\.{1,2}[/\\])"',
     r'REPO_NO_DOT_SEG = r"(?![^\n]*/\.{1,2}/)"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 `file://` takes any number of slashes, so a relative path rides in",
     '    "|file:///" + REPO_LOCAL +                                 # a local repo, as a URL',
     '    "|file://" + REPO_LOCAL +                                  # a local repo, as a URL',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the ssh URL needs no path, so a bare host is a repository",
     '    "|ssh://git@" + REPO_HOST + REPO_PORT + REPO_URL_PATH +    # SSH, spelled as a URL',
     '    "|ssh://git@" + REPO_HOST + REPO_PORT + "(?:" + REPO_URL_PATH + ")?" +    # SSH, spelled as a URL',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the scp-like address needs no path either",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|git@" + REPO_HOST + ":/?[A-Za-z0-9._-]*" + r"(?:/[A-Za-z0-9._-]+)*"   # SSH, scp-like',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the scp-like path may no longer be absolute, a shape that is real",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|git@" + REPO_HOST + ":[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"   # SSH, scp-like',
     ["TestRepoField.test_the_shapes_that_actually_occur_are_accepted"]),

    ("T198 a trailing separator passes, so one repository has two spellings",
     r'    r"(?<![./\\])"',
     r'    r"(?<!\.)"',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the scp-like path takes an all-digit first segment, a port git folds in",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|git@" + REPO_HOST + r":/?[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     ["TestRepoField.test_a_remote_name_or_a_cwd_relative_path_is_refused"]),

    ("T198 the all-digit rule swallows a real path that merely starts with a digit",
     '    "|git@" + REPO_HOST + r":/?(?![0-9]+/)[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     '    "|git@" + REPO_HOST + r":/?(?![0-9])[A-Za-z0-9._-]+" + r"(?:/[A-Za-z0-9._-]+)*"  # SSH, scp-like',
     ["TestRepoField.test_the_shapes_that_actually_occur_are_accepted"]),

    ("T198 the field ceiling stops holding the one field the shape does not bound",
     "                         deferred=args.deferred, repo=args.repo)",
     "                         deferred=args.deferred)",
     ["TestRepoField.test_a_value_past_the_field_ceiling_is_refused"]),

    ("T198 the field is not written at all",
     '    for flag, field in ((args.ticket, "Ticket"), (args.spec, "Spec"),\n'
     '                        (args.repo, "Repo")):',
     '    for flag, field in ((args.ticket, "Ticket"), (args.spec, "Spec")):',
     ["TestRepoField.test_the_field_is_written_at_the_writers_position",
      "TestRepoField.test_the_value_round_trips_byte_for_byte"]),

    ("T198 the repo is written BEFORE the ticket, so the chain's order drifts",
     '    for flag, field in ((args.ticket, "Ticket"), (args.spec, "Spec"),\n'
     '                        (args.repo, "Repo")):',
     '    for flag, field in ((args.repo, "Repo"), (args.ticket, "Ticket"),\n'
     '                        (args.spec, "Spec")):',
     ["TestRepoField.test_the_field_is_written_at_the_writers_position"]),

    ("T198 `pack` stops returning the repository",
     "                            + pack_closes(text) + pack_repo(text))",
     "                            + pack_closes(text))",
     ["TestPackRepo.test_the_repo_of_an_eligible_item_comes_back",
      "TestPackRepo.test_the_repo_follows_the_ticket_on_the_line",
      "TestPack.test_the_documented_sample_IS_what_the_command_prints"]),

    ("T198 the repo is appended BEFORE the ticket",
     "                            + pack_closes(text) + pack_repo(text))",
     "                            + pack_repo(text) + pack_closes(text))",
     ["TestPackRepo.test_the_repo_follows_the_ticket_on_the_line",
      "TestPack.test_the_documented_sample_IS_what_the_command_prints"]),

    ("T198 the repo is read from the whole BLOCK, so prose becomes an address",
     '    segs = real_fields(block, "Repo")',
     '    segs = list(re.finditer(FIELD_MARKER_RE["Repo"].pattern + r"[^*\\n]*", block))',
     ["TestPackRepo.test_a_marker_QUOTED_IN_PROSE_is_not_read_as_the_repo"]),

    ("T198 two Repo fields in the chain are no longer ambiguous — the first wins",
     '    value = field_value(segs[0]) if len(segs) == 1 else None',
     '    value = field_value(segs[0])',
     ["TestPackRepo.test_two_Repo_fields_in_the_chain_are_MARKED_and_never_guessed"]),

    ("T198 the read-side shape gate goes, so a hand-edited `origin` is returned",
     '    if value is None or not REPO_RE.fullmatch(value):',
     '    if value is None:',
     ["TestPackRepo.test_a_value_no_reader_may_use_is_MARKED_too"]),

    ("T198 an unreadable address is silent instead of marked",
     '        return "  [repo: ?]"',
     '        return ""',
     ["TestPackRepo.test_a_value_no_reader_may_use_is_MARKED_too",
      "TestPackRepo.test_two_Repo_fields_in_the_chain_are_MARKED_and_never_guessed"]),

    # --- T148: the birth date and the age it gives the queue -------------

    ("T148 `add` stops stamping the birth date",
     '    fields.append(f"**Born:** {datetime.date.today().isoformat()}.")\n',
     "",
     ["TestBirthDate.test_a_new_item_is_born_with_todays_date"]),

    ("T148 the stamp takes --source's word for when the item was born",
     '    fields.append(f"**Born:** {datetime.date.today().isoformat()}.")',
     '    fields.append(f"**Born:** {args.source or datetime.date.today().isoformat()}.")',
     ["TestBirthDate.test_the_stamp_is_the_day_of_the_add_and_not_what_source_says"]),

    ("T148 `migrate` invents today's date for a **Source:** that states none",
     '    if not seen:\n        return None, "no-date"',
     "    if not seen:\n        return today, None",
     ["TestMigrateBackdates.test_a_source_with_no_date_leaves_the_item_undated_and_says_so"]),

    ("T148 `migrate` picks the first of two dates instead of declining",
     '    if len(seen) > 1:\n        return None, "two"',
     "    if len(seen) > 1:\n        return seen[0], None",
     ["TestMigrateBackdates.test_two_different_dates_in_one_source_decide_nothing"]),

    ("T148 a **Source:** date in the future is stamped as a birth date",
     '    if seen[0] > today:\n        return None, "future"',
     '    if False:\n        return None, "future"',
     ["TestMigrateBackdates.test_a_source_date_in_the_future_is_not_a_birth_date"]),

    ("T148 backdating stamps the day of the migration, not the date **Source:** states",
     "    born, why = source_birthdate(field_value(src[0]), today)",
     "    born, why = today, None",
     ["TestMigrateBackdates.test_a_source_that_states_a_date_backdates_the_item",
      "TestMigrateBackdates.test_a_source_with_no_date_leaves_the_item_undated_and_says_so"]),

    ("T148 an unreadable **Source:** is reported as no **Source:** at all",
     '        return block, ("unreadable" if markers(block, "Source")\n'
     "                       else \"none\")",
     '        return block, "none"',
     ["TestMigrateBackdates.test_a_source_no_reader_may_use_is_reported_as_its_own_case"]),

    ("T148 a second `migrate` restamps an item that already carries a birth date",
     '    if real_fields(block, "Born"):\n        return block, "stamped"',
     '    if False:\n        return block, "stamped"',
     ["TestMigrateFold.test_an_already_canonical_queue_is_untouched_and_silent",
      "TestMigrateFold.test_a_second_migrate_is_a_no_op_on_the_file_and_says_nothing"]),

    ("T148 `list` drops the age column",
     'return (f"{label}  {cls:<10}  {age:>4}  {title}"',
     'return (f"{label}  {cls:<10}  {title}"',
     ["TestListShowsTheAge.test_a_dated_item_shows_its_age_in_days",
      "TestListShowsTheAge.test_the_age_survives_the_project_grouping"]),

    # `age_cell`, not `item_age`: an unstamped item and one whose stamp is
    # unreadable both arrive here as None, and this is the single place that
    # decides what the reader sees for either
    ("T148 an item with no readable birth date is displayed as born today",
     '    return "?" if days is None else f"{days}d"',
     '    return f"{days or 0}d"',
     ["TestListShowsTheAge.test_a_legacy_queue_lists_without_an_age_and_without_breaking"]),

    # same anchor as the mutation above, and the opposite half of the decision:
    # that one asks what an item with NO age shows, this one asks whether an age
    # of zero is an age at all. A falsy test conflates the two, and `0d` — an item
    # added today — would print as `?`, the mark that means "predates the field"
    ("T148 an item born today reads as having no age at all",
     '    return "?" if days is None else f"{days}d"',
     '    return "?" if not days else f"{days}d"',
     ["TestListShowsTheAge.test_an_item_born_today_is_zero_days_old_not_blank"]),

    ("T148 an unreadable birth date crashes `list` instead of reading as unknown",
     "    try:\n        born = datetime.date.fromisoformat(field_value(got[0]))\n"
     "    except ValueError:\n        return None",
     "    born = datetime.date.fromisoformat(field_value(got[0]))",
     ["TestListShowsTheAge.test_a_legacy_queue_lists_without_an_age_and_without_breaking"]),

    # --- T297: the WIP cap ------------------------------------------------

    ("T297 the cap is not consulted at all",
     "    check_wip(load_site(), memdir)\n    iid = max_id(memdir) + 1",
     "    iid = max_id(memdir) + 1",
     ["TestWipCap.test_the_add_is_refused_when_the_open_items_reach_the_cap"]),

    ("T297 --force bypasses the cap",
     "    check_wip(load_site(), memdir)",
     "    if not args.force:\n        check_wip(load_site(), memdir)",
     ["TestWipCap.test_force_does_not_reach_the_cap"]),

    ("T297 the cap refuses only PAST itself (off by one)",
     "    if cap is None or total < cap:\n        return",
     "    if cap is None or total <= cap:\n        return",
     ["TestWipCap.test_the_add_is_refused_when_the_open_items_reach_the_cap"]),

    # the over-refusal direction, and the one that would brick every queue on a
    # machine whose user never chose a number
    ("T297 an unset cap reads as a cap of zero",
     "    cap = site.ceilings.get(WIP_KEY) if site else None",
     "    cap = site.ceilings.get(WIP_KEY, 0) if site else 0",
     ["TestWipCap.test_no_key_in_the_site_file_is_no_cap",
      "TestWipCap.test_no_site_file_at_all_is_no_cap"]),

    # the measured bypass: a cap that counts one queue is walked around with
    # `--dir`, and the WIP is the same WIP
    ("T297 the cap counts the target queue only (the --dir bypass restored)",
     "    dirs = [d for name, d in tk_roster.queues(tk_roster.projects_root())\n"
     "            if not tk_roster.excluded_by(name, allow, deny)]",
     "    dirs = []",
     ["TestWipCap.test_the_count_sums_every_queue_on_the_roster",
      "TestWipCap.test_pointing_dir_at_another_queue_does_not_get_past_the_cap"]),

    ("T297 the queue being written is left out of its own count",
     "    dirs.append(memdir)", "    pass",
     ["TestWipCap.test_the_add_is_refused_when_the_open_items_reach_the_cap"]),

    ("T297 a queue the site file excludes is counted anyway",
     "            if not tk_roster.excluded_by(name, allow, deny)]", "            if True]",
     ["TestWipCap.test_a_queue_the_site_file_excludes_is_not_counted"]),

    ("T297 one queue reached by two spellings is counted twice",
     "        if key in seen:\n            continue", "        if False:\n            continue",
     ["TestWipCap.test_one_queue_named_twice_is_counted_once",
      "TestWipCap.test_a_symlink_naming_a_roster_queue_is_still_counted_once"]),

    ("T297 a closed item still counts as open work",
     '    return sum(1 for kind, _ in split_blocks(content) if kind == "item-open")',
     '    return sum(1 for kind, _ in split_blocks(content) if kind.startswith("item"))',
     ["TestWipCap.test_a_done_item_is_not_open_work"]),

    ("T297 the refusal stops naming `done` as a remedy",
     '    \'`tk-queue done <id> --how "<outcome + pointer>"` for one that is finished, \'',
     "    ''",
     ["TestWipCap.test_the_refusal_names_done_and_cancel_and_where_the_number_lives",
      "TestWipCap.test_the_printed_remedy_RUNS_and_makes_room"]),

    # the cap lives in that file, so a half-read one is a cap that vanishes.
    # A DIFFERENT anchor from validate_env's identical clause below it — this one
    # carries the `return`, which is what makes it match once
    ("T297 a rotten site file reads as an absent one (the cap disappears)",
     "        if site_names_the_cap():\n            fail(str(e))",
     "        if False:\n            fail(str(e))",
     ["TestWipCap.test_a_rotten_site_file_stops_the_add_instead_of_vanishing_the_cap"]),

    # the site file's own half: an unknown key is IGNORED by design, so dropping
    # the key from the tuple does not fail the file — it silently unsets the cap
    ("T297 site the cap's key leaves the tuple, so the value reads as an unknown key",
     'CEILINGS = ("max-local-subagents", "max-cloud-subagents", "max-open-items",\n'
     '            "max-open-items-per-queue")',
     'CEILINGS = ("max-local-subagents", "max-cloud-subagents")',
     ["TestWipCap.test_the_add_is_refused_when_the_open_items_reach_the_cap",
      "TestWipCap.test_a_cap_of_zero_is_refused_by_the_site_file"],
     "bin/tk_site.py"),

    # --- T345: the reader a THIRD PARTY's file goes through ----------------

    # the consolidation itself: `read` is this script's own reader, and it guards
    # none of what the site file's does — the two defects below were measured
    # through it, on the queues of projects this session never opened
    ("T345 the count reads a third party's queue with the unguarded reader",
     '        content = tk_site.read_text(\n'
     '            path, "A queue file is Markdown written by `tk-queue`",\n'
     '            " — the offending byte arrived with text pasted from another encoding")',
     "        content = read(path)",
     ["TestWipCap.test_a_sibling_queue_that_is_not_utf8_is_diagnosed_and_not_crashed"]),

    ("T345/T163 the unguarded reader AND the door stop repairing a sibling's header",
     ['        content = tk_site.read_text(\n'
      '            path, "A queue file is Markdown written by `tk-queue`",\n'
      '            " — the offending byte arrived with text pasted from another encoding")',
      '            fixed = head.replace(BOM, "")'],
     ["        content = read(path)", "            fixed = head"],
     ["TestWipCap.test_an_invisible_bom_in_a_sibling_queue_does_not_undercount_it"]),

    ("T345 the roster is loaded at import again, so every command depends on it",
     "        _ROSTER = mod\n    return _ROSTER",
     "        _ROSTER = mod\n    return _ROSTER\n\n\n_EAGER_ROSTER = roster()",
     ["TestWipCap.test_a_broken_roster_does_not_reach_the_commands_that_never_read_it",
      "TestWipCap.test_an_add_with_no_cap_never_loads_the_roster_either"]),

    ("T345 a `tk-roster` that cannot be loaded comes back as a raw traceback",
     "        except Exception as e:\n            fail(",
     "        except ZeroDivisionError as e:\n            fail(",
     ["TestWipCap.test_a_broken_roster_under_a_cap_is_reported_not_crashed"]),

    # --- T346: the lens's findings on the slice above ---------------------

    # the dedup key, whose reachable input is a `--dir` naming a queue the roster
    # already swept, by another spelling of the same path
    ("T346 two spellings of one queue are compared as STRINGS",
     "        key = os.path.realpath(d)", "        key = d",
     ["TestWipCap.test_a_symlink_naming_a_roster_queue_is_still_counted_once"]),

    ("T346 an absent cap is no longer a no-op: a rotten site file takes the add down",
     "        if site_names_the_cap():", "        if True:",
     ["TestWipCap.test_a_rotten_site_file_with_no_cap_in_it_does_not_break_the_add"]),

    # the leak: a project directory carries a client's or a company's name, and a
    # refusal travels into transcripts and pull request bodies
    ("T346 the refusal dumps every project on the machine again",
     '    others = [(d, n) for d, key, n in counts if key != target and n]\n'
     '    where = f"\\n  {mine:>4}  {memdir}"\n'
     '    if others:\n'
     '        where += (f"\\n  {sum(n for _, n in others):>4}  in {len(others)} '
     'other queue(s) "\n                  "on this machine (`tk-roster` lists them there)")',
     '    where = "".join(f"\\n  {n:>4}  {d}" for d, _, n in counts if n)',
     ["TestWipCap.test_the_refusal_never_names_another_project",
      "TestWipCap.test_the_count_sums_every_queue_on_the_roster"]),

    ("T346 a queue holding nothing is counted among the queues to go look in",
     "    others = [(d, n) for d, key, n in counts if key != target and n]",
     "    others = [(d, n) for d, key, n in counts if key != target]",
     ["TestWipCap.test_an_empty_queue_is_not_counted_as_a_queue_holding_work"]),

    ("T346 a count shrunk by HOME passes in silence",
     "    if not os.path.isdir(root):", "    if False:",
     ["TestWipCap.test_a_home_with_no_projects_directory_says_the_count_shrank"]),

    # the two prose entries: five numbers in this slice's prose were wrong, none
    # of them known to any command. These two are now known to one
    ("T346 the overshoot goes back to one item over the cap",
     """    session adding to ANOTHER queue between this count and our write. The bound
    is not one item: every add that races this one counts the same free slot, so
    k of them land k-1 items above the cap, and only the NEXT add on any queue
    refuses. Measured, four adds on four queues with nine open against a cap of
    ten: thirteen open, three above.""",
     """    session adding to ANOTHER queue between this count and our write, which can
    put the machine one item over the cap; the next `add` on either queue then
    refuses.""",
     ["TestWipCap.test_the_overshoot_the_missing_locks_cost_is_stated_as_measured"]),

    ("T346 the refusal is said again to burn an ID it never reserved",
     """    # the WIP cap. It sits above `max_id` for reading order, not for safety:
    # `max_id` only READS, nothing is reserved, and a refusal below it would
    # leave no hole in the sequence — the claim that it would was written here
    # and was never true.""",
     """    # the WIP cap, and BEFORE the ID is allocated: a refusal that has already
    # spent a number leaves a hole in the sequence.""",
     ["TestWipCap.test_no_prose_claims_a_refused_add_would_burn_an_id"]),

    # --- the two axes, over the batch above (T346, cold session) ----------

    ("T346 the cap is looked for in UTF-8 only, so a UTF-16 site file loses it",
     '(("utf-8", "replace"),) + WIDE_DECODINGS', '(("utf-8", "replace"),)',
     ["TestWipCap.test_a_site_file_in_utf16_that_sets_the_cap_still_stops_the_add"]),

    ("T346 reading the wide encodings makes an ABSENT cap fatal too",
     "        if any(assignment.match(line) for line in text.splitlines()):\n"
     "            return True\n"
     "    return False",
     "        if any(assignment.match(line) for line in text.splitlines()):\n"
     "            return True\n"
     "    return True",
     ["TestWipCap.test_a_site_file_in_utf16_with_no_cap_in_it_still_does_not_break_the_add"]),

    ("T346 the roster is said to be imported at the top of the file again",
     "comes from `tk-roster`, loaded on FIRST USE by `roster()` and not at import",
     "comes from `tk-roster`, imported at the top of this file",
     ["TestWipCap.test_no_prose_says_the_roster_is_imported_at_the_top_of_the_file"]),

    ("T346 the no-leak claim widens back from the refusal to the whole command",
     "    # WHERE the work is, WITHOUT writing another project's name into THE",
     "    # WHERE the work is, WITHOUT writing another project's name into this session's output. The",
     ["TestWipCap.test_no_prose_claims_the_refusals_channel_never_names_another_project"]),

    ("T346 the untested branch claims a first `add` reaches it",
     "THAT RACE IS THE ONLY WAY INTO THAT",
     "The other reachable way in is a first `add` into a brand-new queue. THAT IS NOT",
     ["TestWipCap.test_the_untested_branch_says_it_is_the_race_and_not_a_first_add"]),

    # --- the CLI's own words: one entry per sentence a reader decides from ---
    ("T274 the owner refusal drops the first-character rule again",
     "name: it STARTS with a letter or a ", "name: letters, digits and a ",
     ["TestTheCommandsSayWhatTheyDo.test_the_owner_grammar_names_the_first_character_rule"]),

    ("T274 claim --help drops the first-character rule again",
     "a session or host label STARTING with a ", "a session or host label with a ",
     ["TestTheCommandsSayWhatTheyDo.test_the_owner_grammar_names_the_first_character_rule"]),

    ("T335 edit --text goes back to having no description at all",
     "REPLACES the item's text — everything between the ",
     "the item's new text, replacing everything between the ",
     ["TestTheCommandsSayWhatTheyDo.test_edit_help_says_that_text_replaces_and_what_it_replaces"]),

    ("T340 cancel --help stops naming which command comes first",
     "--text` on the survivor FIRST and `cancel` on the source only ",
     "--text` on the survivor and `cancel` on the source only ",
     ["TestTheCommandsSayWhatTheyDo.test_cancel_and_edit_both_name_the_order_a_fusion_runs_in"]),

    ("T354 the ceiling refusal calls the block the item again",
     "the item BLOCK has {len(item)} chars", "item has {len(item)} chars",
     ["TestTheCommandsSayWhatTheyDo.test_the_ceiling_refusal_names_the_block_and_the_half_over_the_line"]),

    ("T354 the refusal names one half whichever one overflowed",
     "{'text' if text >= fields else 'fields'}. An item is a pending ",
     "{'text'}. An item is a pending ",
     ["TestTheCommandsSayWhatTheyDo.test_the_refusal_points_at_the_fields_when_they_are_the_larger_half"]),

    ("kickoff-prune gaps: add --help stops declaring the canonical spelling",
     "stored: repo lower-cased, number without leading ",
     "stored: the repo and the number as given, with leading ",
     ["TestTheCommandsSayWhatTheyDo.test_add_help_names_the_canonical_spelling_of_a_forge_reference"]),

    ("kickoff-prune gaps: add --repo help goes back to the summary",
     "of five shapes: https://<host>/<path>, ",
     "of shapes, among them ",
     ["TestTheCommandsSayWhatTheyDo.test_add_help_carries_the_whole_repo_whitelist"]),

    ("kickoff-prune gaps: --force names one ceiling again",
     "raise BOTH ceilings for this one call: the item BLOCK, from ",
     "raise the field ceiling for this one call, and the item BLOCK from ",
     ["TestTheCommandsSayWhatTheyDo.test_force_names_both_ceilings_it_raises_wherever_it_is_offered"]),

    ("kickoff-prune gaps: the comment names a prose site the prune moved",
     "docstring, and `tk/reference/queue.md` — the kickoff SKILL.md carried it until",
     "docstring, and the kickoff SKILL.md) cannot read a constant. It carried it until",
     ["TestTheCommandsSayWhatTheyDo.test_the_dry_run_comment_names_the_prose_site_that_exists"]),

    # --- T152 the harness's own reader of an entry ------------------------
    # These mutate THIS file. A short anchor would also match inside its own
    # entry literal and be called UNRUNNABLE; an anchor spanning a line break
    # escapes that, because a `\n` written in an entry is two characters here
    # and never a newline.
    ("T152 an entry naming a test that does not exist is scored as a kill again",
     "    if gone:\n        return \"MISNAMED\", f\"names a test that does not exist:",
     "    if False:\n        return \"MISNAMED\", f\"names a test that does not exist:",
     ["TestMutationHarness.test_an_entry_naming_a_test_that_does_not_exist_is_refused"],
     os.path.join("tests", "mutations.py")),

    # the same defect one level up: `per_module` drops the names of a module
    # nothing resolved, so an entry naming a typo'd MODULE would be scored on
    # whatever names were left and never asked about its typo
    ("T119 an entry naming a module this run never loaded is scored on the rest",
     "    absent = modules_missing([entry], modules)\n    if absent:",
     "    absent = modules_missing([entry], modules)\n    if False:",
     ["TestMutationHarness."
      "test_an_entry_naming_a_module_this_run_never_loaded_is_refused"],
     os.path.join("tests", "mutations.py")),

    ("T119 the absorbed suite's debt is recorded as zero, so its ratchet cannot bite",
     "\nKNOWN_UNPROVED_ROSTER = 4", "\nKNOWN_UNPROVED_ROSTER = 0",
     ["TestMutationHarness."
      "test_the_absorbed_roster_suite_keeps_its_own_unproved_ceiling"],
     os.path.join("tests", "mutations.py")),

    ("T119 the module a name carries is ignored, so one list cannot hold two suites",
     '    if module.startswith("test_") and rest:\n        return module, rest',
     "    if False:\n        return module, rest",
     ["TestMutationHarness.test_a_name_may_say_which_suite_it_lives_in"],
     os.path.join("tests", "mutations.py")),

    ("T152 an entry naming a whole class is read as a typo",
     "            cls = getattr(module_obj, cls_name, None)\n"
     "            if cls is None or (attr and not hasattr(cls, attr)):",
     "            cls = getattr(module_obj, cls_name, None)\n"
     "            if cls is None or not hasattr(cls, attr):",
     ["TestMutationHarness.test_an_entry_naming_a_whole_class_is_not_read_as_a_typo"],
     os.path.join("tests", "mutations_tk_contract.py")),

    ("T152 a mutation that changes nothing runs anyway",
     "    if not pairs or any(o == n for o, n in pairs):\n"
     '        return "UNRUNNABLE"',
     "    if not pairs:\n"
     '        return "UNRUNNABLE"',
     ["TestMutationHarness.test_a_mutation_that_changes_nothing_is_refused"],
     os.path.join("tests", "mutations.py")),

    ("T152 an anchor that matches twice is applied to the first match",
     "    if any(c != 1 for c in counts):\n        # NOT a survivor",
     "    if any(c < 1 for c in counts):\n        # NOT a survivor",
     ["TestMutationHarness.test_an_anchor_that_does_not_match_exactly_once_is_refused"],
     os.path.join("tests", "mutations.py")),

    ("T160 the baseline classes go back to a hand-kept list",
     'have been told from one the mutant reddened."""\n'
     "    return list(test_classes(module_obj))",
     'have been told from one the mutant reddened."""\n'
     '    return ["TestPrefixedId", "TestConcurrency"]',
     ["TestMutationHarness.test_the_classes_the_baseline_runs_are_derived_not_listed"],
     os.path.join("tests", "mutations.py")),

    ("T160 the recorded debt of tests no entry proves stops being read",
     "\nKNOWN_UNPROVED = 61", "\nKNOWN_UNPROVED = 0",
     ["TestMutationHarness."
      "test_the_recorded_count_of_unproved_tests_is_not_below_the_real_one"],
     os.path.join("tests", "mutations.py")),

    ("T152 the recorded debt of misnamed entries stops being read",
     "\nKNOWN_MISNAMED = 9", "\nKNOWN_MISNAMED = 0",
     ["TestMutationHarness."
      "test_the_recorded_count_of_misnamed_entries_is_not_below_the_real_one"],
     os.path.join("tests", "mutations.py")),

    # --- T360: the cap per QUEUE, and a total that scales with the roster ---
    ("T360 the per-queue cap stops refusing anything",
     "    if per_queue is not None and mine >= per_queue:", "    if False:",
     ["TestWipCapPerQueue.test_a_full_queue_is_refused_while_the_others_are_empty",
      "TestWipCapPerQueue.test_force_does_not_reach_the_per_queue_cap_either"]),

    ("T360 the per-queue cap refuses only PAST itself (off by one)",
     "mine >= per_queue:", "mine > per_queue:",
     ["TestWipCapPerQueue.test_a_full_queue_is_refused_while_the_others_are_empty",
      "TestWipCapPerQueue.test_force_does_not_reach_the_per_queue_cap_either"]),

    # over-trigger direction: the brake asked of the MACHINE is the total again,
    # and it closes every queue on it the moment one of them fills
    ("T360 the per-queue cap is asked of the machine, not of the queue",
     "    if per_queue is not None and mine >= per_queue:",
     "    if per_queue is not None and total >= per_queue:",
     ["TestWipCapPerQueue.test_a_sibling_queue_stays_open_while_one_is_full"]),

    ("T360 auto derives the WORST case, per-queue x N",
     "        cap = (per_queue - discount) * len(counts)",
     "        cap = per_queue * len(counts)",
     ["TestWipCapPerQueue.test_the_total_refuses_with_no_queue_at_its_own_cap"]),

    ("T360 auto counts one queue instead of the roster's",
     "        cap = (per_queue - discount) * len(counts)",
     "        cap = (per_queue - discount)",
     ["TestWipCapPerQueue.test_auto_counts_the_queues_the_roster_counts"]),

    ("T360 the derived total stops saying where it came from",
     '    how = (f"`{WIP_KEY} = {tk_site.WIP_AUTO}` in {site.path}, which is "\n'
     '           f"({per_queue} - {site.ceilings.get(DISCOUNT_KEY, 0)}) x {len(counts)} "\n'
     '           "queue(s)" if auto else f"`{WIP_KEY}` in {site.path}")',
     '    how = f"`{WIP_KEY}` in {site.path}"',
     ["TestWipCapPerQueue.test_the_total_refuses_with_no_queue_at_its_own_cap"]),

    # the third option eats the second: a number the user pinned is overwritten
    # by one derived from a key they wrote for the OTHER half of the gate
    ("T360 a pinned total is overwritten by the derived one",
     "    if auto:\n        discount = site.ceilings.get(DISCOUNT_KEY, 0)",
     "    if per_queue is not None:\n        discount = site.ceilings.get(DISCOUNT_KEY, 0)",
     ["TestWipCapPerQueue.test_an_explicit_number_still_pins_the_total"]),

    ("T360 an unset total refuses instead of letting the add through",
     "    if cap is None or total < cap:\n        return",
     "    if cap is not None and total < cap:\n        return",
     ["TestWipCapPerQueue.test_the_per_queue_cap_alone_leaves_the_total_uncapped"]),

    ("T360 an absent per-queue key reads as a cap of three",
     "    per_queue = site.ceilings.get(PER_QUEUE_KEY) if site else None",
     "    per_queue = site.ceilings.get(PER_QUEUE_KEY, 3) if site else None",
     ["TestWipCapPerQueue.test_without_the_per_queue_key_nothing_changes"]),

    ("T360 the gating-key whitelist goes back to the total alone",
     '    assignment = re.compile(r"\\s*(?:" + "|".join(\n'
     "        re.escape(k) for k in (WIP_KEY, PER_QUEUE_KEY, DISCOUNT_KEY)) + r\")\\s*=\")",
     '    assignment = re.compile(rf"\\s*{re.escape(WIP_KEY)}\\s*=")',
     ["TestWipCapPerQueue.test_a_per_queue_cap_that_is_not_a_number_is_refused"]),

    ("T360 site auto with no per-queue cap is read as no cap at all",
     "    if open_items_auto:\n        del pairs[WIP_TOTAL]\n"
     "        if WIP_PER_QUEUE not in pairs:",
     "    if open_items_auto:\n        del pairs[WIP_TOTAL]\n        if False:",
     ["TestWipCapPerQueue."
      "test_auto_without_the_per_queue_key_is_refused_by_the_site_file"],
     "bin/tk_site.py"),

    ("T360 site a discount at or above the per-queue cap is accepted",
     "    if per_queue is not None and discount is not None and discount >= per_queue:",
     "    if False:",
     ["TestWipCapPerQueue.test_a_discount_at_or_above_the_per_queue_cap_is_refused"],
     "bin/tk_site.py"),

    # --- T306: the dependency between two items of one queue ----------------
    ("T306 the blocker is written outside the position every gate reads",
     ['    if args.blocked_by and not clears_field(args.blocked_by):\n'
      '        fields.append(f"**Blocked-by:** {args.blocked_by}.")\n'
      '    fields.append(f"**Criterion:** {args.criterion}.")',
      '    if args.project:\n        fields.append(f"**Project:** {args.project}.")'],
     ['    fields.append(f"**Criterion:** {args.criterion}.")',
      '    if args.project:\n        fields.append(f"**Project:** {args.project}.")\n'
      '    if args.blocked_by and not clears_field(args.blocked_by):\n'
      '        fields.append(f"**Blocked-by:** {args.blocked_by}.")'],
     ["TestBlockedBy.test_the_line_is_written_where_the_gates_read_a_field"]),

    ("T306 add stops validating the blocker",
     '    args.blocked_by = validate_blocker(args.blocked_by)\n'
     "    # returned UNCHANGED where the two above are canonicalised",
     "    # returned UNCHANGED where the two above are canonicalised",
     ["TestBlockedBy.test_a_value_that_is_no_item_id_is_refused_and_writes_nothing",
      "TestBlockedBy.test_every_id_spelling_is_stored_as_the_one"]),

    ("T306 the id is stored in whatever spelling the caller typed",
     '    return f"T{int(m.group(1)):03d}"', "    return value",
     ["TestBlockedBy.test_every_id_spelling_is_stored_as_the_one"]),

    # over-trigger direction: a field written whether or not the caller asked
    # for one gives every item a dependency nobody declared
    ("T306 the line is written on an add that never named a blocker",
     "    if args.blocked_by and not clears_field(args.blocked_by):",
     "    if True:",
     ["TestBlockedBy.test_an_add_without_the_flag_writes_the_item_of_today"]),

    ("T306 an open blocker stops holding the item back",
     "        if int(m.group(1)) in open_ids:", "        if False:",
     ["TestBlockedBy.test_pack_leaves_the_item_out_while_the_blocker_is_open"]),

    # the other direction: a blocker already closed goes on holding the item,
    # which is a package that shrinks by itself and never grows back
    ("T306 every blocker holds the item back, the closed ones included",
     "        if int(m.group(1)) in open_ids:", "        if True:",
     ["TestBlockedBy.test_closing_the_blocker_lets_it_back_in_with_no_re_edit",
      "TestBlockedBy.test_a_blocker_this_queue_never_held_does_not_hold_the_item"]),

    ("T306 the exclusion reason drops the value it read",
     '            return f"blocked by {value}, still open", None',
     '            return "blocked, still open", None',
     ["TestBlockedBy.test_pack_leaves_the_item_out_while_the_blocker_is_open"]),

    ("T306 a blocker no reader can parse is dispatched anyway",
     '            return (f"Blocked-by is {value!r}, which is not an item id, so whether the "\n'
     '                    "dependency is met cannot be told", REPAIR_CANCEL)',
     "            return None",
     ["TestBlockedBy.test_an_unreadable_value_excludes_the_item"]),

    ("T306 a Blocked-by marker where no gate reads it stops excluding",
     "        if markers > len(segs):\n"
     '            return (f"a **{name}:** marker sits where no gate reads it',
     '        if markers > len(segs) and name != "Blocked-by":\n'
     '            return (f"a **{name}:** marker sits where no gate reads it',
     ["TestBlockedBy.test_a_marker_where_no_gate_reads_it_excludes_the_item"]),

    ("T306 the blocker stops being clearable (the stale pin nobody can remove)",
     'CLEARABLE = frozenset(("Risk", "Deferred", "Env", "Blocked-by"))',
     'CLEARABLE = frozenset(("Risk", "Deferred", "Env"))',
     ["TestBlockedBy.test_edit_writes_rewrites_and_clears_the_field"]),

    ("T306 edit stops writing the blocker at all",
     '             (args.blocked_by, "Blocked-by"),', "",
     ["TestBlockedBy.test_edit_writes_rewrites_and_clears_the_field"]),

    ("T306 list stops showing which item is held back",
     '    return f"blocked by {field_value(segs[0])}"', '    return ""',
     ["TestBlockedBy.test_list_shows_the_blocker_beside_the_item"]),

    ("T306 list goes back to showing an ambiguous blocker as FREE",
     '        return "blocked ambiguously — `tk-queue pack` says why"',
     '        return ""',
     ["TestBlockedBy.test_list_marks_the_item_pack_drops_for_an_ambiguous_blocker"]),

    ("T306 list goes back to showing an unreadable marker as FREE",
     '        return "a **Blocked-by:** marker no gate reads" if markers else ""',
     '        return ""',
     ["TestBlockedBy.test_list_marks_the_item_pack_drops_for_a_marker_no_gate_reads"]),

    # --- absorbed from mutations_roster.py (T119) --------------------------
    # The roster suite's own harness was a second file because THIS one ran
    # every named test as `test_tk_queue.<name>`, hardcoded, so a roster entry
    # could not be expressed here at all. It can now: a name may carry the
    # module it lives in, and these twenty do. Their anchors live in two other
    # sources, which the 5th element has always been able to say.
    ("T128 roster any project directory counts, queue file or not",
     "if os.path.isfile(os.path.join(root, name, MEMORY_DIR, QUEUE_FILE))]", "if True]",
     ["test_tk_roster."
       "TestSweep.test_a_directory_without_the_queue_file_is_not_a_project"], ROSTER),

    ("T128 roster the queue is the done log, so a finished project is swept",
     'QUEUE_FILE = "next-steps.md"', 'QUEUE_FILE = "done-log.md"',
     ["test_tk_roster."
       "TestSweep.test_a_directory_without_the_queue_file_is_not_a_project"], ROSTER),

    ("T128 site the encoding alphabet keeps a character tk-queue replaces",
     'PROJECT_ALPHABET = "A-Za-z0-9-"', 'PROJECT_ALPHABET = "A-Za-z0-9_-"',
     ["test_tk_roster."
       "TestProjectPath.test_the_path_is_the_directory_that_encodes_to_the_name"], SITE),

    ("T128 roster a projects root that does not exist is a failure to report",
     "    except FileNotFoundError:\n"
     "        # not a failure of this machine's setup: a machine where no session ever\n"
     "        # ran has no such directory, and an empty roster is the true answer\n"
     "        return []",
     "    except FileNotFoundError:\n        fail(\"no projects root\")",
     ["test_tk_roster."
       "TestSweep.test_an_absent_projects_root_is_an_empty_roster_not_a_failure"], ROSTER),

    ("T128 roster a name no POSIX path encodes to is resolved anyway",
     '    return name.startswith("-")', "    return True",
     ["test_tk_roster."
       "TestProjectPath.test_a_name_another_machine_wrote_is_not_resolved_as_a_shorter_path"],
     ROSTER),

    ("T128 roster a queue another machine wrote is reported as a gone directory",
     "    if not encodes_a_posix_path(name):\n        return \"the name encodes no POSIX "
     "absolute path, so another machine wrote it\"\n",
     "",
     ["test_tk_roster."
       "TestProjectPath.test_a_name_another_machine_wrote_is_not_resolved_as_a_shorter_path"],
     ROSTER),

    ("T128 roster the report names the wrong list as the keeper",
     '        return "fleet-allow"', '        return "fleet-deny"',
     ["test_tk_roster."
       "TestAllowDeny.test_fleet_allow_admits_only_what_it_lists"], ROSTER),

    ("T128 roster an ambiguous name is dispatched to the first match",
     "        if len(paths) == 1:", "        if paths:",
     ["test_tk_roster."
       "TestProjectPath.test_two_directories_encoding_to_one_name_are_not_dispatchable"], ROSTER),

    ("T128 roster a symlinked directory counts as a candidate",
     "if not entry.is_dir(follow_symlinks=False):", "if not entry.is_dir(follow_symlinks=True):",
     ["test_tk_roster."
       "TestProjectPath.test_a_symlink_does_not_make_a_project_ambiguous"], ROSTER),

    ("T128 roster deny is consulted only when there is no allowlist",
     "    if any(list_key(e) == name for e in deny):",
     "    if not allow and any(list_key(e) == name for e in deny):",
     ["test_tk_roster.TestAllowDeny.test_a_name_in_both_lists_is_denied"], ROSTER),

    ("T128 roster an absent allowlist excludes everything",
     "    if allow and not any(list_key(e) == name for e in allow):",
     "    if not any(list_key(e) == name for e in allow):",
     ["test_tk_roster.TestAllowDeny.test_without_lists_every_queue_enters"], ROSTER),

    ("T128 roster the allowlist admits what it does NOT list",
     "    if allow and not any(list_key(e) == name for e in allow):",
     "    if allow and any(list_key(e) == name for e in allow):",
     ["test_tk_roster."
       "TestAllowDeny.test_fleet_allow_admits_only_what_it_lists"], ROSTER),

    ("T128 roster a list entry that is a path is matched verbatim, never encoded",
     '    return project_slug(entry) if entry.startswith("/") else entry',
     "    return entry",
     ["test_tk_roster."
       "TestAllowDeny.test_an_entry_written_as_a_path_names_the_same_project"], ROSTER),

    ("T128 roster an entry that matched nothing is passed over in silence",
     "        unmatched = [e for e in entries if list_key(e) not in listed]",
     "        unmatched = []",
     ["test_tk_roster."
       "TestAllowDeny.test_an_entry_matching_no_queue_is_reported"], ROSTER),

    ("T128 roster every entry is reported as unmatched, matched ones included",
     "        unmatched = [e for e in entries if list_key(e) not in listed]",
     "        unmatched = list(entries)",
     ["test_tk_roster."
       "TestAllowDeny.test_a_matching_entry_is_not_reported_as_unmatched"], ROSTER),

    ("T128 roster a rotten site file is read as an absent one",
     "    except tk_site.SiteError as e:\n        fail(str(e))",
     "    except tk_site.SiteError as e:\n        site = None",
     ["test_tk_roster."
       "TestSiteFile.test_a_rotten_site_file_stops_the_sweep_instead_of_ignoring_the_lists"],
     ROSTER),

    ("T128 roster an absent site file is swept without a word",
     "    if site is None:\n        print(", "    if False:\n        print(",
     ["test_tk_roster."
       "TestSiteFile.test_no_site_file_sweeps_everything_and_says_the_file_is_absent"], ROSTER),

    ("T128 site an empty fleet list reads as an absent one",
     "        if not entries:", "        if False:",
     ["test_tk_roster."
       "TestListValidation.test_an_empty_list_is_refused_not_read_as_an_absent_one"], SITE),

    ("T128 site a project name outside the encoding alphabet is accepted",
     "            if not PROJECT_NAME_RE.match(entry):", "            if False:",
     ["test_tk_roster.TestListValidation.test_a_relative_path_names_no_project",
      "test_tk_roster."
       "TestListValidation.test_a_name_outside_the_encoding_alphabet_is_refused"], SITE),

    ("T128 site an unknown key is refused instead of ignored",
     "        pairs[key] = value.strip()",
     "        pairs[key] = value.strip()\n"
     "        if key not in REQUIRED + CEILINGS + FLEET_LISTS:\n"
     '            raise SiteError(f"{path}:{n}: unknown key {key!r}.")',
     ["test_tk_roster.TestSiteFile.test_an_unknown_key_is_still_ignored"], SITE),

    # --- T301 slice 1: one parse, one structure, one writer ----------------
    # The invariant is `render_item(parse_item(b)) == b`, byte for byte, so each
    # entry here is a way the structure could stop BEING a partition of the
    # block — a piece dropped, a blank normalised, a provenance forgotten — and
    # the round-trip is what falls. A parse that only nearly gives the block back
    # is the shape in which every command rewrites text nobody pointed at.
    ("T301 the renderer drops the item's continuation lines",
     '    return item.head + item.title + "".join(f.text for f in item.fields) + item.prose',
     '    return item.head + item.title + "".join(f.text for f in item.fields)',
     ["TestOneParseOneWriter.test_every_shape_round_trips_byte_for_byte"]),

    ("T301 the parse normalises the blank between the title and the chain",
     "        title=line[len(head):chain[0][1] if chain else len(line)],",
     "        title=line[len(head):chain[0][1] if chain else len(line)].rstrip(),",
     ["TestOneParseOneWriter.test_the_blocks_the_script_itself_writes_round_trip"]),

    ("T301 a field keeps only its canonical name, so the file's own spelling is lost",
     "        self.name = segs[0][0]",
     "        self.name = canonical_field(segs[0][0]) or segs[0][0]",
     ["TestOneParseOneWriter."
      "test_a_field_carries_the_spelling_the_file_uses_and_its_canonical_name"]),

    ("T164/T166 a marker inside a code span is read as a field again",
     "            if in_code_span(spans, m.start()):\n                continue",
     "            if False:\n                continue",
     ["TestAMarkerInACodeSpanIsNotAField."
      "test_a_marker_inside_a_code_span_is_not_a_field_at_all",
      "TestAMarkerInACodeSpanIsNotAField."
      "test_the_quoted_marker_is_not_the_anchor_and_the_real_risk_survives",
      "TestAMarkerInACodeSpanIsNotAField."
      "test_the_quoted_marker_is_never_rewritten_by_an_edit"]),

    ("T301 an unmatched backtick closes on the next run of ANY width",
     "            if closer_end - closer_start == width:", "            if True:",
     ["TestOneParseOneWriter.test_an_odd_backtick_opens_no_span"]),

    ("T301 the writer drops the blank the greedy segment had swallowed",
     "        trailing = field.text[len(field.text.rstrip()):]", '        trailing = ""',
     ["TestOneParseOneWriter."
      "test_a_writer_hands_back_the_structure_and_touches_nothing_else"]),

    ("T301 a written field keeps the offsets it no longer has",
     "    def forget_offsets(self):\n        self.offsets = None",
     "    def forget_offsets(self):\n        pass",
     ["TestOneParseOneWriter.test_the_offsets_of_a_mutated_item_are_refused_not_stale"]),

    # --- T301 slice 2: the door -------------------------------------------
    # Every entry here restores a byte no reader can see. What each test proves
    # is that the item did not silently LEAVE the queue with its id still spent.
    ("T171 the marker header stops repairing the blanks nothing can see",
     '            for ch in INVISIBLE_BLANKS:',
     '            for ch in "":',
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_a_non_breaking_space_after_the_checkbox_still_names_the_item"]),

    ("T163 a BOM glued to a marker below byte 0 is left where it hides the item",
     '            fixed = head.replace(BOM, "")', "            fixed = head",
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_a_bom_glued_to_a_marker_in_the_MIDDLE_of_the_file"]),

    ("T171 a UTF-16 file is read in silence, and the conversion is a surprise",
     '            warn_once(f"{path} is UTF-16 — read as UTF-16, and the next write stores "\n'
     '                      "it as UTF-8, which is what this script emits.")',
     "            pass",
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_a_utf16_file_is_read_and_the_warning_says_what_the_next_write_does"]),

    ("T171 bytes that decode as nothing go back to a raw traceback",
     '        fail(f"{path} is not valid utf-8: byte {e.start} is {data[e.start]:#04x}. "\n'
     '             "Nothing was read. These files are written only by `tk-queue`, so a "\n'
     '             "file it cannot decode came from somewhere else — convert it to UTF-8 "\n'
     '             "and run the command again.")',
     "        raise",
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_bytes_that_are_no_encoding_name_the_file_the_byte_and_the_encoding"]),

    ("T161 a line of only SPACES closes the item block again",
     '        elif kind.startswith("item") and (line.strip("\\r\\n") == ""',
     '        elif kind.startswith("item") and (line.strip() == ""',
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_a_continuation_line_of_only_spaces_does_not_split_the_item"]),

    ("T171 `list` stops naming a class value that is no class",
     "    return cls if cls and cls not in CLASSES else None", "    return None",
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_a_class_value_outside_the_enum_is_named_not_displayed_as_valid"]),

    ("T171 `pack` reads an invented class as a STATE the item is in",
     "    if cls is not None and cls not in CLASSES:", "    if False:",
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_a_class_value_outside_the_enum_is_named_not_displayed_as_valid"]),

    ("T301 the door decodes but stops repairing the marker headers",
     "    text, repaired = normalize_marker_headers(text)", "    repaired = 0",
     ["TestTheDoorNormalisesWhatNoReaderCanSee."
      "test_the_round_trip_holds_over_the_NORMALISED_text"]),

    # --- T301 slice 3: the code-span rule and the value grammar ------------
    ("T134 the embedded-marker guard keeps a grammar of its own",
     "        if val and markers(val):",
     "        if val and FIELD_MARKER_ANY_RE.search(val):",
     ["TestAMarkerInACodeSpanIsNotAField.test_the_remedy_the_pack_prints_is_ACCEPTED_by_the_guard"]),

    ("T065/T166 the guard stops refusing a BARE marker in free text",
     "        if val and markers(val):", "        if False:",
     ["TestAMarkerInACodeSpanIsNotAField.test_a_BARE_marker_in_free_text_is_still_refused"]),

    ("T063 the whole-block value reads go back to a blind search",
     "    for _, _, end in markers(text, field):",
     "    for _, _, end in [(0, 0, m.end()) for m in FIELD_MARKER_ANY_RE.finditer(text)\n"
     "                      if canonical_field(m.group(1)) == field]:",
     ["TestAMarkerInACodeSpanIsNotAField.test_list_groups_it_under_the_real_tag_not_the_quoted_one"]),

    ("T164/T166 the marker COUNT goes back to a blind whole-block count",
     "    return real_fields(block, field), len(markers(block, field))",
     "    return real_fields(block, field), len(re.findall(\n"
     '        r"\\*\\*(?:" + FIELD_VARIANTS[field] + r"):\\*\\*", block))',
     ["TestAMarkerInACodeSpanIsNotAField."
      "test_pack_stops_excluding_it_for_a_marker_no_gate_reads"]),

    # T258 takes a two-part mutant: the truncating body ALONE no longer breaks
    # the chain, because the anchoring condition it used to trip became
    # structural. Restoring the defect means restoring both halves.
    ("T258 the value stops at the first asterisk, and the chain has to reach the line end",
     ["    marks = markers(line)\n"
      "    return [(m[0], m[1], marks[i + 1][1] if i + 1 < len(marks) else len(line))\n"
      "            for i, m in enumerate(marks)]",
      "    segs = field_segments(line)\n    if not segs:\n        return []"],
     ['    marks = markers(line)\n'
      '    return [(m[0], m[1], m[2] + len(re.match(r"[^*\\n]*", line[m[2]:]).group(0)))\n'
      "            for i, m in enumerate(marks)]",
      "    segs = field_segments(line)\n"
      "    if not segs or segs[-1][2] < len(line.rstrip()):\n        return []"],
     ["TestAMarkerInACodeSpanIsNotAField.test_an_asterisk_in_a_value_no_longer_cuts_the_chain"]),

    ("T258 an unmatched backtick swallows the rest of the line",
     "        for j in range(i + 1, len(runs)):\n"
     "            closer_start, closer_end = runs[j]\n"
     "            if closer_end - closer_start == width:\n"
     "                spans.append((opener_start, closer_end))\n"
     "                i = j\n"
     "                break\n"
     "        i += 1",
     "        spans.append((opener_start, len(line)))\n"
     "        i += 1",
     ["TestAMarkerInACodeSpanIsNotAField.test_an_odd_backtick_leaves_the_field_a_field"]),
]


def qualify(name):
    """(module, `Class.method`) for one entry's test name.

    An entry writes `Class.method` and means this harness's own suite, or
    `module.Class.method` and says which suite it means. The FIRST component
    decides: a test module is `test_<something>` and a TestCase class is
    `Test<Something>`, so a leading lowercase `test_` is a module and nothing
    else is. Counting dots was the first rule here and it was wrong for the one
    caller that hands over a whole class — the baseline runs `module.Class`, two
    components naming a module, and every one of them was read as a class of
    this harness's own suite (58 load errors, measured).

    This one line is what a second harness file used to be. `mutations_roster.py`
    existed because the module was hardcoded HERE — its own docstring said so and
    said the merge was this — while its twenty entries already carried the 5th
    element naming their source. Two runners, two baselines and two reports for
    one missing prefix."""
    module, _, rest = name.partition(".")
    if module.startswith("test_") and rest:
        return module, rest
    return TEST_MODULE, name


def run_suite(tk_dir, names):
    tests = os.path.join(tk_dir, "tests")
    argv = [sys.executable, "-m", "unittest", "-v"]
    argv += [f"{module}.{rest}" for module, rest in map(qualify, names)]
    return subprocess.run(argv, cwd=tests, capture_output=True, text=True)


def names_by_module(names):
    """{module: [`Class.method`, …]} — the entry's names, sorted by the suite each
    one lives in, so a check that needs a module object asks the right one."""
    out = {}
    for module, rest in map(qualify, names):
        out.setdefault(module, []).append(rest)
    return out


def baseline_classes(module_obj):
    """The classes the baseline runs — DERIVED from the module, never listed.

    A hand-kept list is a list someone forgets, and a class left out of it drops
    out of the baseline AND out of the orphan check at the same time: both
    watchers go blind at once, in silence. The list this replaced had forgotten
    TestPackLaneUnderWay and TestEverySpawnCarriesTheRedirectedHome, so neither
    ran before a mutation was applied and a suite already red there could not
    have been told from one the mutant reddened."""
    return list(test_classes(module_obj))


def pairs_of(entry):
    """An entry's (old, new) pairs — one, or a list applied in order."""
    old, new = entry[1], entry[2]
    if isinstance(old, (list, tuple)):
        return list(zip(old, new))
    return [(old, new)]


def per_module(mutations, module):
    """`mutations` carrying only the names that belong to `module`, entries with
    none of them dropped.

    It is what lets a check written for ONE suite be asked of a list that now
    carries two: `misnamed` and `unproved` both resolve a name against a module
    object, and neither needs to learn that a name may say which module."""
    out = []
    for entry in mutations:
        names = names_by_module(entry[3]).get(module)
        if names:
            out.append((entry[0], entry[1], entry[2], names) + tuple(entry[4:]))
    return out


def modules_missing(mutations, modules):
    """Entries naming a MODULE this run did not load — the misnamed check one
    level up. A name whose module nothing resolves would otherwise be dropped by
    `per_module` and never asked about by anybody."""
    return sorted(f"{entry[0]} -> {name}" for entry in mutations for name in entry[3]
                  if qualify(name)[0] not in modules)


def entry_problem(entry, modules, source):
    """Why this entry cannot be replayed, as (kind, why) — or None when it can.

    Every reason here means the entry proves NOTHING, and one of them used to be
    invisible: the runner reads a non-zero exit as "the named test fell", so an
    entry naming a test that does not exist reported itself as a mutant killed.

    `modules` is {module name: module object} rather than one module, because an
    entry may name tests in either suite this list now carries, and the question
    "does this test exist" is only answerable against the module it lives in.

    The checks are per PAIR, and one bad pair disqualifies the entry: a paired
    mutation whose second edit did not land is a DIFFERENT mutation from the one
    the label names, and it would be scored under that name."""
    absent = modules_missing([entry], modules)
    if absent:
        return "MISNAMED", f"names a module that is not loaded: {', '.join(absent)}"
    gone = [name for name in entry[3]
            if misnamed([(entry[0], "a", "b", [qualify(name)[1]])],
                        modules[qualify(name)[0]])]
    if gone:
        return "MISNAMED", f"names a test that does not exist: {', '.join(gone)}"
    pairs = pairs_of(entry)
    if not pairs or any(o == n for o, n in pairs):
        return "UNRUNNABLE", "the mutation is a no-op: old == new"
    counts = [source.count(o) for o, _ in pairs]
    if any(c != 1 for c in counts):
        # NOT a survivor: the mutation never ran, so it says nothing about the
        # suite. It is still a failure — a stale anchor silently stops proving
        # whatever it used to prove — but calling it "survived" would be a lie
        return "UNRUNNABLE", f"anchor matched {', '.join(str(c) for c in counts)}x, not once"
    return None


def load_check(tk_dir, rel):
    """None when the mutated file at `rel` imports cleanly, else the error's first
    line. A SEPARATE interpreter, because a broken module must not be imported into
    the harness's own process — and because "does it load" is exactly the question
    the test subprocesses will ask of it a moment later, asked the same way.

    Every source under `bin/` is a Python module: the CLIs carry no `.py` extension,
    so they are loaded through SourceFileLoader rather than by name."""
    path = os.path.join(tk_dir, rel)
    probe = ("import importlib.machinery as m, importlib.util as u, sys;"
             "l = m.SourceFileLoader('mutant', sys.argv[1]);"
             "s = u.spec_from_loader('mutant', l);"
             "l.exec_module(u.module_from_spec(s))")
    try:
        r = subprocess.run([sys.executable, "-c", probe, path],
                           capture_output=True, text=True,
                           # a mutant that hangs on import must not stop the harness
                           # with no diagnostic; no entry needs anything like this long
                           timeout=60,
                           # the module the CLIs import sits beside them
                           cwd=os.path.dirname(path))
    except subprocess.TimeoutExpired:
        return "import did not finish in 60s"
    if r.returncode == 0:
        return None
    tail = [ln for ln in r.stderr.strip().splitlines() if ln.strip()]
    return tail[-1] if tail else f"exit {r.returncode}"


def main():
    # BOTH suites, because the list names tests in both: a baseline over one of
    # them would leave the other's red — from a defect that was already there —
    # indistinguishable from a mutant this run reddened
    modules = {name: load_module(name, TK_DIR) for name in TEST_MODULES}
    baseline_names = [f"{name}.{cls}" for name, obj in modules.items()
                      for cls in baseline_classes(obj)]
    baseline = run_suite(TK_DIR, baseline_names)
    if baseline.returncode != 0:
        print("BASELINE IS RED — fix the suite before mutating\n", baseline.stderr[-3000:])
        return 1

    # per suite, and reported per suite, because the DEBT is per suite: the
    # ceilings below are two numbers and each one only ever goes down
    orphans = {name: unproved(per_module(MUTATIONS, name), obj)
               for name, obj in modules.items()}
    for module, names in orphans.items():
        for name in names:
            print(f"UNPROVED   {module}.{name} — no mutation entry names this test")
    if any(orphans.values()):
        print()

    sources = {}
    for entry in MUTATIONS:
        rel = entry[4] if len(entry) > 4 else DEFAULT_SRC
        if rel not in sources:
            with open(os.path.join(TK_DIR, rel), encoding="utf-8") as f:
                sources[rel] = f.read()
    survived, unrunnable, fictitious = [], [], []
    for entry in MUTATIONS:
        label, old, new, names = entry[:4]
        rel = entry[4] if len(entry) > 4 else DEFAULT_SRC
        src = sources[rel]
        problem = entry_problem(entry, modules, src)
        if problem is not None:
            kind, why = problem
            (fictitious if kind == "MISNAMED" else unrunnable).append(f"{label} ({why})")
            print(f"{kind:10} {label}\n           {why}")
            continue
        mutated = src
        for o, n in pairs_of(entry):
            mutated = mutated.replace(o, n, 1)
        tmp = tempfile.mkdtemp(prefix="tk-mutation.")
        try:
            dst = os.path.join(tmp, "tk")
            # NOT the bytecode cache. copytree preserves mtimes, so a copied
            # __pycache__ entry still matches its (copied) source's mtime and
            # size — and Python then imports the PRE-MUTATION bytecode, which
            # reports a guard as unprotected when it is merely unmutated
            shutil.copytree(TK_DIR, dst, ignore=shutil.ignore_patterns("__pycache__"))
            with open(os.path.join(dst, rel), "w", encoding="utf-8") as f:
                f.write(mutated)
            # THE MUTANT MUST RUN BEFORE A FAILURE MEANS ANYTHING. Every named test
            # falls when the mutated source cannot be loaded at all, whatever the
            # guard it was meant to switch off does — so the harness would score the
            # entry "caught" while exercising nothing. Measured twice, one layer
            # apart: an edit that broke the implicit concatenation of two adjacent
            # string literals (a SyntaxError), and an edit that left a regex
            # unbalanced, which PARSES and then raises re.error the moment the module
            # is imported. Asking the question the first way — `ast.parse` — closed
            # the first door and left the second open, so it is asked the way that
            # has no layers: LOAD the mutated tree and require it to come up.
            loaded = load_check(dst, rel)
            if loaded is not None:
                unrunnable.append(f"{label} (mutated source does not load: {loaded})")
                print(f"UNRUNNABLE {label}\n           mutated source does not load: {loaded}")
                continue
            # EACH named test must fall on its own. Running them as one batch only
            # proves that SOME test failed, so a listed test that quietly still
            # passes stays invisible and the tally claims more than it proved
            still_passing = [n for n in names if run_suite(dst, [n]).returncode == 0]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if still_passing:
            survived.append(f"{label} → {', '.join(still_passing)} still passed")
            print(f"SURVIVED   {label}\n           {', '.join(still_passing)} still passed")
        else:
            print(f"caught     {label}\n           → all {len(names)} named test(s) fell")

    ran = len(MUTATIONS) - len(unrunnable) - len(fictitious)
    print(f"\n{ran - len(survived)}/{ran} mutations caught"
          + (f" ({len(unrunnable)} could not run)" if unrunnable else "")
          + (f" ({len(fictitious)} name no such test)" if fictitious else "")
          + ", " + " + ".join(f"{len(names)} in {module}"
                              for module, names in orphans.items())
          + " test(s) no entry proves")
    for title, items in (("SURVIVORS (the suite does not actually protect these)", survived),
                         ("UNRUNNABLE (stale anchor — proves nothing until fixed)", unrunnable),
                         ("MISNAMED (names no such test — scored as nothing, never as a kill)",
                          fictitious)):
        if items:
            print(f"{title}:")
            for i in items:
                print("  -", i)
    grown = []
    for name, ceiling, count, what in (
            ("KNOWN_MISNAMED", KNOWN_MISNAMED, len(fictitious), "misnamed entries"),
            ("KNOWN_UNPROVED", KNOWN_UNPROVED, len(orphans[TEST_MODULE]),
             "tests no entry proves"),
            ("KNOWN_UNPROVED_ROSTER", KNOWN_UNPROVED_ROSTER,
             len(orphans[ROSTER_TEST_MODULE]), "roster tests no entry proves")):
        if count > ceiling:
            grown.append(f"{name} records {ceiling} {what} and this run found {count}")
        elif count < ceiling:
            print(f"\n{name} says {ceiling} and this run found only {count} {what} — "
                  "lower the constant, or the ratchet stops biting")
    for line in grown:
        print(f"\n{line}: the debt grew")
    return 1 if survived or unrunnable or grown else 0


if __name__ == "__main__":
    sys.exit(main())
