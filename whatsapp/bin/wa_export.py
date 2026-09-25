#!/usr/bin/env python3
"""Diff two WhatsApp export .zip files and emit only what is new.

A WhatsApp export is cumulative: every export of a conversation carries the whole history
again. Re-reading one costs the whole conversation to learn the handful of messages that
arrived since the last export. This script hands over the delta — the new messages, the new
attachments extracted into a dated directory, and the ready-to-paste command that folds
the transcripts of the new voice notes back into the digest.

    wa_export.py diff NEW.zip [--previous OLD.zip | --first] [--out DIR]
    wa_export.py transcripts DIR

Stdlib only. Run it with any Python 3.8+; the transcription step is a separate tool.
"""
import argparse
import datetime
import difflib
import io
import json
import os
import re
import shlex
import sys
import unicodedata
import zipfile
import zlib

AUDIO_EXTS = (".opus", ".ogg", ".m4a", ".mp3", ".wav", ".aac", ".flac", ".amr")

# WhatsApp writes U+200E (LEFT-TO-RIGHT MARK) before an attachment marker, and the other
# three directional marks turn up around a name written right-to-left. None is visible and
# each breaks a naive comparison, so they are stripped before anything else reads the text.
# U+202F (NARROW NO-BREAK SPACE) is deliberately NOT here: it separates the clock from an
# am/pm suffix, where it is a space doing a space's job, and the patterns that read a clock
# accept it alongside the ordinary one.
INVISIBLE = dict.fromkeys(map(ord, "‎‏‪‬"), None)

# Two header shapes ship in the wild and a conversation can change shape between exports:
#   28/08/2026 16:04 - Sender: body          (Android, most locales)
#   [28/08/2026, 16:04:07] Sender: body      (iOS, and the English Android export)
HEADER_RE = re.compile(
    r"^\[?"
    r"(?P<date>\d{1,2}[/.]\d{1,2}[/.]\d{2,4})"
    r",?[  ]+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:[  ]?[AaPp]\.?[Mm]\.?)?)"
    r"\]?"
    r"(?:[  ]*[-–][  ]*| )"
    r"(?P<rest>.*)$"
)

# Two marker shapes ship, and one export uses one of them throughout:
#   `<name> (arquivo anexado)`   Android, the word translated per locale
#   `<anexado: <name>>`          iOS and `_chat.txt`, likewise translated
# Both are needed. One real export of this population carries the second shape alone, and
# reading it with the first pattern only attributed NONE of its 151 attachments to a
# sender or a date. The locale word list is open-ended by design: an unknown locale falls
# back to matching the bare filename against the zip, and the Tally counts what that left
# unattributed.
ATTACHED_WORDS = (
    "arquivo anexado|archivo adjunto|file attached|attached|fichier joint|"
    "Datei angeh\u00e4ngt|anexado|adjunto|joint|angeh\u00e4ngt"
)
ATTACHED_RE = re.compile(
    r"(?P<name>\S.*?)[\u0020\u00a0]*\((?:" + ATTACHED_WORDS + r")\)"
    r"|<(?:" + ATTACHED_WORDS + r"):[\u0020\u00a0]*(?P<ios>[^>]+)>",
    re.IGNORECASE,
)

# A chat member name, across the locales seen: `_chat.txt`, `WhatsApp Chat with <title>.txt`,
# `Conversa do WhatsApp com <title>.txt`, `Chat de WhatsApp con <title>.txt`.
TITLE_RE = re.compile(
    r"^(?:WhatsApp Chat with|Conversa do WhatsApp com|Chat de WhatsApp con|"
    r"Discussion WhatsApp avec|WhatsApp Chat mit)[ ]+(?P<title>.+)\.txt$",
    re.IGNORECASE,
)

# `invoice (1).pdf` in the chat text can be `invoice (1)-1.pdf` in the zip: WhatsApp
# de-duplicates a stored file whose name is already taken.
DEDUP_SUFFIX_RE = re.compile(r"-\d+$")


class Message:
    """One message: its header fields, its body, and the exact lines it occupied."""

    __slots__ = ("index", "line", "date", "time", "sender", "body", "raw")

    def __init__(self, index, line, date, time, sender, body, raw):
        self.index = index
        self.line = line
        self.date = date
        self.time = time
        self.sender = sender
        self.body = body
        self.raw = raw

    @property
    def key(self):
        """What decides whether two exports carry the SAME message.

        The clock is deliberately absent. Measured on two exports of one conversation
        eleven days apart: an untouched message moved from 16:04 to 16:05, so a key
        carrying the time reports an eleven-week-old message as changed. Date, sender and
        body are what identify a message; the minute is decoration WhatsApp rounds.
        """
        return (self.date, self.sender, " ".join(self.body.split()))

    @property
    def attachments(self):
        """Filenames this message says it attached, in the order they appear."""
        names = []
        for match in ATTACHED_RE.finditer(self.body):
            name = match.group("name") or match.group("ios")
            if name:
                names.append(name.strip())
        return names

    def as_dict(self):
        return {
            "index": self.index,
            "line": self.line,
            "date": self.date,
            "time": self.time,
            "sender": self.sender,
            "body": self.body,
            "raw": self.raw,
            "attachments": self.attachments,
        }


def parse_messages(text):
    """Split an exported chat into messages, keeping continuation lines with their message.

    A line that does not open with a timestamp belongs to the message above it — that is how
    a multi-line payment request, and the bare filename WhatsApp repeats under an attachment
    marker, stay attached to what they explain.
    """
    messages = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        clean = line.translate(INVISIBLE)
        match = HEADER_RE.match(clean)
        if not match:
            if messages:
                messages[-1].body += "\n" + clean
                messages[-1].raw += "\n" + line
            continue
        rest = match.group("rest")
        sender, body = split_sender(rest)
        messages.append(
            Message(
                index=len(messages) + 1,
                line=lineno,
                date=normalize_date(match.group("date")),
                time=match.group("time").strip(),
                sender=sender,
                body=body,
                raw=line,
            )
        )
    return messages


def split_sender(rest):
    """`Sender: body` → ("Sender", "body"); a system notice → (None, notice).

    The split takes the FIRST `: `, so `Ana: Payment: 2500` keeps the whole `Payment: 2500`
    as the body. A sender never contains a newline, which is what
    keeps a colon further down a multi-line body from being read as one.
    """
    head, sep, tail = rest.partition(": ")
    if not sep or "\n" in head or len(head) > 120:
        return None, rest
    return head.strip(), tail


