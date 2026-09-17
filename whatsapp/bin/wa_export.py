#!/usr/bin/env python3
"""Diff two WhatsApp export .zip files and emit only what is new.

A WhatsApp export is cumulative: every export of a conversation carries the whole history
again. Re-reading one costs the whole conversation to learn the handful of messages that
arrived since the last export. This script hands over the delta — the new messages, the new
attachments extracted into a dated directory, and the ready-to-paste command that
transcribes the new voice notes.

    wa_export.py diff NEW.zip [--previous OLD.zip] [--out DIR]
    wa_export.py transcripts DIR

Stdlib only. Run it with any Python 3.8+; the transcription step is a separate tool.
"""
import argparse
import datetime
import difflib
import json
import os
import re
import sys
import unicodedata
import zipfile

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
    def anomalies(self):
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


def owning_message(info, messages):
    """The message that announced this attachment, or None when the chat never names it.

    EXACT name first, folded name only as a fallback. The `-1` suffix exists precisely
    because an earlier attachment already took the bare name, so folding it away first
    hands a September file to the August message that sent its namesake — measured, and
    the reason the two passes are not one.
    """
    exact = plain_name(info.filename)
    for message in messages:
        for named in message.attachments:
            if plain_name(named) == exact:
                return message
    wanted = normalize_attachment(info.filename)
    for message in messages:
        for named in message.attachments:
            if normalize_attachment(named) == wanted:
                return message
    return None


def is_audio(name):
    return name.lower().endswith(AUDIO_EXTS)


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


def extract(zip_path, infos, dest):
    """Copy the named members out of the export, flattened into one directory.

    Returns (written, collisions). Flattening is what makes two members collide: a zip can
    carry `media/x.pdf` and `docs/x.pdf`, and writing both under `x.pdf` leaves one of them
    on disk with the other's content and nothing said. The second one is written under a
    `~2` name and the collision is REPORTED, because a reader who opens the wrong PDF and
    concludes from it has no way of noticing.
    """
    if not infos:
        return [], []
    os.makedirs(dest, exist_ok=True)
    written = []
    collisions = []
    taken = {}
    with zipfile.ZipFile(zip_path) as archive:
        for info in infos:
            base = os.path.basename(info.filename)
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
    add("# What is new — %s" % context["title"])
    add("")
    add("- **New export:** `%s` — %d messages, %d attachments"
        % (os.path.basename(context["new_zip"]), context["new_total"], context["new_files"]))
    add("- **Previous export:** `%s` — %d messages, %d attachments"
        % (os.path.basename(context["old_zip"]), context["old_total"], context["old_files"]))
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
            add("| `%s` | %s | %s | %s |"
                % (os.path.basename(entry["name"]), human_size(entry["size"]),
                   entry["sender"] or "—", entry["when"] or "—"))
        add("")
        add("Extracted into `%s`." % context["attachments_dir"])
    else:
        add("_None._")
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
        add("1. Transcribe the attachments directory with the `asr:transcribe-audio` skill, "
            "which reads `.opus` directly.")
        add("2. Fold the transcripts back into this file:")
        add("")
        add("```sh")
        add("%s transcripts %s" % (context["self_name"], shell_quote(context["out_dir"])))
        add("```")
    else:
        add("_None._ Nothing to transcribe this round.")
    add("")
    return "\n".join(out) + "\n"


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


def shell_quote(path):
    return path if re.match(r"^[\w@%+=:,./-]+$", path) else "'%s'" % path.replace("'", "'\\''")


TRANSCRIPT_HEADING = "## New voice notes"


def cmd_diff(args):
    new_zip = args.new
    chat_member, new_text = read_chat(new_zip)
    title = conversation_title(chat_member, new_zip)
    new_messages = parse_messages(new_text)
    if not new_messages:
        fail("%s parses to NO messages — `%s` is not a chat transcript in a shape this "
             "script reads. Every line of it would be reported as unaccounted."
             % (os.path.basename(new_zip), chat_member))

    old_zip = args.previous or find_previous(new_zip, title, len(new_messages))
    if old_zip is None:
        fail("no earlier export of this conversation in %s — pass --previous."
             % os.path.dirname(os.path.abspath(new_zip)))
    old_member, old_text = read_chat(old_zip)
    old_messages = parse_messages(old_text)

    delta = align(old_messages, new_messages)
    if delta.overlap < args.min_overlap and not args.force:
        fail("only %.0f%% of %s survives into the new export — the two do not look like the "
             "same conversation. Name the right one with --previous, or --force to diff "
             "them anyway." % (delta.overlap * 100, os.path.basename(old_zip)))

    old_index = attachment_index(old_zip)
    new_index = attachment_index(new_zip)
    added_infos, modified_infos, dropped_infos = diff_attachments(old_index, new_index)
    added_files = [(info, owning_message(info, new_messages)) for info in added_infos]
    added_audio = [info for info in added_infos if is_audio(info.filename)]

    out_dir = args.out or default_out_dir(new_zip)
    guard_out_dir(out_dir, args.overwrite)
    os.makedirs(out_dir, exist_ok=True)
    attachments_dir = os.path.join(out_dir, "attachments")
    collisions = []
    if not args.no_extract:
        if args.overwrite and os.path.isdir(attachments_dir):
            for entry in os.listdir(attachments_dir):
                target = os.path.join(attachments_dir, entry)
                if os.path.isfile(target):
                    os.unlink(target)
        _written, collisions = extract(new_zip, added_infos, attachments_dir)

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
        "title": title,
        "new_zip": new_zip,
        "old_zip": old_zip,
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
            }
            for info, owner in added_files
        ],
        "modified_files": [{"name": i.filename, "size": i.file_size} for i in modified_infos],
        "dropped_files": [{"name": i.filename, "size": i.file_size} for i in dropped_infos],
        "added_audio": [i.filename for i in added_audio],
        "attachments_dir": attachments_dir,
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
                "messages": [m.as_dict() for m in delta.added],
                "attachments": [i.filename for i in added_infos],
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
        print("previous:  %s" % os.path.basename(old_zip))
        print("new:       %d messages, %d attachments (%d voice notes)"
              % (len(delta.added), len(added_infos), len(added_audio)))
        if modified_infos:
            print("changed:   %d attachments kept their name" % len(modified_infos))
        if delta.anomalies or dropped_infos:
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
    exact = {plain_name(name) for name in index}
    folded = {normalize_attachment(name) for name in index}
    missing = 0
    for message in messages:
        for named in message.attachments:
            if plain_name(named) not in exact and normalize_attachment(named) not in folded:
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
    """Same two passes as `owning_message`, over the records `diff` wrote."""
    exact = plain_name(name)
    for message in messages:
        for named in message.get("attachments", []):
            if plain_name(named) == exact:
                return message
    wanted = normalize_attachment(name)
    for message in messages:
        for named in message.get("attachments", []):
            if normalize_attachment(named) == wanted:
                return message
    return None


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
    diff.add_argument("--previous", metavar="OLD.zip",
                      help="previous export; by default the latest earlier one of the same conversation beside it")
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
