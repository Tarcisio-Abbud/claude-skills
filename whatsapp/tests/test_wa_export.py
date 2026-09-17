#!/usr/bin/env python3
"""Regression suite for `wa_export.py` (../bin/wa_export.py).

Run: python3 -m unittest discover -s whatsapp/tests   (stdlib only, no deps)

Every test here is proved by MUTATION: the defect is put back in the source and the test
must fail. `mutations_wa_export.py` in this directory replays each one mechanically.

The fixtures are synthetic exports built in a tempdir — this repo is PUBLIC, and the real
exports this script was measured against are private conversations. Where a test guards a
behaviour that a real export taught, the test says so in one line rather than shipping the
export.
"""

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(HERE, os.pardir, "bin", "wa_export.py"))


def load_module():
    loader = importlib.machinery.SourceFileLoader("wa_export", SCRIPT)
    spec = importlib.util.spec_from_loader("wa_export", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


wa = load_module()


def make_export(path, chat_name, lines, attachments=()):
    """Write a WhatsApp-shaped .zip: one chat transcript plus its media files."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(chat_name, "\n".join(lines) + "\n")
        for name, payload in attachments:
            archive.writestr(name, payload)
    return path


def run(*args):
    """Drive the real script as a subprocess, the way a session does."""
    return subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True,
        text=True,
    )


BASE = [
    "01/08/2026 09:00 - Ana: bom dia",
    "01/08/2026 09:01 - Bruno: bom dia, Ana",
    "02/08/2026 14:30 - Ana: ‎segue-anexo.pdf (arquivo anexado)",
    "segue-anexo.pdf",
    "02/08/2026 14:31 - Ana: esse e o contrato",
]

TAIL = [
    "10/08/2026 08:00 - Bruno: recebi, obrigado",
    "10/08/2026 08:05 - Ana: ‎nota-nova.pdf (arquivo anexado)",
    "nota-nova.pdf",
]

CHAT = "Conversa do WhatsApp com Ana.txt"


class Fixture(unittest.TestCase):
    """A tempdir holding an old and a new export of one synthetic conversation."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="wa-test-")
        self.addCleanup(self._clean)

    def _clean(self):
        import shutil

        shutil.rmtree(self.dir, ignore_errors=True)

    def path(self, name):
        return os.path.join(self.dir, name)

    def pair(self, old_lines=None, new_lines=None, old_files=(), new_files=(), chat=CHAT):
        old = make_export(self.path("2026-08-01-export.zip"), chat,
                          BASE if old_lines is None else old_lines,
                          old_files or [("segue-anexo.pdf", b"old-contract")])
        new = make_export(self.path("2026-08-10-export.zip"), chat,
                          (BASE + TAIL) if new_lines is None else new_lines,
                          new_files or [("segue-anexo.pdf", b"old-contract"),
                                        ("nota-nova.pdf", b"new-invoice")])
        return old, new

    def diff_json(self, new, *extra):
        result = run("diff", new, "--no-extract", "--json",
                     "--out", self.path("out"), *extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def digest(self, out=None):
        with open(os.path.join(out or self.path("out"), "delta.md"), encoding="utf-8") as f:
            return f.read()


class DeltaTest(Fixture):
    def test_only_the_new_messages_come_back(self):
        _old, new = self.pair()
        payload = self.diff_json(new)
        bodies = [m["body"] for m in payload["messages"]]
        self.assertEqual(bodies, ["recebi, obrigado", "nota-nova.pdf (arquivo anexado)\nnota-nova.pdf"])

    def test_the_new_messages_carry_their_line_numbers(self):
        _old, new = self.pair()
        payload = self.diff_json(new)
        self.assertEqual([m["line"] for m in payload["messages"]], [6, 7])

    def test_a_minute_that_moved_is_not_a_change(self):
        """Measured on two real exports eleven days apart: an untouched message moved from
        16:04 to 16:05. A key carrying the clock reports it as changed, and the reader is
        sent back to a message from two weeks ago for nothing."""
        jittered = list(BASE)
        jittered[1] = "01/08/2026 09:02 - Bruno: bom dia, Ana"
        _old, new = self.pair(new_lines=jittered + TAIL)
        payload = self.diff_json(new)
        self.assertEqual(payload["anomalies"], {"changed": [], "removed": []})
        self.assertEqual(len(payload["messages"]), 2)

    def test_a_multiline_message_stays_whole(self):
        long_message = BASE + [
            "09/08/2026 11:00 - Ana: pagamento stand",
            "R$ 2.500,00",
            "venc 15/08",
        ]
        _old, new = self.pair(new_lines=long_message)
        payload = self.diff_json(new)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["body"],
                         "pagamento stand\nR$ 2.500,00\nvenc 15/08")

    def test_a_colon_in_the_body_does_not_become_the_sender(self):
        lines = BASE + ["09/08/2026 11:00 - Ana: Pagamento: R$ 2.500"]
        _old, new = self.pair(new_lines=lines)
        payload = self.diff_json(new)
        self.assertEqual(payload["messages"][0]["sender"], "Ana")
        self.assertEqual(payload["messages"][0]["body"], "Pagamento: R$ 2.500")

    def test_nothing_new_is_reported_as_nothing(self):
        _old, new = self.pair(new_lines=BASE, new_files=[("segue-anexo.pdf", b"old-contract")])
        payload = self.diff_json(new)
        self.assertEqual(payload["messages"], [])
        self.assertIn("nothing", self.digest())

    def test_a_message_that_vanished_is_an_anomaly(self):
        """An export only grows. A message missing from the new one means the pair is
        wrong, and swallowing it would let a bad pair read as a clean delta."""
        shorter = BASE[:-1] + TAIL
        _old, new = self.pair(new_lines=shorter)
        payload = self.diff_json(new)
        self.assertTrue(payload["anomalies"]["removed"])
        self.assertIn("Anomalies", self.digest())

    def test_the_ios_bracket_format_parses(self):
        ios = [
            "[01/08/2026, 09:00:11] Ana: bom dia",
            "[01/08/2026, 09:01:02] Bruno: bom dia, Ana",
        ]
        old = make_export(self.path("a.zip"), "_chat.txt", ios, [])
        new = make_export(self.path("b.zip"), "_chat.txt",
                          ios + ["[10/08/2026, 08:00:00] Bruno: recebi"], [])
        result = run("diff", new, "--previous", old, "--no-extract", "--json",
                     "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([m["body"] for m in payload["messages"]], ["recebi"])


class AttachmentTest(Fixture):
    def test_only_the_new_files_come_back(self):
        _old, new = self.pair()
        payload = self.diff_json(new)
        self.assertEqual(payload["attachments"], ["nota-nova.pdf"])

    def test_the_chat_transcript_is_not_an_attachment(self):
        """It sits in both exports and its bytes always move, so counting it lands it
        under the heading for a file whose content changed — the one heading that says
        an earlier reading is unproven."""
        _old, new = self.pair()
        payload = self.diff_json(new)
        self.assertNotIn(CHAT, payload["attachments"])
        self.assertNotIn(CHAT, payload["modified"])

    def test_a_file_whose_bytes_moved_is_reported_apart(self):
        _old, new = self.pair(
            new_files=[("segue-anexo.pdf", b"REPLACED"), ("nota-nova.pdf", b"new-invoice")]
        )
        payload = self.diff_json(new)
        self.assertEqual(payload["modified"], ["segue-anexo.pdf"])
        self.assertIn("CONTENT changed", self.digest())

    def test_the_dedup_suffix_does_not_hand_the_file_to_the_older_message(self):
        """Measured: WhatsApp stores a second `boleto (1).pdf` as `boleto (1)-1.pdf` and names
        the SUFFIXED file in the new message. Folding the suffix away before trying the
        exact name credited the later file to the earlier message that sent its namesake."""
        lines = BASE + [
            "05/08/2026 10:00 - Ana: ‎boleto (1).pdf (arquivo anexado)",
            "boleto (1).pdf",
            "09/08/2026 10:00 - Ana: ‎boleto (1)-1.pdf (arquivo anexado)",
            "boleto (1).pdf",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("segue-anexo.pdf", b"old"),
                           ("boleto (1).pdf", b"first"),
                           ("boleto (1)-1.pdf", b"second")])
        self.diff_json(new, "--previous", old)
        rows = [l for l in self.digest().splitlines()
                if l.startswith("| `boleto (1)-1.pdf`")]
        self.assertEqual(len(rows), 1, "the attachment table has no row for the file")
        self.assertIn("09/08/2026", rows[0])

    def test_the_attachments_are_extracted_beside_the_digest(self):
        _old, new = self.pair()
        result = run("diff", new, "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        extracted = os.path.join(self.path("out"), "attachments", "nota-nova.pdf")
        self.assertTrue(os.path.exists(extracted))
        with open(extracted, "rb") as handle:
            self.assertEqual(handle.read(), b"new-invoice")
        self.assertFalse(
            os.path.exists(os.path.join(self.path("out"), "attachments", "segue-anexo.pdf"))
        )


class AudioTest(Fixture):
    def audio_pair(self):
        lines = BASE + [
            "10/08/2026 08:00 - Ana: ‎PTT-20260810-WA0001.opus (arquivo anexado)",
            "PTT-20260810-WA0001.opus",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("segue-anexo.pdf", b"old"),
                           ("PTT-20260810-WA0001.opus", b"audio-bytes")])
        return old, new

    def test_a_new_voice_note_is_named_as_pending(self):
        _old, new = self.audio_pair()
        payload = self.diff_json(new)
        self.assertEqual(payload["audio"], ["PTT-20260810-WA0001.opus"])
        self.assertIn("incomplete until", self.digest())

    def test_the_transcription_command_is_ready_to_paste(self):
        _old, new = self.audio_pair()
        self.diff_json(new)
        self.assertIn("transcripts", self.digest())
        self.assertIn("asr:transcribe-audio", self.digest())

    def test_transcripts_fold_into_the_digest_with_who_and_when(self):
        _old, new = self.audio_pair()
        out = self.path("out")
        result = run("diff", new, "--out", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        transcript = os.path.join(out, "attachments", "transcript.jsonl")
        with open(transcript, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "file": os.path.join(out, "attachments", "PTT-20260810-WA0001.opus"),
                "dur": 12.0,
                "text": "o pagamento e do fornecedor novo",
            }) + "\n")
        folded = run("transcripts", out)
        self.assertEqual(folded.returncode, 0, folded.stderr)
        digest = self.digest(out)
        self.assertIn("o pagamento e do fornecedor novo", digest)
        self.assertIn("Ana", digest.split("## New voice notes")[1])
        self.assertIn("10/08/2026 08:00", digest.split("## New voice notes")[1])

    def test_transcripts_refuses_when_nothing_was_transcribed(self):
        _old, new = self.audio_pair()
        out = self.path("out")
        run("diff", new, "--out", out)
        result = run("transcripts", out)
        self.assertEqual(result.returncode, 2)
        self.assertIn("transcript.jsonl", result.stderr)