def normalize_date(raw):
    """`3/6/26` and `03/06/2026` are the same day written twice.

    The day/month ORDER is left exactly as exported: it cannot be recovered from one date,
    and both exports of a conversation come from the same phone, so the two sides agree.
    """
    parts = re.split(r"[/.]", raw)
    if len(parts) != 3:
        return raw
    day, month, year = parts
    if len(year) == 2:
        year = "20" + year
    return "%02d/%02d/%s" % (int(day), int(month), year)


def fix_member_name(info):
    """Repair a member name the zip stored as UTF-8 without saying so, in place.

    A zip entry declares UTF-8 with bit 11 of its flags; with the bit clear the format says
    the name is CP437, and `zipfile` obeys. One real export writes UTF-8 bytes with the bit
    CLEAR, so an accented attachment arrives spelled `ALTERAC\u2560\u00baA...` — a name the
    chat text never uses, so the file belongs to no message and the reader is never told the
    document is there. `orig_filename` keeps the stored spelling, and that is what `open()`
    matches against the local header, so renaming the entry here is safe.
    """
    if info.flag_bits & 0x800:
        return info
    try:
        info.filename = info.filename.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return info


def zip_members(archive):
    """Every entry of an archive, each with its name repaired."""
    return [fix_member_name(info) for info in archive.infolist()]


def chat_rank(info):
    """Sort key deciding which `.txt` of an export is the conversation.

    The NAME decides before the size does. Taking the largest `.txt` is right until the
    conversation carries a `.txt` ATTACHMENT — a bank return file, an exported statement —
    that outweighs the transcript. The attachment then becomes "the chat", parses to zero
    messages, and the real transcript is filed as an attachment: the whole delta is wrong
    and nothing says so.
    """
    base = os.path.basename(info.filename)
    if base.lower() in ("_chat.txt", "chat.txt"):
        named = 0
    elif TITLE_RE.match(base):
        named = 1
    else:
        named = 2
    return (named, info.filename.count("/"), -info.file_size)


def read_chat(zip_path):
    """Return (member name, decoded text) for the conversation inside an export."""
    with zipfile.ZipFile(zip_path) as archive:
        txts = [i for i in zip_members(archive) if i.filename.lower().endswith(".txt")]
        if not txts:
            raise ValueError("%s carries no .txt: not a WhatsApp export" % zip_path)
        chat = min(txts, key=chat_rank)
        raw = archive.read(chat.filename)
    return chat.filename, raw.decode("utf-8", errors="replace").lstrip("﻿")


def conversation_title(member_name, zip_path):
    """The conversation's own name, so two exports of it can be recognised as a pair.

    Derived from the chat member when the locale spells it there. `_chat.txt` spells
    nothing, and then the zip's own stem is the only name on offer.
    """
    base = os.path.basename(member_name)
    match = TITLE_RE.match(base)
    if match:
        return match.group("title").strip()
    if base.lower() not in ("_chat.txt", "chat.txt"):
        return base[:-4].strip()
    return os.path.splitext(os.path.basename(zip_path))[0]


def attachment_index(zip_path):
    """Every member of the export except the chat transcript, keyed by filename."""
    chat_member, _ = read_chat(zip_path)
    index = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in zip_members(archive):
            if info.is_dir() or info.filename == chat_member:
                continue
            index[info.filename] = info
    return index


def plain_name(name):
    """A filename as the comparison sees it: basename, no invisible marks, composed.

    The composition is not cosmetic. An export written on iOS stores its zip entries
    DECOMPOSED (`C` + a combining cedilla) while the chat text spells the same name
    composed (`Ç`). The two are the same name to a reader and different strings to
    `==`, and the file then belongs to no message: measured on a real export, where
    exactly one attachment of 151 carried an accent in its name.
    """
    return unicodedata.normalize(
        "NFC", os.path.basename(name).translate(INVISIBLE).strip()
    )


def normalize_attachment(name):
    """Fold the `-1` WhatsApp appends when two attachments share a name."""
    stem, ext = os.path.splitext(plain_name(name))
    return (DEDUP_SUFFIX_RE.sub("", stem).strip().casefold(), ext.casefold())


class Delta:
    """What the new export carries that the old one did not."""

    def __init__(self, added, changed, removed, matched, total_new, total_old):
        self.added = added          # messages present only in the new export
        self.changed = changed      # (old, new) pairs whose key moved — never expected
        self.removed = removed      # messages the new export dropped — never expected
        self.matched = matched      # messages aligned across the two
        self.total_new = total_new
        self.total_old = total_old

    @property
    def message_anomalies(self):
        """Messages the new export edited or dropped. Attachments gone are counted apart,
        by `diff_attachments`; the digest's `## Anomalies` is the two together."""
        return self.changed or self.removed

    @property
    def overlap(self):
        """Share of the OLD export the new one still carries.

        The invariant a WhatsApp export obeys is append-only: everything the old export
        held is in the new one, plus what arrived since. So the question is whether the
        new export CONTAINS the old, not what fraction of the new is old — a pair eleven
        days apart where the conversation exploded is a perfectly good pair with a low
        share of the new, and measuring it that way refused a real one (11 of 11 old
        messages present, 37% of the new).

        An old export with no messages at all contains nothing to confirm the pair with,
        and returns 0.0 rather than a vacuous 1.0.
        """
        return self.matched / self.total_old if self.total_old else 0.0


def align(old_messages, new_messages):
    """Line up two exports of one conversation and report only what moved.

    `SequenceMatcher` over the message keys, not over raw lines: a WhatsApp export is
    append-only, so everything but a tail of inserts is a signal that something is wrong
    with the pair — and this reports that rather than swallowing it.
    """
    old_keys = [m.key for m in old_messages]
    new_keys = [m.key for m in new_messages]
    added, changed, removed, matched = [], [], [], 0
    matcher = difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            matched += j2 - j1
        elif tag == "insert":
            added.extend(new_messages[j1:j2])
        elif tag == "delete":
            removed.extend(old_messages[i1:i2])
        elif tag == "replace":
            # A replace block is only an EDIT where the two sides are plausibly the same
            # message — same day, same sender. Pairing positionally without that test
            # marries a message the new export dropped to an unrelated one it gained, and
            # then reports both as one edit: two exports of different conversations came
            # back as "40 messages edited, none new".
            for offset in range(max(i2 - i1, j2 - j1)):
                old = old_messages[i1 + offset] if i1 + offset < i2 else None
                new = new_messages[j1 + offset] if j1 + offset < j2 else None
                if old is not None and new is not None and \
                        old.date == new.date and old.sender == new.sender:
                    changed.append((old, new))
                    continue
                if new is not None:
                    added.append(new)
                if old is not None:
                    removed.append(old)
    added.sort(key=lambda m: m.index)
    return Delta(added, changed, removed, matched, len(new_messages), len(old_messages))


