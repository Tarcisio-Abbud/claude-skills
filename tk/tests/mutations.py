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

# (label, old, new, [test names that must fail]) — plus an optional 5th element,
# the source file the anchor lives in, relative to tk/ (default: bin/tk-queue).
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
     '        line += f" **Project:** {tag_m.group(1)}."',
     '        pass',
     ["TestProjectTagInDoneLog.test_tag_reaches_the_done_log",
      "TestProjectTagInDoneLog.test_report_groups_by_tag_untagged_last"]),

    ("T064 --summary drops the tag (tag read from the title instead of the block)",
     "tag_m = PROJECT_TAG_RE.search(block)",
     "tag_m = PROJECT_TAG_RE.search(args.summary or item_title(block, limit=400))",
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
     'EMBEDDED_MARKER_RE = re.compile(r"\\*\\*(?:" + ANY_FIELD + r"):\\*\\*")',
     'EMBEDDED_MARKER_RE = re.compile(r"(?!x)x")',
     ["TestEmbeddedMarker.test_add_refuses_a_marker_in_the_text"]),

    # the opposite direction, which no other mutation covers: a guard that over-refuses
    # blocks legitimate prose, and only the false-positive test can see it
    ("T065 the guard broadens to the bare field name, refusing ordinary prose",
     'EMBEDDED_MARKER_RE = re.compile(r"\\*\\*(?:" + ANY_FIELD + r"):\\*\\*")',
     'EMBEDDED_MARKER_RE = re.compile(r"(?:" + ANY_FIELD + r")")',
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
    # real allocation invisible — measured on the live m365 queue, which carries
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
     '                if tail[:1] in ("", "\\n"):', "                if False:",
     ["TestRiskDeletion.test_no_trailing_blank_is_left_when_risk_was_the_last_field"]),

    # the same repair in the other direction: too WIDE instead of absent
    ("review#2 the blank repair sweeps the whole block again, eating a hard break",
     '                if tail[:1] in ("", "\\n"):\n'
     '                    head = head.rstrip(" \\t")\n'
     "                new = head + tail",
     '                new = re.sub(r"[ \\t]+(?=\\n|\\Z)", "", head + tail)',
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
     "                         deferred=args.deferred)",
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

    # over-trigger direction: readers write nothing, so announcing a write target
    # on `list`/`report` is noise on every read
    ("T072 readers announce a write target too",
     'READERS = frozenset(("list", "report"))', "READERS = frozenset()",
     ["TestTargetQueueAnnounced.test_readers_stay_silent"]),
    # --- review#2: the real field is the one in the CHAIN ------------------

    ("review#2 the real field is the LAST marker in the block again (note eaten)",
     "        found = [m for m in field_chain(new) if canonical_field(m.group(1)) == field]",
     '        found = list(re.finditer(r"\\*\\*(?:" + FIELD_VARIANTS[field] + '
     'r"):\\*\\*[^*\\n]*", new))[-1:]',
     ["TestFieldChain.test_clearing_hits_the_real_field_and_spares_the_note",
      "TestFieldChain.test_setting_hits_the_real_field_and_spares_the_note"]),

    ("T065/review#2 the real field is the FIRST marker in the block again (prose eaten)",
     "        found = [m for m in field_chain(new) if canonical_field(m.group(1)) == field]",
     '        found = list(re.finditer(r"\\*\\*(?:" + FIELD_VARIANTS[field] + '
     'r"):\\*\\*[^*\\n]*", new))[:1]',
     ["TestEmbeddedMarker.test_edit_rewrites_the_real_field_not_prose_that_looks_like_one",
      "TestFieldChain.test_a_marker_before_the_fields_is_still_prose",
      "TestRiskDeletion.test_clearing_rewrites_the_real_field_not_prose_that_looks_like_one"]),

    ("review#2 the chain admits prose (the period discriminator goes away)",
     '        ends_field = (m.group(0).rstrip().endswith(".")\n'
     '                      or canonical_field(m.group(1)) == "Source")',
     "        ends_field = True",
     ["TestEmbeddedMarker.test_edit_rewrites_the_real_field_not_prose_that_looks_like_one",
      "TestFieldChain.test_a_marker_before_the_fields_is_still_prose"]),

    ("review#2 the chain stops at Source (fields appended after it become unreachable)",
     '                      or canonical_field(m.group(1)) == "Source")',
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
     "        if len(found) > 1:", "        if False:",
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
     'CLEARABLE = frozenset(("Risk", "Deferred", "Env"))',
     'CLEARABLE = frozenset(("Risk", "Env"))',
     ["TestDecisionDeferralGate.test_leaving_the_decision_class_takes_the_deferral_with_it"]),

    ("T119 add stops measuring the justification against the field ceiling",
     "                         criterion=args.criterion, project=args.project, "
     "source=args.source,\n"
     "                         deferred=args.deferred)",
     "                         criterion=args.criterion, project=args.project, "
     "source=args.source)",
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
     '    path = os.path.join(memdir, "next-steps.md")',
     '    path = os.path.join(memdir, "next-steps.md")\n'
     "    content = read(path) or \"\"\n"
     '    block, start = next(((t, 0) for k, t in split_blocks(content)\n'
     '                         if k == "item-open" and item_id(t) == args.id), ("", 0))',
     ["TestBump.test_an_unknown_id_is_diagnosed_and_nothing_moves"]),

    ("T119 list orders its groups alphabetically, so a bump is invisible",
     "                            for label, cls, title, project in rows], by_position=True)",
     "                            for label, cls, title, project in rows])",
     ["TestBump.test_a_bump_shows_in_list_on_a_tagged_queue_too"]),

    ("T119 bump counts as a reader, so it takes no lock and names no queue",
     'READERS = frozenset(("list", "report"))',
     'READERS = frozenset(("list", "report", "bump"))',
     ["TestTargetQueueAnnounced.test_every_mutating_command_names_the_memdir_on_stderr"]),

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

    ("2ª review a Deferred anywhere in the chain counts, so prose satisfies the gate",
     '        seg = next((m for i, m in enumerate(chain)\n'
     '                    if names[i] == "Deferred" and i > after), None)',
     '        seg = next((m for i, m in enumerate(chain)\n'
     '                    if names[i] == "Deferred"), None)',
     ["TestDecisionDeferralGate."
      "test_prose_that_looks_like_a_deferral_never_satisfies_the_gate"]),

    ("2ª review the stray marker is ignored instead of refused (prose gets deleted)",
     "    if stray and (args.classe or args.deferred is not None):", "    if False:",
     ["TestDecisionDeferralGate."
      "test_prose_that_looks_like_a_deferral_never_satisfies_the_gate"]),

    # the over-refusal direction: a guard that fires on every edit of such an item
    # makes it uneditable, which is worse than the shape it protects against
    ("2ª review the stray guard fires even when the edit never touches the deferral",
     "    if stray and (args.classe or args.deferred is not None):", "    if stray:",
     ["TestDecisionDeferralGate.test_an_edit_that_never_consults_the_deferral_stays_allowed"]),

    # --- 2nd pair of eyes: an item's TEXT is not its ADDRESS ------------------

    ("2ª review the block is addressed by its TEXT again (a quoted copy wins)",
     "            return content, text, pos",
     "            return content, text, content.index(text)",
     ["TestBlockAddressing.test_done_closes_the_real_item_and_spares_the_quoted_copy",
      "TestBlockAddressing.test_bump_moves_the_real_item_and_leaves_no_phantom",
      "TestBlockAddressing.test_edit_rewrites_the_real_item_and_not_the_quotation"]),

    # --- re-check of the FIX: the corruption the fix itself shipped -----------

    ("re-check the clearing branch shadows the item's offset in the FILE",
     "                f_start, f_end = found[0].span()\n"
     "                head, tail = new[:f_start], new[f_end:]",
     "                start, end = found[0].span()\n"
     "                head, tail = new[:start], new[end:]",
     ["TestClearingKeepsTheFileIntact.test_clearing_a_risk_rewrites_only_that_field",
      "TestClearingKeepsTheFileIntact.test_clearing_a_deferral_rewrites_only_that_field"]),

    ("re-check the gate reads the class the loose way `list` displays it",
     "    result_class = args.classe or chain_class(block)",
     "    result_class = args.classe or item_class(block)",
     ["TestDecisionDeferralGate.test_a_class_named_only_in_prose_does_not_open_the_gate"]),

    ("re-check an ambiguous class in the chain is guessed instead of refused",
     "    if len(found) != 1:\n        return None",
     "    if not found:\n        return None",
     ["TestDecisionDeferralGate.test_a_class_named_only_in_prose_does_not_open_the_gate"]),

    ("re-check a deferral counts with no Class in the chain to qualify",
     '    if "Class" in names:\n        after = names.index("Class")',
     '    if True:\n        after = names.index("Class") if "Class" in names else -1',
     ["TestDecisionDeferralGate.test_a_chain_with_no_class_carries_no_deferral_to_find"]),

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
     "    validate_env(args.env)\n    path = os.path.join(memdir, \"next-steps.md\")",
     '    path = os.path.join(memdir, "next-steps.md")',
     ["TestEnvField.test_add_refuses_a_value_outside_the_roster"]),

    ("T120 edit stops validating the env",
     "    validate_env(args.env)\n    # before the deferral gate",
     "    # before the deferral gate",
     ["TestEnvField.test_edit_refuses_it_too"]),

    ("T120 add writes an Env line for the reserved clear word",
     "    if args.env and not clears_field(args.env):", "    if args.env:",
     ["TestEnvField.test_add_writes_no_field_for_the_reserved_word"]),

    ("T120 the field moves out of the position the package filter reads",
     '    if args.env and not clears_field(args.env):\n'
     '        fields.append(f"**Env:** {args.env}.")\n'
     '    fields.append(f"**Criterion:** {args.criterion}.")',
     '    fields.append(f"**Criterion:** {args.criterion}.")\n'
     '    if args.env and not clears_field(args.env):\n'
     '        fields.append(f"**Env:** {args.env}.")',
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
     'CLEARABLE = frozenset(("Risk", "Deferred", "Env"))',
     'CLEARABLE = frozenset(("Risk", "Deferred"))',
     ["TestEnvField.test_the_reserved_word_clears_the_field_and_leaves_the_file_intact",
      "TestEnvField.test_clearing_needs_no_site_file_at_all"]),

    ("T120 edit stops writing the field at all",
     "                        (args.risk, \"Risk\"), (args.env, \"Env\"),",
     '                        (args.risk, "Risk"),',
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
     "        fail(str(e))",
     "    site = tk_site.load()",
     ["TestEnvField.test_an_absent_identity_is_refused"]),

    ("T120 site the ceilings become mandatory",
     "        if key not in pairs:\n            continue",
     "        if key not in pairs:\n            raise SiteError(missing_key_message(path, key, pairs))",
     ["TestEnvField.test_the_ceilings_are_optional"],
     "bin/tk_site.py"),

    ("2ª review edit splices by search-and-replace again",
     "    write_atomic(os.path.join(memdir, \"next-steps.md\"),\n"
     "                 content[:start] + new + content[start + len(block):])",
     "    write_atomic(os.path.join(memdir, \"next-steps.md\"), "
     "content.replace(block, new, 1))",
     ["TestBlockAddressing.test_edit_rewrites_the_real_item_and_not_the_quotation"]),
]


