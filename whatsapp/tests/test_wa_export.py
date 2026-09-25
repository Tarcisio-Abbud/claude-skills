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


def pdf_with_text():
    """A PDF whose page resources name a font: it has a text layer, raw in the bytes."""
    return (b"%PDF-1.4\n1 0 obj\n<< /Type /Page /Resources << /Font << /F1 2 0 R >> >> >>\n"
            b"endobj\n2 0 obj\n<< /Type /Font /BaseFont /Helvetica >>\nendobj\n"
            b"trailer\n<< /Root 1 0 R >>\n%%EOF\n")


def pdf_scanned():
    """A photograph of a document: an image XObject and no font anywhere."""
    return (b"%PDF-1.4\n1 0 obj\n<< /Type /Page /Resources << /XObject << /Im0 2 0 R >> >> "
            b">>\nendobj\n2 0 obj\n<< /Subtype /Image /Filter /DCTDecode /Width 1200 >>\n"
            b"stream\n\xff\xd8\xff\xe0 scan bytes\nendstream\nendobj\n"
            b"trailer\n<< /Root 1 0 R >>\n%%EOF\n")


def pdf_encrypted():
    return (b"%PDF-1.6\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"trailer\n<< /Encrypt 9 0 R /Root 1 0 R >>\n%%EOF\n")


def pdf_objstm():
    """A PDF written since 1.5: the font lives inside a Flate object stream, not in the
    raw bytes. Every modern generator produces this, so a raw search alone calls an
    ordinary document a scan."""
    import zlib

    inner = zlib.compress(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    return (b"%PDF-1.5\n1 0 obj\n<< /Type /ObjStm /Filter /FlateDecode >>\nstream\n"
            + inner + b"\nendstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n")


def xlsx_bytes():
    """A real ZIP container holding the member that makes it a workbook."""
    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as inner:
        inner.writestr("[Content_Types].xml", "<Types/>")
        inner.writestr("xl/workbook.xml", "<workbook/>")
    return buf.getvalue()


JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 40


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
        self.assertEqual(payload["anomalies"], {"changed": [], "removed": [], "dropped": []})
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

    def test_an_attachment_the_previous_export_had_is_an_anomaly(self):
        """An export only grows. A file that was there and is not says the pair is wrong or
        the media was deleted on the phone; either way whatever was concluded from that
        file is now unbacked, and silence is the one answer that hides it."""
        old_lines = BASE + ["03/08/2026 10:00 - Ana: \u200esumido.pdf (arquivo anexado)"]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, old_lines,
                          [("segue-anexo.pdf", b"old"), ("sumido.pdf", b"gone")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, old_lines + TAIL,
                          [("segue-anexo.pdf", b"old"), ("nota-nova.pdf", b"new-invoice")])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual(payload["anomalies"]["dropped"], ["sumido.pdf"])
        digest = self.digest()
        self.assertIn("## Anomalies", digest)
        self.assertIn("**Attachment gone**: `sumido.pdf`", digest)

    def test_a_decomposed_accent_in_the_zip_is_the_same_name_as_a_composed_one(self):
        """Measured on a real export: iOS stores the zip entry DECOMPOSED (`C` + a combining
        cedilla) and the chat text spells the name composed. One attachment of 151 carried
        an accent, and it was the one that belonged to no message — the file was there, the
        message was there, and nothing connected them."""
        import unicodedata

        composed = "NOTA ALTERAÇÃO.pdf"
        decomposed = unicodedata.normalize("NFD", composed)
        self.assertNotEqual(composed, decomposed)
        lines = BASE + ["10/08/2026 08:00 - Ana: \u200e%s (arquivo anexado)" % composed]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("segue-anexo.pdf", b"old"), (decomposed, b"nota")])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual(payload["tally"]["markers_without_file"], 0)
        self.assertEqual(payload["tally"]["files_without_message"], 0)
        rows = [l for l in self.digest().splitlines() if l.startswith("| `")]
        self.assertEqual(len(rows), 1)
        self.assertIn("Ana", rows[0])

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