# The share of the OLD export a relaxed key has to reach before its story is told as the
# reason. It is a FLOOR under the comparison, never the comparison itself: the key is judged
# against the STRICT share the run already measured, because a relaxed key that finds no more
# than the strict one has explained nothing, and a cause named on that evidence prescribes a
# remedy for a problem that is not there.
DIAGNOSIS_FLOOR = 0.5


def diagnose_pair(old_messages, new_messages, overlap=0.0):
    """Why two exports that should be one conversation share too little.

    The refusal alone sends the reader back to a file manager to compare two zips by eye.
    The causes measured on the first real run are invisible there and obvious here: two
    phones set to different LOCALES spell every date differently, two phones of one group
    spell the SENDERS differently from their own contact books, and two phones of one group
    do BOTH — which is what an Android export and an iOS export of one group actually are.
    None of the three is fixed by `--force`, which is what makes naming the cause worth the
    lines.

    `overlap` is the strict share the refusal prints one line above this sentence, and every
    relaxed key is measured against it. Without that, the two answers below it are both
    false: a pair that really does share a third of the old export is told nothing of it
    survives, and a pair refused by a raised `--min-overlap` is told its dates are spelled
    in two locales when they are identical.
    """
    if not old_messages or not new_messages:
        return ("one of the two exports parses to no message at all, so nothing in it "
                "vouches for the pair — that file is probably not a transcript.")

    def body_of(message):
        return " ".join(message.body.split())

    def share(key_of):
        wanted = {key_of(m) for m in new_messages}
        return sum(1 for m in old_messages if key_of(m) in wanted) / len(old_messages)

    floor = max(DIAGNOSIS_FLOOR, overlap)
    if share(lambda m: (m.sender, body_of(m))) > floor:
        return ("the same messages are there under different DATES — two phones set to "
                "different locales (`8/19/26` against `19/08/2026`). Export both sides from "
                "ONE phone; --force would report the whole history as new.")
    if share(lambda m: (m.date, body_of(m))) > floor:
        return ("the same messages are there under different SENDER names — two exports of "
                "one group taken on two phones, each spelling the members from its own "
                "contact book. Diff two exports taken on the SAME phone.")
    if share(body_of) > floor:
        return ("the same TEXTS are there under different dates AND different sender names — "
                "two phones of one group, one of them on another locale and each spelling "
                "the members from its own contact book. Diff two exports taken on the SAME "
                "phone; --force would report the whole history as new.")
    if overlap > 0:
        return ("%.0f%% of the previous export IS there, verbatim, and no relaxed key finds "
                "more — nothing is spelled differently here, the pair simply falls under the "
                "floor `--min-overlap` sets. Confirm this is the right predecessor, then "
                "lower the floor: --min-overlap %.2f." % (overlap * 100, max(overlap - 0.05, 0.01)))
    return ("no message of the previous export survives in any form — not its date, not its "
            "sender, not its text. Either these are two different conversations, or they are "
            "two members' exports of one group and the histories do not meet.")


def diff_attachments(old_index, new_index):
    """(added, modified, dropped) across the two exports.

    `dropped` is the same kind of fact as a vanished message: an export only grows, so a
    file the old export held and the new one does not means the pair is suspect, or the
    media was deleted on the phone. Either way whatever was concluded from that file is
    now unbacked, and the digest says so under Anomalies.
    """
    added, modified = [], []
    for name, info in new_index.items():
        previous = old_index.get(name)
        if previous is None:
            added.append(info)
        elif previous.CRC != info.CRC or previous.file_size != info.file_size:
            modified.append(info)
    dropped = [info for name, info in old_index.items() if name not in new_index]
    added.sort(key=lambda i: i.filename)
    modified.sort(key=lambda i: i.filename)
    dropped.sort(key=lambda i: i.filename)
    return added, modified, dropped


# The two forms a filename is matched by, in the order they are tried. EXACT name first,
# folded name only as a fallback: the `-1` suffix exists precisely because an earlier
# attachment already took the bare name, so folding it away first hands a September file to
# the August message that sent its namesake — measured, and the reason the passes are two.
# Every site that matches a name reads this list, so the rule cannot drift between the
# attribution and the tally that counts what the attribution missed.
NAME_FORMS = (plain_name, normalize_attachment)


def owner_by_name(name, messages, attachments_of):
    """The message announcing `name`, or None when the chat never names it.

    Each form is tried over EVERY message before the next form is tried at all: a fallback
    match on message 2 must not beat an exact match on message 40.
    """
    for form in NAME_FORMS:
        wanted = form(name)
        for message in messages:
            for named in attachments_of(message):
                if form(named) == wanted:
                    return message
    return None


def owning_message(info, messages):
    """The message that announced this attachment, over the parsed `Message` objects."""
    return owner_by_name(info.filename, messages, lambda message: message.attachments)


def is_audio(name):
    return name.lower().endswith(AUDIO_EXTS)


# --- What an attachment really is, and what stands between it and a reader ----------------
#
# Three of these cost a manual round on the first real run of this skill: an attachment
# arrived as `DOC-20260612-WA0000.` with no extension (one was a PDF, another an xlsx, and
# only the bytes said which), a utility bill was password-protected, and two tax forms were
# scans with no text in them at all. Each is invisible in the digest and obvious the moment
# somebody double-clicks the file — which is the wrong moment, because by then the reader is
# in a file manager rather than in the delta.

# Leading bytes → (extension, what to call it). ZIP is the ambiguous one and is refined by
# looking inside; the rest identify themselves.
MAGIC = (
    (b"%PDF-", ".pdf", "PDF"),
    (b"\x89PNG\r\n\x1a\n", ".png", "PNG image"),
    (b"\xff\xd8\xff", ".jpg", "JPEG image"),
    (b"GIF8", ".gif", "GIF image"),
    (b"OggS", ".ogg", "Ogg audio"),
    (b"ID3", ".mp3", "MP3 audio"),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", ".doc", "old Office document"),
    (b"{\\rtf", ".rtf", "RTF document"),
    (b"PK\x03\x04", ".zip", "ZIP archive"),
)