def run_suite(tk_dir, names):
    tests = os.path.join(tk_dir, "tests")
    argv = [sys.executable, "-m", "unittest", "-v"] + [f"test_tk_queue.{n}" for n in names]
    return subprocess.run(argv, cwd=tests, capture_output=True, text=True)


def main():
    baseline = run_suite(TK_DIR, ["TestPrefixedId", "TestConcurrency", "TestMissingItemMessage",
                                  "TestDirResolution", "TestProjectTagInDoneLog",
                                  "TestEmbeddedMarker", "TestAtomicWrite",
                                  "TestRiskDeletion", "TestCeilingScope",
                                  "TestTargetQueueAnnounced", "TestFieldChain",
                                  "TestCloseFieldCeilings", "TestIdAllocationScope",
                                  "TestDoneLogLineGrammar", "TestCanonicalHead",
                                  "TestDecisionDeferralGate", "TestBump",
                                  "TestBlockAddressing", "TestClearingKeepsTheFileIntact",
                                  "TestEnvField"])
    if baseline.returncode != 0:
        print("BASELINE IS RED — fix the suite before mutating\n", baseline.stderr[-3000:])
        return 1

    sources = {}
    for entry in MUTATIONS:
        rel = entry[4] if len(entry) > 4 else DEFAULT_SRC
        if rel not in sources:
            with open(os.path.join(TK_DIR, rel), encoding="utf-8") as f:
                sources[rel] = f.read()
    survived, unrunnable = [], []
    for entry in MUTATIONS:
        label, old, new, names = entry[:4]
        rel = entry[4] if len(entry) > 4 else DEFAULT_SRC
        src = sources[rel]
        if src.count(old) != 1:
            # NOT a survivor: the mutation never ran, so it says nothing about the
            # suite. It is still a failure — a stale anchor silently stops proving
            # whatever it used to prove — but calling it "survived" would be a lie
            unrunnable.append(f"{label} (anchor matched {src.count(old)}x, not once)")
            print(f"UNRUNNABLE {label}\n           anchor matched {src.count(old)}x, not once")
            continue
        tmp = tempfile.mkdtemp(prefix="tk-mutation.")
        try:
            dst = os.path.join(tmp, "tk")
            # NOT the bytecode cache. copytree preserves mtimes, so a copied
            # __pycache__ entry still matches its (copied) source's mtime and
            # size — and Python then imports the PRE-MUTATION bytecode, which
            # reports a guard as unprotected when it is merely unmutated
            shutil.copytree(TK_DIR, dst, ignore=shutil.ignore_patterns("__pycache__"))
            with open(os.path.join(dst, rel), "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
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