class CollisionNameTest(Fixture):
    """Two zip members flattening onto one basename, seen from the digest.

    `extract` already writes the second one as `x~2.pdf` and counts the collision. The
    reader opens what the TABLE names, so a table naming both rows `x.pdf` hands them a
    file whose content belongs to the other message — the harm the collision count exists
    to prevent, one step further down.
    """

    def collided_pair(self):
        lines = BASE + [
            "10/08/2026 08:05 - Ana: \u200edocumento.pdf (arquivo anexado)",
            "documento.pdf",
            "10/08/2026 08:06 - Bruno: \u200edocumento.pdf (arquivo anexado)",
            "documento.pdf",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("segue-anexo.pdf", b"old"),
                           ("media/documento.pdf", b"da-ana"),
                           ("docs/documento.pdf", b"do-bruno")])
        return old, new

    def test_the_digest_names_the_file_the_reader_will_open(self):
        _old, new = self.collided_pair()
        out = self.path("out")
        result = run("diff", new, "--out", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        digest = self.digest(out)
        self.assertIn("saved as `documento~2.pdf`", digest)
        attachments = os.path.join(out, "attachments")
        self.assertTrue(os.path.exists(os.path.join(attachments, "documento.pdf")))
        self.assertTrue(os.path.exists(os.path.join(attachments, "documento~2.pdf")))

    def test_a_name_that_did_not_collide_is_not_dressed_up(self):
        _old, new = self.pair()
        out = self.path("out")
        result = run("diff", new, "--out", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("saved as", self.digest(out))


class ContextSchemaTest(Fixture):
    """`context.json` is a contract between two runs of this script.

    Without a version on it, a directory written by an older version fails deep inside the
    renderer with a KeyError, instead of the re-diff message the code already writes for a
    delta directory it cannot read.
    """

    def test_a_context_from_another_version_is_refused_by_name(self):
        _old, new = self.audio_pair_for_schema()
        out = self.path("out")
        self.assertEqual(run("diff", new, "--out", out).returncode, 0)
        context_path = os.path.join(out, "context.json")
        with open(context_path, encoding="utf-8") as handle:
            context = json.load(handle)
        del context["line_runs"]
        context["schema"] = 99
        with open(context_path, "w", encoding="utf-8") as handle:
            json.dump(context, handle)
        with open(os.path.join(out, "attachments", "transcript.jsonl"), "w",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({"file": "PTT-20260810-WA0001.opus",
                                     "text": "oi"}) + "\n")
        folded = run("transcripts", out)
        self.assertEqual(folded.returncode, 2, folded.stdout)
        self.assertIn("another version", folded.stderr)
        self.assertIn("re-run `diff`", folded.stderr)

    def audio_pair_for_schema(self):
        return AudioTest.audio_pair(self)


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
        out = self.path("out")
        result = run("diff", new, "--out", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        digest = self.digest(out)
        self.assertIn("transcripts", digest)
        self.assertIn("asr:transcribe-audio", digest)

    def test_no_extract_neither_claims_an_extraction_nor_points_at_one(self):
        """`--no-extract` writes no attachments/ — the digest must not say it did.

        The digest is what the reader acts on: a line naming a directory that was never
        written sends them to transcribe an empty path, and the `Unaccounted` line below
        it is read as trustworthy because the lines above it are.
        """
        _old, new = self.audio_pair()
        self.diff_json(new)
        digest = self.digest()
        self.assertNotIn("Extracted into", digest)
        self.assertIn("Not extracted", digest)
        self.assertNotIn("asr:transcribe-audio", digest)
        self.assertFalse(os.path.isdir(os.path.join(self.path("out"), "attachments")))

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

    def test_the_fold_re_renders_the_whole_digest(self):
        """The fold used to splice its section onto the text below it, so everything after
        the heading was whatever the previous run wrote. Re-rendering from the recorded
        data is what keeps one piece of code writing this file: a voice note still without
        a transcript is named, which a splice of the transcribed ones cannot do."""
        lines = BASE + [
            "10/08/2026 08:00 - Ana: \u200ePTT-20260810-WA0001.opus (arquivo anexado)",
            "PTT-20260810-WA0001.opus",
            "10/08/2026 08:30 - Bruno: \u200ePTT-20260810-WA0002.opus (arquivo anexado)",
            "PTT-20260810-WA0002.opus",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE, [])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("PTT-20260810-WA0001.opus", b"a"),
                           ("PTT-20260810-WA0002.opus", b"b")])
        out = self.path("out")
        self.assertEqual(run("diff", new, "--previous", old, "--out", out).returncode, 0)
        with open(os.path.join(out, "attachments", "transcript.jsonl"), "w",
                  encoding="utf-8") as handle:
            handle.write(json.dumps({"file": "PTT-20260810-WA0001.opus",
                                     "text": "so o primeiro"}) + "\n")
        folded = run("transcripts", out)
        self.assertEqual(folded.returncode, 0, folded.stderr)
        digest = self.digest(out)
        self.assertIn("so o primeiro", digest)
        self.assertIn("**Still pending:** `PTT-20260810-WA0002.opus`", digest)
        self.assertIn("PTT-20260810-WA0002.opus", folded.stdout)
        # the rest of the document is still there, re-rendered rather than inherited
        self.assertIn("## New attachments", digest)
        self.assertIn("**Unaccounted:**", digest)

    def test_transcripts_refuses_when_nothing_was_transcribed(self):
        _old, new = self.audio_pair()
        out = self.path("out")
        run("diff", new, "--out", out)
        result = run("transcripts", out)
        self.assertEqual(result.returncode, 2)
        self.assertIn("transcript.jsonl", result.stderr)


class MarkerTest(Fixture):
    """The second attachment marker shape, and the `.txt` that is not the chat."""

    def test_the_ios_attachment_marker_is_read(self):
        """Measured on a real export of this population: its 151 attachments are announced
        as `<anexado: NAME>`, and a reader that knows only `NAME (arquivo anexado)`
        attributed NONE of them to a sender or a date — the table came back empty while the
        files were there."""
        lines = BASE + [
            "10/08/2026 08:00 - Ana: \u200e<anexado: 00000042-NOTA.pdf>",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("segue-anexo.pdf", b"old"), ("00000042-NOTA.pdf", b"nota")])
        self.diff_json(new, "--previous", old)
        rows = [l for l in self.digest().splitlines() if l.startswith("| `00000042-NOTA.pdf`")]
        self.assertEqual(len(rows), 1)
        self.assertIn("Ana", rows[0])
        self.assertIn("10/08/2026", rows[0])

    def test_a_txt_attachment_does_not_become_the_chat(self):
        """The largest `.txt` is the conversation until somebody sends a bank return file.
        Then it wins on size, parses to zero messages, and the real transcript is filed as
        an attachment: every line of the delta is wrong and nothing says so."""
        bulky = ("0" * 200 + "\n") * 50
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, BASE + TAIL,
                          [("segue-anexo.pdf", b"old"), ("nota-nova.pdf", b"new-invoice"),
                           ("RETORNO-BANCO.txt", bulky.encode())])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual([m["body"] for m in payload["messages"]][0], "recebi, obrigado")
        self.assertIn("RETORNO-BANCO.txt", payload["attachments"])

    def test_an_export_with_no_messages_at_all_is_refused(self):
        """Nothing to diff and nothing to align: an empty parse means the file picked is
        not a transcript, and every line of it would count as unaccounted."""
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE, [])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT,
                          ["not a transcript at all", "second line"], [])
        result = run("diff", new, "--previous", old, "--no-extract", "--out", self.path("out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("NO messages", result.stderr)


class TallyTest(Fixture):
    """What the run could not place is counted, not passed over."""

    def test_the_tally_is_clean_when_everything_is_placed(self):
        _old, new = self.pair()
        self.diff_json(new)
        self.assertIn("**Unaccounted:** nothing", self.digest())

    def test_a_marker_naming_no_file_is_counted(self):
        """The message says a PDF was attached and the zip does not carry it. Without the
        tally the digest reports the messages it understood and says nothing about the
        document the reader is waiting for."""
        lines = BASE + [
            "10/08/2026 08:00 - Ana: \u200eboleto-ausente.pdf (arquivo anexado)",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"old")])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("segue-anexo.pdf", b"old")])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual(payload["tally"]["markers_without_file"], 1)
        self.assertIn("1 attachment markers naming no file", self.digest())

    def test_an_entry_the_zip_carries_twice_is_counted(self):
        """The attachment index is keyed by name, so the second entry replaces the first and
        the file leaves the delta without a word — the same silence as every other item on
        this line."""
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE, [])
        path = self.path("2026-08-10-export.zip")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(CHAT, "\n".join(BASE + TAIL) + "\n")
            archive.writestr("segue-anexo.pdf", b"first")
            archive.writestr("segue-anexo.pdf", b"second")
            archive.writestr("nota-nova.pdf", b"new-invoice")
        payload = self.diff_json(path, "--previous", old)
        self.assertEqual(payload["tally"]["duplicate_members"], 1)
        self.assertIn("1 entries the zip carries twice", self.digest())

    def test_lines_before_the_first_message_are_counted(self):
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE, [])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT,
                          ["preamble nobody sent", ""] + BASE + TAIL, [])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual(payload["tally"]["orphan_lines"], 1)

    def test_a_header_shape_the_parser_misses_is_counted(self):
        """Measured with a parser probe: the same am/pm clock written with U+00A0 instead of
        U+202F opens no message, and the line is GLUED onto the message above it — changing
        that message's text, and with it its identity across two exports. Counting the shape
        is what makes an unknown header recoverable instead of invisible."""
        strange = "01/09/2026, 9:00\u00a0AM - Ana: mensagem que nao abre"
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE, [])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT,
                          BASE + TAIL + [strange], [])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual(payload["tally"]["unparsed_headers"], 1)
        self.assertIn("1 lines that look like a header", self.digest())

    def test_a_continuation_line_is_not_counted_as_a_missed_header(self):
        """The count has to stay quiet on the ordinary export, or it is noise nobody reads:
        a bare filename under an attachment marker opens no message and is not a header."""
        _old, new = self.pair()
        payload = self.diff_json(new)
        self.assertEqual(payload["tally"]["unparsed_headers"], 0)

    def test_the_new_message_lines_are_reported_run_by_run(self):
        """Two arrivals with untouched text between them are two runs. One spanning range
        covers lines nobody added, and a reader who opens the export at that range reads
        messages already read."""
        old_lines = BASE + ["05/08/2026 12:00 - Bruno: meio"]
        new_lines = (BASE + ["04/08/2026 09:00 - Ana: primeiro novo"]
                     + ["05/08/2026 12:00 - Bruno: meio"]
                     + ["06/08/2026 09:00 - Ana: segundo novo"])
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, old_lines, [])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, new_lines, [])
        self.diff_json(new, "--previous", old)
        header = [l for l in self.digest().splitlines() if l.startswith("- **New:**")][0]
        self.assertIn("lines 6, 8 of", header)