# What a ZIP container holds, and therefore which Office document it is.
ZIP_MARKERS = (("xl/", ".xlsx", "Excel workbook"),
               ("word/", ".docx", "Word document"),
               ("ppt/", ".pptx", "PowerPoint deck"))

# Extensions that are the same kind of file written two ways. A name inside its own family is
# not a mismatch worth a line: `.jpeg` against `.jpg`, or an `.xlsx` seen as the ZIP it is.
EXT_FAMILIES = (
    frozenset((".jpg", ".jpeg")),
    frozenset((".ogg", ".oga", ".opus")),
    frozenset((".mp4", ".m4a", ".mov", ".3gp")),
    frozenset((".zip", ".xlsx", ".docx", ".pptx", ".odt", ".ods")),
)

# A member larger than this is not read to be probed. Nothing in a WhatsApp export comes
# close; the ceiling is there so a hand-built zip cannot make this script read a gigabyte
# into memory to answer a question about its first eight bytes.
PROBE_LIMIT = 16 * 1024 * 1024


def sniff_bytes(data):
    """(extension, label) the CONTENT says, or (None, None) for bytes this table cannot name.

    The extension a name carries is the sender's word for what the file is, and WhatsApp
    strips it often enough that the word goes missing. The bytes do not go missing.
    """
    for magic, ext, label in MAGIC:
        if not data.startswith(magic):
            continue
        if ext != ".zip":
            return ext, label
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as inner:
                names = inner.namelist()
        except (zipfile.BadZipFile, OSError):
            return ext, label
        for prefix, zip_ext, zip_label in ZIP_MARKERS:
            if any(name.startswith(prefix) for name in names):
                return zip_ext, zip_label
        return ext, label
    if data[4:8] == b"ftyp":
        return ".mp4", "MP4 video"
    return None, None


def same_family(left, right):
    """Whether two extensions name the same kind of file."""
    if left == right:
        return True
    return any(left in family and right in family for family in EXT_FAMILIES)


def inflated_streams(data, budget=4 * 1024 * 1024):
    """Every `stream ... endstream` block of a PDF that zlib can inflate.

    A PDF written since version 1.5 packs its object dictionaries into compressed object
    streams, so the `/Font` that proves a text layer is not in the raw bytes at all. Inflating
    is what keeps a perfectly ordinary modern PDF from being announced as a scan.
    """
    spent = 0
    for match in re.finditer(rb"stream\r?\n", data):
        if spent >= budget:
            return
        end = data.find(b"endstream", match.end())
        if end < 0:
            continue
        try:
            chunk = zlib.decompressobj().decompress(data[match.end():end], budget - spent)
        except zlib.error:
            continue
        if chunk:
            spent += len(chunk)
            yield chunk


def pdf_notes(data):
    """What a reader will hit when opening this PDF, as notes, or [] for an ordinary one.

    Two states are worth a line and the third is worth silence. Password-protected: no reader
    opens it, and the password is usually spelled out in the conversation itself. No text
    layer at all: it is a photograph of a document, and every text tool returns empty rather
    than failing, so the reader concludes the document is blank.
    """
    notes = []
    if b"/Encrypt" in data:
        notes.append({
            "text": "password-protected — no text tool opens it without the password, and "
                    "the conversation is usually where the password is said (a utility bill "
                    "uses the first digits of the account holder's tax id)",
            "command": "pdftotext -upw <password> {path} -",
        })
        # An encrypted PDF's own resources are encrypted too, so the text-layer question
        # below cannot be answered about it: every marker it would read is ciphertext.
        return notes
    if b"/Font" in data or any(b"/Font" in chunk for chunk in inflated_streams(data)):
        return notes
    notes.append({
        "text": "no text layer — it is a scan, and every text tool returns EMPTY rather than "
                "failing, which reads as a blank document. Render it and read the images",
        "command": "pdftoppm -r 150 -png {path} {stem}",
    })
    return notes


def probe_member(archive, info, announced):
    """What this attachment is, and the notes its reader needs. None when nothing to say.

    `announced` is the name the chat gave it, which is what carries (or lacks) an extension.
    """
    if info.file_size > PROBE_LIMIT:
        return None
    try:
        with archive.open(info) as handle:
            data = handle.read(PROBE_LIMIT)
    except (zipfile.BadZipFile, OSError, RuntimeError):
        return None
    kind, label = sniff_bytes(data)
    if kind is None:
        return None
    notes = []
    stem, ext = os.path.splitext(plain_name(announced))
    ext = ext.casefold()
    if ext in ("", "."):
        # Renamed on disk, and the digest says so: a file with no extension opens in nothing,
        # and the reader has no way to guess which of two namesakes is the spreadsheet.
        notes.append({
            "text": "carries no extension — the bytes say %s, and it is saved with `%s` on it"
                    % (label, kind),
            "command": None,
        })
    elif not same_family(ext, kind):
        notes.append({
            "text": "is named `%s` and its bytes are %s — open it as %s, whatever the name says"
                    % (ext, label, label),
            "command": None,
        })
    if kind == ".pdf":
        notes.extend(pdf_notes(data))
    rename = (stem.rstrip(".") or "attachment") + kind if ext in ("", ".") else None
    return {"kind": kind, "label": label, "notes": notes, "rename": rename}


def probe_new_files(zip_path, infos):
    """`{member name: probe}` over the attachments this export adds."""
    probes = {}
    if not infos:
        return probes
    with zipfile.ZipFile(zip_path) as archive:
        for info in infos:
            probe = probe_member(archive, info, info.filename)
            if probe and probe["notes"]:
                probes[info.filename] = probe
    return probes


def find_previous(new_zip, title, new_count, directory=None):
    """The latest earlier export of this conversation sitting beside the new one.

    Chosen by the conversation's own name rather than by the filename's date, because the
    date in a filename is written by whoever saved it and has already been wrong here. An
    export is a predecessor only if it carries no MORE messages than the new one: a
    WhatsApp export only grows, so a longer neighbour is a LATER export, and diffing
    against it would report the conversation running backwards.
    """
    directory = directory or os.path.dirname(os.path.abspath(new_zip))
    new_abs = os.path.abspath(new_zip)
    candidates = []
    for entry in sorted(os.listdir(directory)):
        if not entry.lower().endswith(".zip"):
            continue
        path = os.path.join(directory, entry)
        if os.path.abspath(path) == new_abs:
            continue
        try:
            member, text = read_chat(path)
        except (ValueError, zipfile.BadZipFile, OSError):
            continue
        if conversation_title(member, path) != title:
            continue
        count = len(parse_messages(text))
        if count and count <= new_count:
            candidates.append((count, path))
    if not candidates:
        return None
    return max(candidates)[1]


