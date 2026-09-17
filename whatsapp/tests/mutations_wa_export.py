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
        "    exact = os.path.basename(info.filename).translate(INVISIBLE).strip()\n"
        "    for message in messages:\n"
        "        for named in message.attachments:\n"
        "            if os.path.basename(named).translate(INVISIBLE).strip() == exact:\n"
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
        "            target = os.path.join(dest, os.path.basename(info.filename))",
        "        for info in archive.infolist():\n"
        "            target = os.path.join(dest, os.path.basename(info.filename))",
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