class PreviousExportTest(Fixture):
    def test_the_previous_export_is_found_beside_the_new_one(self):
        _old, new = self.pair()
        payload = self.diff_json(new)
        self.assertTrue(payload["previous"].endswith("2026-08-01-export.zip"))

    def test_a_longer_neighbour_is_not_a_predecessor(self):
        """A WhatsApp export only grows, so a neighbour with MORE messages is a LATER
        export. Diffing against it reports the conversation running backwards."""
        self.pair()
        make_export(self.path("2026-08-20-export.zip"), CHAT,
                    BASE + TAIL + ["20/08/2026 09:00 - Ana: depois"], [])
        payload = self.diff_json(self.path("2026-08-10-export.zip"))
        self.assertTrue(payload["previous"].endswith("2026-08-01-export.zip"))

    def test_another_conversation_is_not_a_predecessor(self):
        self.pair()
        make_export(self.path("2026-08-05-outra.zip"),
                    "Conversa do WhatsApp com Carla.txt", BASE, [])
        payload = self.diff_json(self.path("2026-08-10-export.zip"))
        self.assertTrue(payload["previous"].endswith("2026-08-01-export.zip"))

    def test_no_predecessor_is_refused_rather_than_guessed(self):
        new = make_export(self.path("solo.zip"), CHAT, BASE, [])
        result = run("diff", new, "--no-extract", "--out", self.path("out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--previous", result.stderr)

    def test_an_unrelated_pair_is_refused(self):
        old = make_export(self.path("a.zip"), CHAT,
                          ["01/01/2026 09:00 - Ana: %d" % n for n in range(40)], [])
        new = make_export(self.path("b.zip"), CHAT,
                          ["01/02/2026 09:00 - Bruno: %d" % n for n in range(40)], [])
        result = run("diff", new, "--previous", old, "--no-extract", "--out", self.path("out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("same conversation", result.stderr)

    def test_force_diffs_an_unrelated_pair_anyway(self):
        old = make_export(self.path("a.zip"), CHAT,
                          ["01/01/2026 09:00 - Ana: %d" % n for n in range(40)], [])
        new = make_export(self.path("b.zip"), CHAT,
                          ["01/02/2026 09:00 - Bruno: %d" % n for n in range(40)], [])
        result = run("diff", new, "--previous", old, "--no-extract", "--force",
                     "--json", "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["messages"]), 40)


class UnitTest(unittest.TestCase):
    """The pieces the CLI is built from, exercised directly."""

    def test_a_short_year_is_the_same_day_as_a_long_one(self):
        self.assertEqual(wa.normalize_date("3/6/26"), wa.normalize_date("03/06/2026"))

    def test_the_title_survives_the_locale_of_the_chat_file(self):
        for member in ("Conversa do WhatsApp com Ana.txt", "WhatsApp Chat with Ana.txt",
                       "Chat de WhatsApp con Ana.txt"):
            self.assertEqual(wa.conversation_title(member, "/tmp/x.zip"), "Ana")

    def test_an_unnamed_chat_file_falls_back_to_the_zip_name(self):
        self.assertEqual(wa.conversation_title("_chat.txt", "/tmp/2026-Ana.zip"), "2026-Ana")

    def test_an_invisible_mark_does_not_split_a_message(self):
        messages = wa.parse_messages("01/08/2026 09:00 - Ana: ‎ok\n")
        self.assertEqual(messages[0].body, "ok")


if __name__ == "__main__":
    unittest.main()