def extract(zip_path, infos, dest, rename=None):
    """Copy the named members out of the export, flattened into one directory.

    Returns (written, collisions). Flattening is what makes two members collide: a zip can
    carry `media/x.pdf` and `docs/x.pdf`, and writing both under `x.pdf` leaves one of them
    on disk with the other's content and nothing said. The second one is written under a
    `~2` name and the collision is REPORTED, because a reader who opens the wrong PDF and
    concludes from it has no way of noticing.

    `rename` maps a member to the basename it should land under, which is how an attachment
    the chat named without an extension reaches the disk with the one its bytes earned.
    """
    if not infos:
        return [], []
    rename = rename or {}
    os.makedirs(dest, exist_ok=True)
    written = []
    collisions = []
    taken = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in infos:
            base = rename.get(info.filename) or os.path.basename(info.filename)
            target = os.path.join(dest, base)
            if base in taken or os.path.exists(target):
                collisions.append((info.filename, taken.get(base)))
                stem, ext = os.path.splitext(base)
                n = 2
                while os.path.exists(os.path.join(dest, "%s~%d%s" % (stem, n, ext))):
                    n += 1
                base = "%s~%d%s" % (stem, n, ext)
                target = os.path.join(dest, base)
            taken[base] = info.filename
            with archive.open(info) as src, open(target, "wb") as out:
                out.write(src.read())
            written.append(target)
    return written, collisions