class WritePathTest(Fixture):
    """Where the run puts its files, and what it refuses to put them on top of."""

    def test_a_second_run_will_not_land_on_the_first(self):
        """Same zip re-run into the same directory is the common case, and half-overwriting
        it leaves this run's delta.md beside the previous run's attachments."""
        _old, new = self.pair()
        first = run("diff", new, "--out", self.path("out"))
        self.assertEqual(first.returncode, 0, first.stderr)
        second = run("diff", new, "--out", self.path("out"))
        self.assertEqual(second.returncode, 2)
        self.assertIn("--overwrite", second.stderr)
        third = run("diff", new, "--out", self.path("out"), "--overwrite")
        self.assertEqual(third.returncode, 0, third.stderr)

    def test_an_overwriting_run_clears_the_old_attachments(self):
        _old, new = self.pair()
        run("diff", new, "--out", self.path("out"))
        stale = os.path.join(self.path("out"), "attachments", "de-outra-corrida.pdf")
        with open(stale, "wb") as handle:
            handle.write(b"left over")
        result = run("diff", new, "--out", self.path("out"), "--overwrite")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(os.path.exists(stale))

    def test_two_members_sharing_a_basename_are_both_extracted(self):
        """Extraction flattens the zip, so `media/x.pdf` and `docs/x.pdf` land on one name.
        Writing the second over the first leaves a file whose content belongs to the other
        one, and a reader who opens it concludes from the wrong document."""
        lines = BASE + [
            "10/08/2026 08:00 - Ana: \u200ex.pdf (arquivo anexado)",
        ]
        old = make_export(self.path("2026-08-01-export.zip"), CHAT, BASE, [])
        new = make_export(self.path("2026-08-10-export.zip"), CHAT, lines,
                          [("media/x.pdf", b"first-document"),
                           ("docs/x.pdf", b"second-document")])
        result = run("diff", new, "--previous", old, "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        files = sorted(os.listdir(os.path.join(self.path("out"), "attachments")))
        self.assertEqual(files, ["x.pdf", "x~2.pdf"])
        payloads = set()
        for name in files:
            with open(os.path.join(self.path("out"), "attachments", name), "rb") as handle:
                payloads.add(handle.read())
        self.assertEqual(payloads, {b"first-document", b"second-document"})
        self.assertIn("1 names that collided", self.digest())


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

    def test_a_conversation_that_exploded_is_still_the_same_pair(self):
        """Measured on a real pair: 11 old messages, all present in a new export of 30. The
        share of the NEW export that is old was 37% and the run refused a perfectly good
        pair. The invariant an export obeys is append-only, so the question is whether the
        new one CONTAINS the old."""
        old_lines = ["01/08/2026 09:%02d - Ana: linha %d" % (n, n) for n in range(11)]
        new_lines = old_lines + ["02/08/2026 10:%02d - Bruno: nova %d" % (n, n)
                                 for n in range(19)]
        old = make_export(self.path("a.zip"), CHAT, old_lines, [])
        new = make_export(self.path("b.zip"), CHAT, new_lines, [])
        payload = self.diff_json(new, "--previous", old)
        self.assertEqual(len(payload["messages"]), 19)

    def test_an_empty_predecessor_confirms_nothing(self):
        """No message in the old export means nothing vouches for the pair, and a ratio of
        0/0 read as a perfect overlap: the emptiest possible evidence passed the check that
        exists to catch a wrong pair."""
        old = make_export(self.path("a.zip"), CHAT, ["nao e uma transcricao"], [])
        new = make_export(self.path("b.zip"), CHAT, BASE + TAIL, [])
        result = run("diff", new, "--previous", old, "--no-extract", "--out", self.path("out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("same conversation", result.stderr)
        self.assertIn("probably not a transcript", result.stderr)

    def test_force_diffs_an_unrelated_pair_anyway(self):
        old = make_export(self.path("a.zip"), CHAT,
                          ["01/01/2026 09:00 - Ana: %d" % n for n in range(40)], [])
        new = make_export(self.path("b.zip"), CHAT,
                          ["01/02/2026 09:00 - Bruno: %d" % n for n in range(40)], [])
        result = run("diff", new, "--previous", old, "--no-extract", "--force",
                     "--json", "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["messages"]), 40)


class FirstExportTest(Fixture):
    """The conversation nobody has exported before.

    Measured on the first real run of this skill: of nine exports, one had no predecessor at
    all. The run refused it, and the conversation was read the way this script exists to
    avoid — `unzip`, then the whole transcript by eye, with the attachments unattributed.
    """

    def test_a_first_export_is_read_whole_instead_of_refused(self):
        new = make_export(self.path("solo.zip"), CHAT, BASE,
                          [("segue-anexo.pdf", b"contract")])
        result = run("diff", new, "--first", "--no-extract", "--json",
                     "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["messages"]), 4)
        self.assertIsNone(payload["previous"])
        self.assertTrue(payload["first"])
        self.assertEqual(payload["attachments"], ["segue-anexo.pdf"])

    def test_the_refusal_offers_the_flag_that_reads_the_export_whole(self):
        """A refusal that names no way forward is where the manual round started."""
        new = make_export(self.path("solo.zip"), CHAT, BASE, [])
        result = run("diff", new, "--no-extract", "--out", self.path("out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--first", result.stderr)

    def test_a_first_export_does_not_claim_a_previous_one(self):
        """The digest is read by somebody who did not run the command. Reading it as a delta
        when it is the whole history makes every line look like news."""
        new = make_export(self.path("solo.zip"), CHAT, BASE, [])
        result = run("diff", new, "--first", "--out", self.path("out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        digest = self.digest()
        self.assertIn("# The whole conversation — Ana", digest)
        self.assertIn("**Previous export:** none (`--first`)", digest)

    def test_first_and_previous_contradict_each_other(self):
        """Both together ask for two different runs, and picking one silently means the
        reader gets a whole history where they asked for a delta, or the other way round."""
        old, new = self.pair()
        result = run("diff", new, "--previous", old, "--first", "--out", self.path("out"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with", result.stderr)


class RefusedPairTest(Fixture):
    """Why the two exports do not match, in the refusal itself.

    The floor refuses correctly and says nothing about the cause, which leaves the reader
    comparing two zips by eye. Both causes below were met on the first real run, and neither
    is visible from outside the files.
    """

    def refusal(self, old_lines, new_lines, *extra):
        old = make_export(self.path("a.zip"), CHAT, old_lines, [])
        new = make_export(self.path("b.zip"), CHAT, new_lines, [])
        result = run("diff", new, "--previous", old, "--no-extract", "--out", self.path("out"),
                     *extra)
        self.assertEqual(result.returncode, 2, result.stdout)
        return result.stderr

    def test_a_locale_that_spells_dates_differently_is_named(self):
        """Two exports of one conversation saved on phones set to different locales spell
        every date differently, so no message matches and a real pair is refused. `--force`
        does not repair it: the delta would then be the whole history."""
        stderr = self.refusal(
            ["19/08/2026 09:%02d - Ana: mensagem %d" % (n, n) for n in range(20)],
            ["8/19/26 09:%02d - Ana: mensagem %d" % (n, n) for n in range(20)],
        )
        self.assertIn("different DATES", stderr)
        self.assertIn("locales", stderr)

    def test_two_phones_spelling_the_senders_differently_are_named(self):
        """One group exported from two phones: each spells the members from its own contact
        book, so the same message carries a saved name on one side and a number on the
        other. Nothing about the files says so."""
        stderr = self.refusal(
            ["01/08/2026 09:%02d - Ana Silva: mensagem %d" % (n, n) for n in range(20)],
            ["01/08/2026 09:%02d - +55 11 99999-0000: mensagem %d" % (n, n)
             for n in range(20)],
        )
        self.assertIn("different SENDER names", stderr)

    def test_a_pair_with_nothing_in_common_says_exactly_that(self):
        """The third answer is the honest one: no relaxed key finds the old export in the new
        one, so the two are not one conversation and no flag makes them one."""
        stderr = self.refusal(
            ["01/01/2026 09:%02d - Ana: assunto antigo %d" % (n, n) for n in range(20)],
            ["05/05/2026 11:%02d - Carla: outro assunto %d" % (n, n) for n in range(20)],
        )
        self.assertIn("survives in any form", stderr)

    def test_two_phones_differing_in_BOTH_ways_are_not_called_unrelated(self):
        """The case the first real run actually met: one group exported from an Android phone
        and from an iOS one. The dates are spelled differently AND the members are spelled
        differently, so both single-relaxation keys miss and the pair falls to the answer that
        says not its text — about a pair whose text is identical throughout."""
        stderr = self.refusal(
            ["19/08/2026 09:%02d - Ana Silva: mensagem %d" % (n, n) for n in range(20)],
            ["8/19/26 09:%02d - +55 11 99999-0000: mensagem %d" % (n, n) for n in range(20)],
        )
        self.assertIn("same TEXTS", stderr)
        self.assertNotIn("survives in any form", stderr)

    def test_a_real_partial_overlap_is_not_reported_as_nothing_in_common(self):
        """A third of the old export is there VERBATIM and the refusal used to answer that not
        its date, not its sender and not its text survives — contradicting the percentage it
        prints one line above. The share is the evidence; the sentence has to match it."""
        stderr = self.refusal(
            ["01/08/2026 09:%02d - Ana: mensagem %d" % (n, n) for n in range(10)],
            ["01/08/2026 09:%02d - Ana: mensagem %d" % (n, n) for n in range(3)]
            + ["09/08/2026 10:00 - Ana: nova"],
        )
        self.assertNotIn("survives in any form", stderr)
        self.assertIn("IS there, verbatim", stderr)
        self.assertIn("--min-overlap 0.25", stderr)

    def test_a_raised_floor_does_not_invent_a_locale_to_blame(self):
        """`--min-overlap 0.9` refuses a pair spelled identically on both sides. A diagnosis
        measured against a constant instead of against that share names the locale cause —
        and sends the reader off to re-export from one phone, over dates that already match."""
        stderr = self.refusal(
            ["01/08/2026 09:%02d - Ana: mensagem %d" % (n, n) for n in range(10)],
            ["01/08/2026 09:%02d - Ana: mensagem %d" % (n, n) for n in range(8)]
            + ["09/08/2026 10:00 - Ana: nova"],
            "--min-overlap", "0.9",
        )
        self.assertNotIn("different DATES", stderr)
        self.assertNotIn("different SENDER names", stderr)
        self.assertIn("IS there, verbatim", stderr)


class AttachmentProbeTest(Fixture):
    """What the bytes say an attachment is, and what stands between it and its reader.

    Three findings of the first real run live here. An attachment arrived as
    `DOC-20260612-WA0000.` with no extension — one was a PDF and another a workbook, and only
    the bytes said which. A utility bill was password-protected. Two tax forms were scans with
    no text in them at all, which every text tool reports as an empty document rather than as
    a failure.
    """

    def probe(self, announced, files, *extra):
        lines = BASE + ["10/08/2026 08:%02d - Ana: ‎%s (arquivo anexado)" % (i, name)
                        for i, name in enumerate(announced)]
        new = make_export(self.path("export.zip"), CHAT, lines, files)
        out = self.path("out")
        result = run("diff", new, "--first", "--out", out, *extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        return out

    def test_an_attachment_with_no_extension_is_saved_as_what_its_bytes_say(self):
        out = self.probe(["DOC-20260810-WA0000."],
                         [("DOC-20260810-WA0000.", pdf_with_text())])
        self.assertTrue(os.path.exists(
            os.path.join(out, "attachments", "DOC-20260810-WA0000.pdf")))
        digest = self.digest(out)
        self.assertIn("saved as `DOC-20260810-WA0000.pdf`", digest)
        self.assertIn("carries no extension", digest)

    def test_an_extensionless_workbook_is_named_by_looking_inside_the_zip(self):
        """A workbook and a Word document are both ZIP archives, and stopping at `PK` names
        neither. The member list says which one it is."""
        out = self.probe(["DOC-20260810-WA0001."],
                         [("DOC-20260810-WA0001.", xlsx_bytes())])
        self.assertTrue(os.path.exists(
            os.path.join(out, "attachments", "DOC-20260810-WA0001.xlsx")))
        self.assertIn("Excel workbook", self.digest(out))

    def test_a_password_protected_pdf_carries_the_command_that_opens_it(self):
        out = self.probe(["fatura-luz.pdf"], [("fatura-luz.pdf", pdf_encrypted())])
        digest = self.digest(out)
        self.assertIn("password-protected", digest)
        self.assertIn("pdftotext -upw <password>", digest)
        self.assertIn(os.path.join(out, "attachments", "fatura-luz.pdf"), digest)

    def test_a_scanned_pdf_is_flagged_as_needing_rendering(self):
        """A scan returns EMPTY from every text tool instead of failing, so the reader
        concludes the document is blank rather than that it needs a different tool."""
        out = self.probe(["darf.pdf"], [("darf.pdf", pdf_scanned())])
        digest = self.digest(out)
        self.assertIn("no text layer", digest)
        self.assertIn("pdftoppm -r 150 -png", digest)

    def test_a_text_layer_inside_an_object_stream_is_not_a_scan(self):
        """Every PDF written since version 1.5 packs its object dictionaries into compressed
        streams, so the `/Font` that proves a text layer is not in the raw bytes. A raw search
        alone announces the most ordinary modern PDF as a scan."""
        out = self.probe(["extrato.pdf"], [("extrato.pdf", pdf_objstm())])
        self.assertNotIn("no text layer", self.digest(out))

    def test_an_ordinary_attachment_is_not_flagged_at_all(self):
        """The section has to stay quiet on the ordinary export, or it is noise nobody reads
        a third time — including on a name spelled `.jpeg` where the bytes say `.jpg`."""
        out = self.probe(
            ["contrato.pdf", "foto.jpeg", "planilha.xlsx"],
            [("contrato.pdf", pdf_with_text()), ("foto.jpeg", JPEG),
             ("planilha.xlsx", xlsx_bytes())],
        )
        digest = self.digest(out)
        self.assertNotIn("## Attachments that need a step", digest)
        self.assertNotIn("saved as", digest)

    def test_an_extension_the_bytes_contradict_is_named(self):
        """The extension is the sender's word for what the file is. When the bytes disagree,
        the reader opens the wrong tool and reads a failure as a corrupt document."""
        out = self.probe(["comprovante.pdf"], [("comprovante.pdf", JPEG)])
        digest = self.digest(out)
        self.assertIn("is named `.pdf` and its bytes are JPEG image", digest)

    def test_no_command_is_offered_for_a_file_that_was_not_extracted(self):
        """`--no-extract` writes no file, and a command naming a path that does not exist
        fails in a way that reads as the PDF being broken."""
        out = self.probe(["fatura-luz.pdf"], [("fatura-luz.pdf", pdf_encrypted())],
                         "--no-extract")
        digest = self.digest(out)
        self.assertIn("password-protected", digest)
        self.assertNotIn("pdftotext", digest)
        self.assertIn("No command is offered", digest)

    def test_the_legend_says_which_of_the_two_renamings_happened(self):
        """A collision and a repaired extension both put a file on disk under another name,
        and they ask for opposite reactions: one says the announced name is now ambiguous,
        the other says only the spelling changed."""
        out = self.probe(["DOC-20260810-WA0000."],
                         [("DOC-20260810-WA0000.", pdf_with_text())])
        digest = self.digest(out)
        self.assertIn("arrived with no extension", digest)
        self.assertNotIn("collided with another member", digest)


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

    def test_a_name_stored_as_utf8_without_the_flag_is_repaired(self):
        """Measured on a real export: the zip carries UTF-8 filename bytes with bit 11 of
        the flags CLEAR, which tells every reader the name is CP437. `zipfile` obeys, the
        accented attachment arrives as mojibake, no message names it, and the document is
        invisible to the reader who needed it."""
        stored = "NOTA ALTERAÇÃO.pdf".encode("utf-8").decode("cp437")
        info = zipfile.ZipInfo(stored)
        info.flag_bits = 0x8
        wa.fix_member_name(info)
        self.assertEqual(info.filename, "NOTA ALTERAÇÃO.pdf")
        self.assertEqual(wa.plain_name(info.filename), "NOTA ALTERAÇÃO.pdf")

    def test_a_name_the_zip_declared_utf8_is_left_alone(self):
        """The repair reads a flag, not a hunch. The same bytes are a correct name under one
        flag and mojibake under the other, so an entry that DECLARED UTF-8 is taken at its
        word — re-encoding it through CP437 would rewrite a name the zip spelled on purpose."""
        stored = "NOTA ALTERAÇÃO.pdf".encode("utf-8").decode("cp437")
        info = zipfile.ZipInfo(stored)
        info.flag_bits = 0x800
        wa.fix_member_name(info)
        self.assertEqual(info.filename, stored)

    def test_an_invisible_mark_does_not_split_a_message(self):
        messages = wa.parse_messages("01/08/2026 09:00 - Ana: ‎ok\n")
        self.assertEqual(messages[0].body, "ok")


if __name__ == "__main__":
    unittest.main()
