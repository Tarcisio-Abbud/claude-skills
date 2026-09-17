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
        "    exact = plain_name(info.filename)\n"
        "    for message in messages:\n"
        "        for named in message.attachments:\n"
        "            if plain_name(named) == exact:\n"
        "                return message\n",
        "",
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
        "            base = os.path.basename(info.filename)",
        "        for info in archive.infolist():\n"
        "            base = os.path.basename(info.filename)",
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
        '    """Same two passes as `owning_message`, over the records `diff` wrote."""',
        '    """Same two passes as `owning_message`, over the records `diff` wrote."""\n'
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
        '    if old_zip is None:\n        fail("no earlier export of this conversation in %s — pass --previous."',
        '    if False:\n        fail("no earlier export of this conversation in %s — pass --previous."',
        ["test_no_predecessor_is_refused_rather_than_guessed"],
    ),
    (
        "two unrelated exports are diffed rather than refused",
        "    if delta.overlap < args.min_overlap and not args.force:",
        "    if False:",
        ["test_an_unrelated_pair_is_refused"],
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
        "            if plain_name(named) not in exact and "
        "normalize_attachment(named) not in folded:\n                missing += 1",
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