def human_size(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0


def render_digest(context):
    """The readable delta, rendered from PLAIN DATA and nothing else.

    Every input is JSON, which is what lets `transcripts` re-render this file whole instead
    of splicing a new section onto the text of the old one. Splicing was the first design
    and it is a trap: the digest is then written by two different pieces of code, and the
    second one silently keeps whatever the first got wrong.
    """
    out = []
    add = out.append
    first = context.get("first")
    add("# %s — %s" % ("The whole conversation" if first else "What is new",
                       context["title"]))
    add("")
    add("- **New export:** `%s` — %d messages, %d attachments"
        % (os.path.basename(context["new_zip"]), context["new_total"], context["new_files"]))
    if first:
        add("- **Previous export:** none (`--first`). Everything below is the WHOLE "
            "conversation, not a delta: there is nothing to compare it against, so the "
            "anomaly checks that catch a wrong pair are silent here.")
    else:
        add("- **Previous export:** `%s` — %d messages, %d attachments"
            % (os.path.basename(context["old_zip"]), context["old_total"],
               context["old_files"]))
    if context["added"]:
        add("- **New:** %d messages (%s of `%s`) · %d attachments, %d voice notes"
            % (len(context["added"]), describe_runs(context["line_runs"]),
               os.path.basename(context["chat_member"]), len(context["added_files"]),
               len(context["added_audio"])))
    else:
        add("- **New:** nothing. The new export adds no message at all.")
    add("- **Unaccounted:** %s" % describe_tally(context["tally"]))
    add("- Generated on %s" % context["generated"])
    add("")

    anomalies = context["changed"] or context["removed"] or context["dropped_files"]
    if anomalies:
        add("## Anomalies")
        add("")
        add("A WhatsApp export only GROWS. What follows should not exist — check that the two "
            "files are really the same conversation before trusting this digest.")
        add("")
        for pair in context["changed"]:
            add("- **Message edited** (line %d → %d): `%s` → `%s`"
                % (pair["old_line"], pair["new_line"],
                   one_line(pair["old_raw"]), one_line(pair["new_raw"])))
        for gone in context["removed"]:
            add("- **Message gone** (line %d of the previous export): `%s`"
                % (gone["line"], one_line(gone["raw"])))
        for gone in context["dropped_files"]:
            add("- **Attachment gone**: `%s` was in the previous export and is not in this one"
                % os.path.basename(gone["name"]))
        add("")

    add("## New messages")
    add("")
    if context["added"]:
        add("```")
        for message in context["added"]:
            add(message["raw"])
        add("```")
    else:
        add("_None._")
    add("")

    add("## New attachments")
    add("")
    if context["added_files"]:
        add("| File | Size | Sender | When |")
        add("|---|---|---|---|")
        for entry in context["added_files"]:
            announced = os.path.basename(entry["name"])
            on_disk = entry.get("on_disk")
            shown = ("`%s` — saved as `%s`" % (announced, on_disk)
                     if on_disk and on_disk != announced else "`%s`" % announced)
            add("| %s | %s | %s | %s |"
                % (shown, human_size(entry["size"]),
                   entry["sender"] or "—", entry["when"] or "—"))
        add("")
        if context.get("extracted", True):
            reasons = renamed_reasons(context["added_files"])
            renamed = bool(reasons)
            add("Extracted into `%s`." % context["attachments_dir"])
            if renamed:
                add("")
                add("A row reading *saved as* is on disk under another name: %s."
                    % "; ".join(reasons))
        else:
            add("**Not extracted** (`--no-extract`): every file above is still inside the "
                "zip, and no `attachments/` directory was written.")
    else:
        add("_None._")
    add("")

    flagged = [entry for entry in context["added_files"] if entry.get("notes")]
    if flagged:
        add(PROBE_HEADING)
        add("")
        add("Each of these opens in nothing, or opens EMPTY — which reads as a document with "
            "nothing in it, rather than as a document that needs a step first. The step is "
            "under the file.")
        add("")
        extracted = context.get("extracted", True)
        for entry in flagged:
            shown = entry.get("on_disk") or os.path.basename(entry["name"])
            path = os.path.join(context["attachments_dir"], shown)
            add("- **`%s`**" % shown)
            for note in entry["notes"]:
                add("  - %s." % note["text"])
                if note.get("command") and extracted:
                    add("")
                    add("        %s" % note["command"].format(
                        path=shlex.quote(path),
                        stem=shlex.quote(os.path.splitext(path)[0])))
                    add("")
        if not extracted:
            add("")
            add("No command is offered: `--no-extract` wrote no file to run one on. Re-run "
                "`diff` without it.")
        add("")

    if context["modified_files"]:
        add("## Attachments whose CONTENT changed")
        add("")
        add("Same name, different bytes. The previous export held something else under this "
            "name; re-read it before trusting what was read then.")
        add("")
        for entry in context["modified_files"]:
            add("- `%s` (%s)" % (os.path.basename(entry["name"]), human_size(entry["size"])))
        add("")

    add(TRANSCRIPT_HEADING)
    add("")
    transcripts = context.get("transcripts") or {}
    if transcripts:
        add("%d voice note(s), transcribed locally." % len(transcripts))
        add("")
        for name in sorted(transcripts):
            entry = transcripts[name]
            add("### `%s`" % name)
            add("")
            add("_%s · %s_" % (entry.get("sender") or "—", entry.get("when") or "—"))
            add("")
            add(entry.get("text") or "_(silence: the transcriber returned no text)_")
            add("")
        pending = [n for n in context["added_audio"]
                   if os.path.basename(n) not in transcripts]
        if pending:
            add("**Still pending:** %s" % ", ".join("`%s`" % os.path.basename(n)
                                                    for n in sorted(pending)))
            add("")
    elif context["added_audio"]:
        add("%d new voice note(s). **This digest is incomplete until they are transcribed** — "
            "in a working conversation the voice note is usually where WHO IS WHO lives."
            % len(context["added_audio"]))
        add("")
        if not context.get("extracted", True):
            add("They were **not extracted** (`--no-extract`), so there is nothing to hand a "
                "transcriber. Re-run `diff` without `--no-extract` first.")
        else:
            add("1. Transcribe the attachments directory with the `asr:transcribe-audio` "
                "skill, which reads `.opus` directly.")
            add("2. Fold the transcripts back into this file:")
            add("")
            add("```sh")
            add("%s transcripts %s" % (context["self_name"], shlex.quote(context["out_dir"])))
            add("```")
    else:
        add("_None._ Nothing to transcribe this round.")
    add("")
    return "\n".join(out) + "\n"


RENAME_REASONS = {
    "collision": "it collided with another member of the zip, and the one on disk is the "
                 "SECOND of the two",
    "extension": "it arrived with no extension and is saved under the one its bytes earned",
}


def renamed_reasons(entries):
    """Why a row of the table says *saved as*, in the order the reasons are explained.

    Two different facts put a file on disk under another name, and they call for opposite
    reactions: a collision means the announced name is now ambiguous and the reader must
    open the one named here, while a repaired extension means nothing about the file changed
    but the name it opens under. One legend covering both says neither.
    """
    found = []
    for entry in entries:
        on_disk = entry.get("on_disk")
        announced = os.path.basename(entry["name"])
        if not on_disk or on_disk == announced:
            continue
        reason = "extension" if os.path.splitext(announced)[1] in ("", ".") else "collision"
        if reason not in found:
            found.append(reason)
    return [RENAME_REASONS[reason] for reason in found]


def describe_runs(runs):
    """`lines 923–972` for one block, and every block when the new messages are not one.

    A single spanning range is a lie whenever the delta is not contiguous: two arrivals with
    an untouched stretch between them read as one run covering text nobody added.
    """
    if not runs:
        return "no lines"
    parts = ["%d–%d" % (start, end) if end > start else "%d" % start for start, end in runs]
    return "lines " + ", ".join(parts)


TALLY_LABELS = (
    ("orphan_lines", "lines before the first message"),
    ("unparsed_headers", "lines that look like a header and opened no message"),
    ("extra_txt", "other .txt members"),
    ("duplicate_members", "entries the zip carries twice under one name"),
    ("markers_without_file", "attachment markers naming no file in the zip"),
    ("files_without_message", "new files no message announces"),
    ("collisions", "names that collided on extraction"),
    ("dropped_files", "attachments the previous export had"),
)


def describe_tally(tally):
    """What the run could not place. Zero across the board is the fact worth printing.

    Without this line the digest reports only what it managed to understand, and an export
    it understood half of looks exactly like one it understood entirely.
    """
    parts = ["%d %s" % (tally[key], label) for key, label in TALLY_LABELS if tally.get(key)]
    return "nothing — every line and every file is placed" if not parts else "; ".join(parts)


def one_line(text):
    return " ".join(text.split())


TRANSCRIPT_HEADING = "## New voice notes"
PROBE_HEADING = "## Attachments that need a step before reading"

# Bumped whenever `context.json` gains or loses a key `render_digest` indexes directly.
# `transcripts` refuses a directory written by any other version rather than failing on
# the missing key halfway through re-rendering the digest.
CONTEXT_SCHEMA = 2


def cmd_diff(args):
    new_zip = args.new
    chat_member, new_text = read_chat(new_zip)
    title = conversation_title(chat_member, new_zip)
    new_messages = parse_messages(new_text)
    if not new_messages:
        fail("%s parses to NO messages — `%s` is not a chat transcript in a shape this "
             "script reads. Every line of it would be reported as unaccounted."
             % (os.path.basename(new_zip), chat_member))

    if args.first:
        old_zip = None
    else:
        old_zip = args.previous or find_previous(new_zip, title, len(new_messages))
        if old_zip is None:
            fail("no earlier export of this conversation in %s — pass --previous, or --first "
                 "to read this export whole as the conversation's first reading."
                 % os.path.dirname(os.path.abspath(new_zip)))
    old_messages = []
    if old_zip is not None:
        _old_member, old_text = read_chat(old_zip)
        old_messages = parse_messages(old_text)

    delta = align(old_messages, new_messages)
    if old_zip is not None and delta.overlap < args.min_overlap and not args.force:
        fail("only %.0f%% of %s survives into the new export — the two do not look like the "
             "same conversation. Name the right one with --previous, --force to diff them "
             "anyway, or --first to read the new export whole.\n  why: %s"
             % (delta.overlap * 100, os.path.basename(old_zip),
                diagnose_pair(old_messages, new_messages, delta.overlap)))

    old_index = attachment_index(old_zip) if old_zip is not None else {}
    new_index = attachment_index(new_zip)
    added_infos, modified_infos, dropped_infos = diff_attachments(old_index, new_index)
    added_files = [(info, owning_message(info, new_messages)) for info in added_infos]
    added_audio = [info for info in added_infos if is_audio(info.filename)]
    probes = probe_new_files(new_zip, added_infos)

    out_dir = args.out or default_out_dir(new_zip)
    guard_out_dir(out_dir, args.overwrite)
    os.makedirs(out_dir, exist_ok=True)
    attachments_dir = os.path.join(out_dir, "attachments")
    collisions = []
    on_disk = []
    if not args.no_extract:
        if args.overwrite and os.path.isdir(attachments_dir):
            for entry in os.listdir(attachments_dir):
                target = os.path.join(attachments_dir, entry)
                if os.path.isfile(target):
                    os.unlink(target)
        written, collisions = extract(new_zip, added_infos, attachments_dir,
                                      rename={name: probe["rename"]
                                              for name, probe in probes.items()
                                              if probe["rename"]})
        on_disk = [os.path.basename(path) for path in written]

    tally = {
        "orphan_lines": count_orphan_lines(new_text),
        "unparsed_headers": count_unparsed_headers(new_text),
        "extra_txt": count_extra_txt(new_zip, chat_member),
        "duplicate_members": count_duplicate_members(new_zip),
        "markers_without_file": count_unmatched_markers(new_messages, new_index),
        "files_without_message": sum(1 for _info, owner in added_files if owner is None),
        "collisions": len(collisions),
        "dropped_files": len(dropped_infos),
    }

    context = {
        "schema": CONTEXT_SCHEMA,
        "title": title,
        "new_zip": new_zip,
        "old_zip": old_zip,
        "first": old_zip is None,
        "chat_member": chat_member,
        "new_total": len(new_messages),
        "old_total": len(old_messages),
        "new_files": len(new_index),
        "old_files": len(old_index),
        "added": [m.as_dict() for m in delta.added],
        "changed": [{"old_line": o.line, "new_line": n.line, "old_raw": o.raw,
                     "new_raw": n.raw} for o, n in delta.changed],
        "removed": [{"line": m.line, "raw": m.raw} for m in delta.removed],
        "added_files": [
            {
                "name": info.filename,
                "size": info.file_size,
                "sender": owner.sender if owner and owner.sender else None,
                "when": ("%s %s" % (owner.date, owner.time)) if owner else None,
                # The name ON DISK, which a collision changes: `extract` writes the second
                # `x.pdf` as `x~2.pdf`. The reader opens this one, not the announced name.
                "on_disk": on_disk[i] if i < len(on_disk) else None,
                # What the bytes say the file is, and what stands between it and a reader.
                "notes": probes[info.filename]["notes"] if info.filename in probes else [],
            }
            for i, (info, owner) in enumerate(added_files)
        ],
        "modified_files": [{"name": i.filename, "size": i.file_size} for i in modified_infos],
        "dropped_files": [{"name": i.filename, "size": i.file_size} for i in dropped_infos],
        "added_audio": [i.filename for i in added_audio],
        "attachments_dir": attachments_dir,
        "extracted": not args.no_extract,
        "out_dir": out_dir,
        "line_runs": line_runs(delta.added),
        "tally": tally,
        "transcripts": {},
        "generated": datetime.date.today().isoformat(),
        "self_name": os.path.basename(sys.argv[0]) or "wa_export.py",
    }

    digest_path = os.path.join(out_dir, "delta.md")
    with open(digest_path, "w", encoding="utf-8") as handle:
        handle.write(render_digest(context))

    # The same data the digest was rendered from, so `transcripts` re-renders the whole
    # file rather than splicing a section into text it did not write.
    with open(os.path.join(out_dir, "context.json"), "w", encoding="utf-8") as handle:
        json.dump(context, handle, ensure_ascii=False, indent=2)

    records_path = os.path.join(out_dir, "delta.jsonl")
    with open(records_path, "w", encoding="utf-8") as handle:
        for message in delta.added:
            handle.write(json.dumps(message.as_dict(), ensure_ascii=False) + "\n")

    if args.json:
        json.dump(
            {
                "title": title,
                "previous": old_zip,
                "first": old_zip is None,
                "messages": [m.as_dict() for m in delta.added],
                "attachments": [i.filename for i in added_infos],
                "needs_a_step": {name: [note["text"] for note in probe["notes"]]
                                 for name, probe in probes.items()},
                "modified": [i.filename for i in modified_infos],
                "audio": [i.filename for i in added_audio],
                "anomalies": {
                    "changed": [[o.line, n.line] for o, n in delta.changed],
                    "removed": [m.line for m in delta.removed],
                    "dropped": [i.filename for i in dropped_infos],
                },
                "tally": tally,
                "out_dir": out_dir,
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print("previous:  %s" % (os.path.basename(old_zip) if old_zip
                                 else "none (--first): the whole conversation, not a delta"))
        print("new:       %d messages, %d attachments (%d voice notes)"
              % (len(delta.added), len(added_infos), len(added_audio)))
        if probes:
            print("a step first: %d attachment(s) do not just open — see `%s` in the digest"
                  % (len(probes), PROBE_HEADING))
        if modified_infos:
            print("changed:   %d attachments kept their name" % len(modified_infos))
        if delta.message_anomalies or dropped_infos:
            print("WARNING:   %d edited, %d gone, %d attachments gone — see Anomalies in the "
                  "digest" % (len(delta.changed), len(delta.removed), len(dropped_infos)))
        print("unplaced:  %s" % describe_tally(tally))
        print("digest:    %s" % digest_path)
        if added_audio:
            print("audio:     %d to transcribe in %s" % (len(added_audio), attachments_dir))
    return 0


def guard_out_dir(out_dir, overwrite):
    """A digest never lands on top of another run's without being asked.

    `--out` pointed at a directory that already holds files leaves the reader with a
    delta.md from this run beside attachments from the last one, and no way to tell. The
    default directory is named after the zip, so the same zip re-run is the common case:
    `--overwrite` is how that is said out loud.
    """
    if overwrite or not os.path.isdir(out_dir):
        return
    if os.listdir(out_dir):
        fail("%s is not empty — it holds another run. Pass --overwrite to replace it, or "
             "--out to write somewhere else." % out_dir)


def line_runs(messages):
    """Contiguous [start, end] line runs the new messages occupy, in file order."""
    runs = []
    for message in sorted(messages, key=lambda m: m.line):
        start = message.line
        end = message.line + message.raw.count("\n")
        if runs and start <= runs[-1][1] + 1:
            runs[-1][1] = max(runs[-1][1], end)
        else:
            runs.append([start, end])
    return runs


def count_orphan_lines(text):
    """Non-empty lines before the first header, which `parse_messages` cannot place."""
    count = 0
    for line in text.splitlines():
        if HEADER_RE.match(line.translate(INVISIBLE)):
            return count
        if line.strip():
            count += 1
    return count


# A line OPENING with a date is what a header looks like from a distance, whatever shape the
# rest of it takes. The anchor is the date and not a clock, which is what keeps the count
# quiet: measured across 17 real exports, a clock anywhere near the start of a line also
# matched two ordinary sentences, and a tally that cries wolf twice is one nobody reads a
# third time.
DATE_START_RE = re.compile(r"^\[?[ ]*\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b")


def count_unparsed_headers(text):
    """Lines that look like a header and did not open a message.

    Measured: the same clock written with U+00A0 instead of U+202F fails to parse, and the
    line is then GLUED onto the message above it — changing that message's text, and with it
    its identity across two exports. Nothing said so. This counts the shapes the parser does
    not know, including the ones nobody has thought of yet, so an export it half-understood
    stops looking like one it understood entirely.
    """
    count = 0
    for line in text.splitlines():
        clean = line.translate(INVISIBLE)
        if HEADER_RE.match(clean):
            continue
        if DATE_START_RE.match(clean):
            count += 1
    return count


def count_duplicate_members(zip_path):
    """Entries a zip carries twice under one name.

    The index is keyed by name, so the second entry replaces the first and the file is gone
    from the delta without a word — the same class as every other item on this line, and the
    last one the lens found.
    """
    seen = set()
    duplicates = 0
    with zipfile.ZipFile(zip_path) as archive:
        for info in zip_members(archive):
            if info.is_dir():
                continue
            if info.filename in seen:
                duplicates += 1
            seen.add(info.filename)
    return duplicates


def count_extra_txt(zip_path, chat_member):
    with zipfile.ZipFile(zip_path) as archive:
        return sum(1 for i in zip_members(archive)
                   if i.filename.lower().endswith(".txt") and i.filename != chat_member)


def count_unmatched_markers(messages, index):
    """Attachment markers naming a file no member of the zip carries."""
    carried = [{form(name) for name in index} for form in NAME_FORMS]
    missing = 0
    for message in messages:
        for named in message.attachments:
            if not any(form(named) in names for form, names in zip(NAME_FORMS, carried)):
                missing += 1
    return missing


def default_out_dir(new_zip):
    stem = os.path.splitext(os.path.basename(new_zip))[0]
    return os.path.join(os.path.dirname(os.path.abspath(new_zip)), stem + "-delta")


def cmd_transcripts(args):
    """Re-render the digest with the transcripts in it, from the data `diff` recorded.

    The digest is written in ONE place, `render_digest`. An earlier version spliced the new
    section onto the text of the old file, which meant two pieces of code wrote one
    document: everything below the splice point was whatever the previous run produced,
    preserved even when this run would have written it differently.
    """
    out_dir = args.dir
    digest_path = os.path.join(out_dir, "delta.md")
    context_path = os.path.join(out_dir, "context.json")
    if not os.path.exists(context_path):
        fail("%s has no context.json — run `diff` first (a delta directory from an older "
             "version of this script has to be re-diffed)." % out_dir)
    transcript_path = args.transcript or find_transcript(out_dir)
    if transcript_path is None:
        fail("no transcript.jsonl in %s — transcribe the voice notes first." % out_dir)

    by_file = {}
    with open(transcript_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            name = os.path.basename(record.get("file", ""))
            if name:
                by_file[name] = (record.get("text") or "").strip()
    if not by_file:
        fail("%s carries no transcript at all." % transcript_path)

    with open(context_path, encoding="utf-8") as handle:
        context = json.load(handle)
    if context.get("schema") != CONTEXT_SCHEMA:
        fail("%s was written by another version of this script (context schema %s, this one "
             "reads %d) — re-run `diff` on the zip to rebuild it."
             % (context_path, context.get("schema", "absent"), CONTEXT_SCHEMA))

    messages = context.get("added", [])
    transcripts = {}
    for name in sorted(by_file):
        owner = owner_of(name, messages)
        transcripts[name] = {
            "text": by_file[name],
            "sender": owner.get("sender") if owner else None,
            "when": ("%s %s" % (owner["date"], owner["time"])) if owner else None,
        }
    context["transcripts"] = transcripts

    with open(digest_path, "w", encoding="utf-8") as handle:
        handle.write(render_digest(context))
    with open(context_path, "w", encoding="utf-8") as handle:
        json.dump(context, handle, ensure_ascii=False, indent=2)

    pending = [os.path.basename(n) for n in context.get("added_audio", [])
               if os.path.basename(n) not in transcripts]
    print("folded %d voice notes into %s" % (len(by_file), digest_path))
    if pending:
        print("pending:   %d voice note(s) still without a transcript: %s"
              % (len(pending), ", ".join(sorted(pending))))
    return 0


def owner_of(name, messages):
    """The same search as `owning_message`, over the records `diff` wrote to disk."""
    return owner_by_name(name, messages,
                         lambda message: message.get("attachments", []))


def find_transcript(out_dir):
    for candidate in (
        os.path.join(out_dir, "transcript.jsonl"),
        os.path.join(out_dir, "attachments", "transcript.jsonl"),
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def fail(message):
    sys.stderr.write("wa_export: %s\n" % message)
    raise SystemExit(2)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="wa_export.py", description=__doc__.splitlines()[0]
    )
    sub = parser.add_subparsers(dest="command")

    diff = sub.add_parser("diff", help="what the new export carries that the previous one did not")
    diff.add_argument("new", metavar="NEW.zip")
    pair = diff.add_mutually_exclusive_group()
    pair.add_argument("--previous", metavar="OLD.zip",
                      help="previous export; by default the latest earlier one of the same conversation beside it")
    pair.add_argument("--first", action="store_true",
                      help="no previous export exists: read this one whole, as the conversation's first reading")
    diff.add_argument("--out", metavar="DIR", help="where to write the digest and the new attachments")
    diff.add_argument("--no-extract", action="store_true",
                      help="digest only, leaving the attachments inside the zip")
    diff.add_argument("--json", action="store_true", help="write the delta to stdout as JSON")
    diff.add_argument("--min-overlap", type=float, default=0.5,
                      help="minimum overlap between the two exports (0-1, default 0.5)")
    diff.add_argument("--force", action="store_true",
                      help="diff even when the overlap is below the minimum")
    diff.add_argument("--overwrite", action="store_true",
                      help="replace a delta directory that already holds a run")
    diff.set_defaults(func=cmd_diff)

    transcripts = sub.add_parser(
        "transcripts", help="fold transcript.jsonl into the digest, after transcribing"
    )
    transcripts.add_argument("dir", metavar="DIR")
    transcripts.add_argument("--transcript", metavar="PATH")
    transcripts.set_defaults(func=cmd_transcripts)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
