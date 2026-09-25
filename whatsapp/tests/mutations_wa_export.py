#!/usr/bin/env python3
"""Mutation proof for `test_wa_export.py`.

Each mutation restores one defect the script exists to avoid, then requires the tests named
for it to FAIL. A test that still passes with the defect back guards nothing.

Two checks keep the harness honest, both borrowed from `githooks/tests`:

- a test named by a mutation must EXIST, or a typo reports as a killed mutant;
- every test in the suite is enumerated, and any test no mutation names is reported
  UNPROVED, because a score of 100% only ever measures the mutants that were written.

Run: python3 whatsapp/tests/mutations_wa_export.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.abspath(os.path.join(HERE, os.pardir, "bin", "wa_export.py"))

# name -> (what the defect is, the literal to replace, its replacement, tests it must kill)
MUTATIONS = [
    (
        "the message key carries the clock, so a drifting minute reads as an edit",
        'return (self.date, self.sender, " ".join(self.body.split()))',
        'return (self.date, self.time, self.sender, " ".join(self.body.split()))',
        ["test_a_minute_that_moved_is_not_a_change"],
    ),
    (
        "the folded filename is tried before the exact one",
        "NAME_FORMS = (plain_name, normalize_attachment)",
        "NAME_FORMS = (normalize_attachment, plain_name)",
        ["test_the_dedup_suffix_does_not_hand_the_file_to_the_older_message"],
    ),
    (
        "a form is tried message by message, so a fallback match beats a later exact one",
        "    for form in NAME_FORMS:\n"
        "        wanted = form(name)\n"
        "        for message in messages:",
        "    for message in messages:\n"
        "        for form in NAME_FORMS:\n"
        "            wanted = form(name)\n"
        "            _ = message\n"
        "        for message in messages:",
        ["test_the_dedup_suffix_does_not_hand_the_file_to_the_older_message"],
    ),
    (
        "a replace block pairs positionally, marrying a dropped message to an unrelated new one",
        "                if old is not None and new is not None and \\\n"
        "                        old.date == new.date and old.sender == new.sender:",
        "                if old is not None and new is not None:",
        [
            "test_a_message_that_vanished_is_an_anomaly",
            "test_force_diffs_an_unrelated_pair_anyway",
        ],
    ),
    (
        "every message of the new export is reported as new",
        'if tag == "equal":\n            matched += j2 - j1',
        'if tag == "equal":\n            matched += j2 - j1\n            added.extend(new_messages[j1:j2])',
        [
            "test_only_the_new_messages_come_back",
            "test_nothing_new_is_reported_as_nothing",
        ],
    ),
    (
        "a continuation line starts a message of its own instead of joining the one above",
        "            if messages:\n"
        "                messages[-1].body += \"\\n\" + clean\n"
        "                messages[-1].raw += \"\\n\" + line\n"
        "            continue",
        "            continue",
        ["test_a_multiline_message_stays_whole"],
    ),
    (
        "the line number counts messages rather than lines",
        "                line=lineno,",
        "                line=len(messages) + 1,",
        ["test_the_new_messages_carry_their_line_numbers"],
    ),
    (
        "the sender is split off the LAST colon, so a colon in the body becomes the sender",
        'head, sep, tail = rest.partition(": ")',
        'head, sep, tail = rest.rpartition(": ")',
        ["test_a_colon_in_the_body_does_not_become_the_sender"],
    ),
    (
        "a two-digit year is not the same day as a four-digit one",
        '    if len(year) == 2:\n        year = "20" + year\n',
        "",
        ["test_a_short_year_is_the_same_day_as_a_long_one"],
    ),
    (
        "the square bracket of the iOS header is not consumed, so that shape never matches",
        '    r"^\\[?"\n',
        '    r"^"\n',
        ["test_the_ios_bracket_format_parses"],
    ),
    (
        "the chat transcript is counted as an attachment",
        "            if info.is_dir() or info.filename == chat_member:",
        "            if info.is_dir():",
        ["test_the_chat_transcript_is_not_an_attachment"],
    ),
    (
        "every attachment of the new export is reported as new",
        "        previous = old_index.get(name)\n        if previous is None:",
        "        previous = old_index.get(name)\n        if True:",
        ["test_only_the_new_files_come_back"],
    ),
    (
        "a file whose bytes moved under the same name passes unremarked",
        "        elif previous.CRC != info.CRC or previous.file_size != info.file_size:\n"
        "            modified.append(info)",
        "        elif False:\n            modified.append(info)",
        ["test_a_file_whose_bytes_moved_is_reported_apart"],
    ),
    (
        "extraction copies the whole export instead of the new members",
        "        for info in infos:\n"
        "            base = rename.get(info.filename) or os.path.basename(info.filename)",
        "        for info in archive.infolist():\n"
        "            base = rename.get(info.filename) or os.path.basename(info.filename)",
        ["test_the_attachments_are_extracted_beside_the_digest"],
    ),
    (
        "no extension counts as audio, so a new voice note is never flagged",
        'AUDIO_EXTS = (".opus", ".ogg", ".m4a", ".mp3", ".wav", ".aac", ".flac", ".amr")',
        'AUDIO_EXTS = (".nothing",)',
        [
            "test_a_new_voice_note_is_named_as_pending",
            "test_the_transcription_command_is_ready_to_paste",
        ],
    ),
    (
        "the transcript is never credited to the message that sent the voice note",
        '    """The same search as `owning_message`, over the records `diff` wrote to disk."""',
        '    """The same search as `owning_message`, over the records `diff` wrote to disk."""\n'
        "    return None",
        ["test_transcripts_fold_into_the_digest_with_who_and_when"],
    ),
    (
        "a missing transcript is treated as an empty one instead of refused",
        '    if transcript_path is None:\n'
        '        fail("no transcript.jsonl in %s — transcribe the voice notes first." % out_dir)',
        "    if transcript_path is None:\n        return 0",
        ["test_transcripts_refuses_when_nothing_was_transcribed"],
    ),
    (
        "a longer neighbour is accepted as the predecessor",
        "        if count and count <= new_count:",
        "        if count:",
        ["test_a_longer_neighbour_is_not_a_predecessor"],
    ),
    (
        "any neighbouring export is a candidate, whatever conversation it holds",
        "        if conversation_title(member, path) != title:\n            continue",
        "        if False:\n            continue",
        ["test_another_conversation_is_not_a_predecessor"],
    ),
    (
        "no predecessor is searched for at all",
        "    if not candidates:\n        return None\n    return max(candidates)[1]",
        "    return None",
        ["test_the_previous_export_is_found_beside_the_new_one"],
    ),
    (
        "a missing predecessor crashes instead of saying which flag names one",
        '        if old_zip is None:\n            fail("no earlier export of this conversation',
        '        if False:\n            fail("no earlier export of this conversation',
        ["test_no_predecessor_is_refused_rather_than_guessed"],
    ),
    (
        "two unrelated exports are diffed rather than refused",
        "    if old_zip is not None and delta.overlap < args.min_overlap and not args.force:",
        "    if False:",
        ["test_an_unrelated_pair_is_refused"],
    ),
    (
        "--first is ignored, so an export with no predecessor is refused anyway",
        "    if args.first:\n        old_zip = None\n    else:",
        "    if False:\n        old_zip = None\n    else:",
        [
            "test_a_first_export_is_read_whole_instead_of_refused",
            "test_a_first_export_does_not_claim_a_previous_one",
        ],
    ),
    (
        "the refusal names no way to read an export that has no predecessor",
        '            fail("no earlier export of this conversation in %s — pass --previous, or --first "\n'
        "                 \"to read this export whole as the conversation's first reading.\"",
        '            fail("no earlier export of this conversation in %s — pass --previous."',
        ["test_the_refusal_offers_the_flag_that_reads_the_export_whole"],
    ),
    (
        "the digest of a first export reports a previous export that does not exist",
        '    if first:\n        add("- **Previous export:** none (`--first`).',
        '    if False:\n        add("- **Previous export:** none (`--first`).',
        ["test_a_first_export_does_not_claim_a_previous_one"],
    ),
    (
        "a first export is titled as a delta, so the whole history reads as news",
        '    add("# %s — %s" % ("The whole conversation" if first else "What is new",',
        '    add("# %s — %s" % ("What is new" if first else "What is new",',
        ["test_a_first_export_does_not_claim_a_previous_one"],
    ),
    (
        "--first and --previous are both accepted, and one of them is silently ignored",
        "    pair = diff.add_mutually_exclusive_group()",
        "    pair = diff",
        ["test_first_and_previous_contradict_each_other"],
    ),
    (
        "a pair one of whose exports is not a transcript is refused with `why: None`",
        '        return ("one of the two exports parses to no message at all, so nothing in it "\n'
        '                "vouches for the pair — that file is probably not a transcript.")',
        "        return None",
        ["test_an_empty_predecessor_confirms_nothing"],
    ),
    (
        "a refused pair whose dates are spelled in two locales is not diagnosed",
        "    if share(lambda m: (m.sender, body_of(m))) > floor:",
        "    if False:",
        ["test_a_locale_that_spells_dates_differently_is_named"],
    ),
    (
        "a refused pair exported on two phones is not diagnosed",
        "    if share(lambda m: (m.date, body_of(m))) > floor:",
        "    if False:",
        ["test_two_phones_spelling_the_senders_differently_are_named"],
    ),
    (
        "a pair spelled differently in BOTH ways falls through to `nothing in common`",
        "    if share(body_of) > floor:",
        "    if False:",
        ["test_two_phones_differing_in_BOTH_ways_are_not_called_unrelated"],
    ),
    (
        "the relaxed keys are measured against a constant, not against the strict share",
        "    floor = max(DIAGNOSIS_FLOOR, overlap)",
        "    floor = DIAGNOSIS_FLOOR",
        ["test_a_raised_floor_does_not_invent_a_locale_to_blame"],
    ),
    (
        "the strict share never reaches the diagnosis, so it is measured against 0.0",
        "                diagnose_pair(old_messages, new_messages, delta.overlap)))",
        "                diagnose_pair(old_messages, new_messages)))",
        ["test_a_raised_floor_does_not_invent_a_locale_to_blame"],
    ),
    (
        "a pair with a real partial overlap is told that nothing of it survives",
        "    if overlap > 0:",
        "    if False:",
        [
            "test_a_real_partial_overlap_is_not_reported_as_nothing_in_common",
            "test_a_raised_floor_does_not_invent_a_locale_to_blame",
        ],
    ),
    (
        "a pair with nothing in common gets no answer at all",
        '    return ("no message of the previous export survives in any form — not its date, not its "\n'
        '            "sender, not its text. Either these are two different conversations, or they are "\n'
        "            \"two members' exports of one group and the histories do not meet.\")",
        '    return ""',
        ["test_a_pair_with_nothing_in_common_says_exactly_that"],
    ),
    (
        "an attachment with no extension reaches the disk without one",
        '    rename = (stem.rstrip(".") or "attachment") + kind if ext in ("", ".") else None',
        "    rename = None",
        [
            "test_an_attachment_with_no_extension_is_saved_as_what_its_bytes_say",
            "test_the_legend_says_which_of_the_two_renamings_happened",
        ],
    ),
    (
        "a ZIP container is never opened, so a workbook is announced as an archive",
        "        for prefix, zip_ext, zip_label in ZIP_MARKERS:",
        "        for prefix, zip_ext, zip_label in ():",
        ["test_an_extensionless_workbook_is_named_by_looking_inside_the_zip"],
    ),
    (
        "a password-protected PDF passes as an ordinary one",
        '    if b"/Encrypt" in data:',
        "    if False:",
        [
            "test_a_password_protected_pdf_carries_the_command_that_opens_it",
            "test_no_command_is_offered_for_a_file_that_was_not_extracted",
        ],
    ),
    (
        "what the bytes said about an attachment never reaches the digest",
        '                "notes": probes[info.filename]["notes"] if info.filename in probes else [],',
        '                "notes": [],',
        ["test_a_password_protected_pdf_carries_the_command_that_opens_it"],
    ),
    (
        "a scan is taken for a document with text, and reads as a blank one",
        '    if b"/Font" in data or any(b"/Font" in chunk for chunk in inflated_streams(data)):\n'
        "        return notes",
        "    if True:\n        return notes",
        ["test_a_scanned_pdf_is_flagged_as_needing_rendering"],
    ),
    (
        "only the raw bytes are searched for a font, so a modern PDF is called a scan",
        '    if b"/Font" in data or any(b"/Font" in chunk for chunk in inflated_streams(data)):',
        '    if b"/Font" in data:',
        ["test_a_text_layer_inside_an_object_stream_is_not_a_scan"],
    ),
    (
        "two spellings of one kind of file count as a mismatch, and the section cries wolf",
        "    return any(left in family and right in family for family in EXT_FAMILIES)",
        "    return False",
        ["test_an_ordinary_attachment_is_not_flagged_at_all"],
    ),
    (
        "an extension the bytes contradict is passed over",
        "    elif not same_family(ext, kind):",
        "    elif False:",
        ["test_an_extension_the_bytes_contradict_is_named"],
    ),
    (
        "a command is printed for a file `--no-extract` never wrote",
        '                if note.get("command") and extracted:',
        '                if note.get("command"):',
        ["test_no_command_is_offered_for_a_file_that_was_not_extracted"],
    ),
    (
        "the legend blames a collision for every name that changed on disk",
        '        reason = "extension" if os.path.splitext(announced)[1] in ("", ".") else "collision"',
        '        reason = "collision"',
        ["test_the_legend_says_which_of_the_two_renamings_happened"],
    ),
    (
        "only the English chat filename yields a title",
        r'    r"^(?:WhatsApp Chat with|Conversa do WhatsApp com|Chat de WhatsApp con|"'
        "\n"
        r'    r"Discussion WhatsApp avec|WhatsApp Chat mit)[ ]+(?P<title>.+)\.txt$",',
        r'    r"^(?:WhatsApp Chat with)[ ]+(?P<title>.+)\.txt$",',
        ["test_the_title_survives_the_locale_of_the_chat_file"],
    ),
    (
        "`_chat.txt` becomes the conversation's name instead of the zip's",
        '    if base.lower() not in ("_chat.txt", "chat.txt"):\n        return base[:-4].strip()',
        "    if True:\n        return base[:-4].strip()",
        ["test_an_unnamed_chat_file_falls_back_to_the_zip_name"],
    ),
    (
        "the invisible marks are left in, so they split a message and hide an attachment",
        'INVISIBLE = dict.fromkeys(map(ord, "\u200e\u200f\u202a\u202c"), None)',
        "INVISIBLE = {}",
        ["test_an_invisible_mark_does_not_split_a_message"],
    ),
    (
        "only the Android attachment marker is read, so an iOS export attributes nothing",
        r'    r"|<(?:" + ATTACHED_WORDS + r"):[\u0020\u00a0]*(?P<ios>[^>]+)>",',
        r'    r"|<(?:ZZZ_NEVER):[\u0020\u00a0]*(?P<ios>[^>]+)>",',
        ["test_the_ios_attachment_marker_is_read"],
    ),
    (
        "the biggest .txt is the conversation, so a .txt attachment displaces it",
        "        chat = min(txts, key=chat_rank)",
        "        chat = min(txts, key=lambda i: (i.filename.count(\"/\"), -i.file_size))",
        ["test_a_txt_attachment_does_not_become_the_chat"],
    ),
    (
        "an export that parses to no message at all is diffed instead of refused",
        '    if not new_messages:\n        fail("%s parses to NO messages',
        '    if False:\n        fail("%s parses to NO messages',
        ["test_an_export_with_no_messages_at_all_is_refused"],
    ),
    (
        "the overlap measures the share of the NEW export, refusing a conversation that grew",
        "        return self.matched / self.total_old if self.total_old else 0.0",
        "        return self.matched / self.total_new if self.total_new else 1.0",
        ["test_a_conversation_that_exploded_is_still_the_same_pair"],
    ),
    (
        "an old export with no messages divides by zero instead of refusing the pair",
        "        return self.matched / self.total_old if self.total_old else 0.0",
        "        return self.matched / self.total_old",
        ["test_an_empty_predecessor_confirms_nothing"],
    ),
    (
        "the tally line is built the same way whether or not anything was unplaced",
        '    return "nothing — every line and every file is placed" if not parts else "; ".join(parts)',
        '    return "; ".join(parts)',
        ["test_the_tally_is_clean_when_everything_is_placed"],
    ),
    (
        "an attachment the new export dropped passes unremarked",
        "    dropped = [info for name, info in old_index.items() if name not in new_index]",
        "    dropped = []",
        ["test_an_attachment_the_previous_export_had_is_an_anomaly"],
    ),
    (
        "a run lands on top of a previous run's delta directory",
        "    if os.listdir(out_dir):\n        fail(\"%s is not empty",
        "    if False:\n        fail(\"%s is not empty",
        ["test_a_second_run_will_not_land_on_the_first"],
    ),
    (
        "an overwriting run leaves the previous run's attachments in place",
        "        if args.overwrite and os.path.isdir(attachments_dir):",
        "        if False and os.path.isdir(attachments_dir):",
        ["test_an_overwriting_run_clears_the_old_attachments"],
    ),
    (
        "two members sharing a basename overwrite each other on extraction",
        "            if base in taken or os.path.exists(target):",
        "            if False:",
        ["test_two_members_sharing_a_basename_are_both_extracted"],
    ),
    (
        "the new messages report as ONE spanning range, covering lines nobody added",
        "        if runs and start <= runs[-1][1] + 1:",
        "        if runs:",
        ["test_the_new_message_lines_are_reported_run_by_run"],
    ),
    (
        "a marker naming no file in the zip is not counted",
        "            if not any(form(named) in names "
        "for form, names in zip(NAME_FORMS, carried)):\n                missing += 1",
        "            if False:\n                missing += 1",
        ["test_a_marker_naming_no_file_is_counted"],
    ),
    (
        "lines before the first message are dropped without a count",
        "        if line.strip():\n            count += 1",
        "        if False:\n            count += 1",
        ["test_lines_before_the_first_message_are_counted"],
    ),
    (
        "the tally line claims everything is placed whatever it found",
        '    parts = ["%d %s" % (tally[key], label) for key, label in TALLY_LABELS if tally.get(key)]',
        "    parts = []",
        [
            "test_a_marker_naming_no_file_is_counted",
            "test_two_members_sharing_a_basename_are_both_extracted",
        ],
    ),
    (
        "the fold splices its section onto the old text instead of re-rendering",
        '    with open(digest_path, "w", encoding="utf-8") as handle:\n'
        "        handle.write(render_digest(context))\n"
        '    with open(context_path, "w", encoding="utf-8") as handle:',
        '    with open(digest_path, encoding="utf-8") as old_handle:\n'
        "        head = old_handle.read().partition(TRANSCRIPT_HEADING)[0]\n"
        '    with open(digest_path, "w", encoding="utf-8") as handle:\n'
        '        handle.write(head + TRANSCRIPT_HEADING + "\\n\\n"\n'
        '                     + "\\n".join(sorted(transcripts)))\n'
        '    with open(context_path, "w", encoding="utf-8") as handle:',
        ["test_the_fold_re_renders_the_whole_digest"],
    ),
    (
        "a decomposed filename is a different string, so the file belongs to no message",
        '    return unicodedata.normalize(\n        "NFC", os.path.basename(name).translate(INVISIBLE).strip()\n    )',
        "    return os.path.basename(name).translate(INVISIBLE).strip()",
        ["test_a_decomposed_accent_in_the_zip_is_the_same_name_as_a_composed_one"],
    ),
    (
        "a member name stored as UTF-8 without the flag is left as mojibake",
        '        info.filename = info.filename.encode("cp437").decode("utf-8")',
        "        pass",
        ["test_a_name_stored_as_utf8_without_the_flag_is_repaired"],
    ),
    (
        "the repair ignores the flag and re-encodes a name that was already UTF-8",
        "    if info.flag_bits & 0x800:\n        return info",
        "    if False:\n        return info",
        ["test_a_name_the_zip_declared_utf8_is_left_alone"],
    ),
    (
        "a header shape the parser misses is absorbed into the message above, silently",
        "        if DATE_START_RE.match(clean):\n            count += 1",
        "        if False:\n            count += 1",
        ["test_a_header_shape_the_parser_misses_is_counted"],
    ),
    (
        "every line that opens no message counts as a missed header, drowning the tally",
        r'DATE_START_RE = re.compile(r"^\[?[ ]*\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b")',
        r'DATE_START_RE = re.compile(r"")',
        ["test_a_continuation_line_is_not_counted_as_a_missed_header"],
    ),
    (
        "an entry the zip carries twice replaces its twin without a word",
        "            if info.filename in seen:\n                duplicates += 1",
        "            if False:\n                duplicates += 1",
        ["test_an_entry_the_zip_carries_twice_is_counted"],
    ),
    (
        "the table names the announced file, not the one the collision wrote to disk",
        '''            shown = ("`%s` — saved as `%s`" % (announced, on_disk)
                     if on_disk and on_disk != announced else "`%s`" % announced)''',
        '            shown = "`%s`" % announced',
        ["test_the_digest_names_the_file_the_reader_will_open"],
    ),
    (
        "a run that extracted nothing still says where it extracted to",
        '        if context.get("extracted", True):\n            reasons',
        '        if True:\n            reasons',
        ["test_no_extract_neither_claims_an_extraction_nor_points_at_one"],
    ),
    (
        "a digest that extracted nothing still hands a transcriber the empty directory",
        '        if not context.get("extracted", True):',
        "        if False:",
        ["test_no_extract_neither_claims_an_extraction_nor_points_at_one"],
    ),
    (
        "the legend for `saved as` prints over a delta where nothing collided",
        "            if renamed:",
        "            if True:",
        ["test_a_name_that_did_not_collide_is_not_dressed_up"],
    ),
    (
        "context.json is read whatever version wrote it, so a missing key raises KeyError",
        '    if context.get("schema") != CONTEXT_SCHEMA:',
        "    if False:",
        ["test_a_context_from_another_version_is_refused_by_name"],
    ),
]


def suite_test_ids():
    """method name -> full unittest id. Derived, never hand-kept: a list beside a
    completeness check is the next defect."""
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
    with open(SOURCE, encoding="utf-8") as fh:
        original = fh.read()

    ids = suite_test_ids()
    available = set(ids)
    named = set()
    problems = []

    ok, output = run_tests(sorted(available), ids)
    if not ok:
        print("the suite is not green before mutating; fix that first\n%s" % output)
        return 1

    backup = tempfile.mkstemp(prefix="wa-export-backup-")[1]
    shutil.copy(SOURCE, backup)
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

            with open(SOURCE, "w", encoding="utf-8") as fh:
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
        shutil.copy(backup, SOURCE)
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
    return 1 if problems or unproved else 0


if __name__ == "__main__":
    sys.exit(main())
