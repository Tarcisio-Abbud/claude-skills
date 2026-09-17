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
import zipfile

AUDIO_EXTS = (".opus", ".ogg", ".m4a", ".mp3", ".wav", ".aac", ".flac", ".amr")

# WhatsApp writes U+200E (LEFT-TO-RIGHT MARK) before an attachment marker and U+202F
# (NARROW NO-BREAK SPACE) between the clock and an am/pm suffix. Neither is visible and
# both break a naive comparison, so they are stripped before anything else reads the text.
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

# `<name> (arquivo anexado)` and its siblings. The locale word list is open-ended by
# design: an unknown locale falls back to matching the bare filename against the zip.
ATTACHED_RE = re.compile(
    r"(?P<name>\S.*?)[  ]*\((?:arquivo anexado|archivo adjunto|file attached|"
    r"attached|fichier joint|Datei angehängt)\)",
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
        return [m.group("name").strip() for m in ATTACHED_RE.finditer(self.body)]

    def as_dict(self):
        return {
            "index": self.index,
            "line": self.line,
            "date": self.date,
            "time": self.time,
            "sender": self.sender,
            "body": self.body,
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


def read_chat(zip_path):
    """Return (member name, decoded text) for the conversation inside an export."""
    with zipfile.ZipFile(zip_path) as archive:
        members = [i for i in archive.infolist() if i.filename.lower().endswith(".txt")]
        if not members:
            raise ValueError("%s carries no .txt: not a WhatsApp export" % zip_path)
        chat = min(members, key=lambda i: (i.filename.count("/"), -i.file_size))
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
        for info in archive.infolist():
            if info.is_dir() or info.filename == chat_member:
                continue
            index[info.filename] = info
    return index


def normalize_attachment(name):
    """Fold the `-1` WhatsApp appends when two attachments share a name."""
    stem, ext = os.path.splitext(os.path.basename(name).translate(INVISIBLE).strip())
    return (DEDUP_SUFFIX_RE.sub("", stem).strip().casefold(), ext.casefold())


class Delta:
    """What the new export carries that the old one did not."""

    def __init__(self, added, changed, removed, matched, total_new):
        self.added = added          # messages present only in the new export
        self.changed = changed      # (old, new) pairs whose key moved — never expected
        self.removed = removed      # messages the new export dropped — never expected
        self.matched = matched      # messages aligned across the two
        self.total_new = total_new

    @property
    def anomalies(self):
        return self.changed or self.removed

    @property
    def overlap(self):
        """Share of the new export that the old one already carried.

        Two exports of the SAME conversation overlap almost entirely; a low value means the
        pair is wrong, and that is worth refusing rather than diffing.
        """
        return self.matched / self.total_new if self.total_new else 1.0


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
    return Delta(added, changed, removed, matched, len(new_messages))


def diff_attachments(old_index, new_index):
    """(added, modified) — members the new export gained, and members whose bytes moved."""
    added, modified = [], []
    for name, info in new_index.items():
        previous = old_index.get(name)
        if previous is None:
            added.append(info)
        elif previous.CRC != info.CRC or previous.file_size != info.file_size:
            modified.append(info)
    added.sort(key=lambda i: i.filename)
    modified.sort(key=lambda i: i.filename)
    return added, modified


def owning_message(info, messages):
    """The message that announced this attachment, or None when the chat never names it.

    EXACT name first, folded name only as a fallback. The `-1` suffix exists precisely
    because an earlier attachment already took the bare name, so folding it away first
    hands a September file to the August message that sent its namesake — measured, and
    the reason the two passes are not one.
    """
    exact = os.path.basename(info.filename).translate(INVISIBLE).strip()
    for message in messages:
        for named in message.attachments:
            if os.path.basename(named).translate(INVISIBLE).strip() == exact:
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
    """Copy the named members out of the export, flattened into one directory."""
    if not infos:
        return []
    os.makedirs(dest, exist_ok=True)
    written = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in infos:
            target = os.path.join(dest, os.path.basename(info.filename))
            with archive.open(info) as src, open(target, "wb") as out:
                out.write(src.read())
            written.append(target)
    return written


def human_size(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0


def render_digest(context):
    """The readable delta. One file, so the reader is never sent back to the export."""
    out = []
    add = out.append
    add("# What is new — %s" % context["title"])
    add("")
    add("- **New export:** `%s` — %d messages, %d attachments"
        % (os.path.basename(context["new_zip"]), context["new_total"], context["new_files"]))
    add("- **Previous export:** `%s` — %d messages, %d attachments"
        % (os.path.basename(context["old_zip"]), context["old_total"], context["old_files"]))
    delta = context["delta"]
    if delta.added:
        add("- **New:** %d messages (lines %d–%d of `%s`) · %d attachments, %d voice notes"
            % (len(delta.added), delta.added[0].line, context["last_line"],
               os.path.basename(context["chat_member"]), len(context["added_files"]),
               len(context["added_audio"])))
    else:
        add("- **New:** nothing. The new export adds no message at all.")
    add("- Generated on %s" % datetime.date.today().isoformat())
    add("")

    if delta.anomalies:
        add("## Anomalies")
        add("")
        add("A WhatsApp export only GROWS. What follows should not exist — check that the two "
            "files are really the same conversation before trusting this digest.")
        add("")
        for old, new in delta.changed:
            add("- **Message edited** (line %d → %d): `%s` → `%s`"
                % (old.line, new.line, one_line(old.raw), one_line(new.raw)))
        for gone in delta.removed:
            add("- **Message gone** (line %d of the previous export): `%s`"
                % (gone.line, one_line(gone.raw)))
        add("")

    add("## New messages")
    add("")
    if delta.added:
        add("```")
        for message in delta.added:
            add(message.raw)
        add("```")
    else:
        add("_None._")
    add("")

    add("## New attachments")
    add("")
    if context["added_files"]:
        add("| File | Size | Sender | When |")
        add("|---|---|---|---|")
        for info, owner in context["added_files"]:
            add("| `%s` | %s | %s | %s |"
                % (os.path.basename(info.filename), human_size(info.file_size),
                   (owner.sender if owner and owner.sender else "—"),
                   ("%s %s" % (owner.date, owner.time)) if owner else "—"))
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
        for info in context["modified_files"]:
            add("- `%s` (%s)" % (os.path.basename(info.filename), human_size(info.file_size)))
        add("")

    add("## New voice notes")
    add("")
    if context["added_audio"]:
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

    old_zip = args.previous or find_previous(new_zip, title, len(new_messages))
    if old_zip is None:
        fail("no earlier export of this conversation in %s — pass --previous."
             % os.path.dirname(os.path.abspath(new_zip)))
    old_member, old_text = read_chat(old_zip)
    old_messages = parse_messages(old_text)

    delta = align(old_messages, new_messages)
    if delta.overlap < args.min_overlap and not args.force:
        fail("only %.0f%% of the new export appears in %s — the two do not look like the "
             "same conversation. Name the right one with --previous, or --force to diff "
             "them anyway." % (delta.overlap * 100, os.path.basename(old_zip)))

    old_index = attachment_index(old_zip)
    new_index = attachment_index(new_zip)
    added_infos, modified_infos = diff_attachments(old_index, new_index)
    added_files = [(info, owning_message(info, new_messages)) for info in added_infos]
    added_audio = [info for info in added_infos if is_audio(info.filename)]

    out_dir = args.out or default_out_dir(new_zip)
    os.makedirs(out_dir, exist_ok=True)
    attachments_dir = os.path.join(out_dir, "attachments")
    if not args.no_extract:
        extract(new_zip, added_infos, attachments_dir)

    context = {
        "title": title,
        "new_zip": new_zip,
        "old_zip": old_zip,
        "chat_member": chat_member,
        "new_total": len(new_messages),
        "old_total": len(old_messages),
        "new_files": len(new_index),
        "old_files": len(old_index),
        "delta": delta,
        "added_files": added_files,
        "modified_files": modified_infos,
        "added_audio": added_audio,
        "attachments_dir": attachments_dir,
        "out_dir": out_dir,
        "last_line": last_line_of(new_text, delta),
        "self_name": os.path.basename(sys.argv[0]) or "wa_export.py",
    }

    digest_path = os.path.join(out_dir, "delta.md")
    with open(digest_path, "w", encoding="utf-8") as handle:
        handle.write(render_digest(context))

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
                },
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
        if delta.anomalies:
            print("WARNING:   %d edited, %d gone — see Anomalies in the digest"
                  % (len(delta.changed), len(delta.removed)))
        print("digest:    %s" % digest_path)
        if added_audio:
            print("audio:     %d to transcribe in %s" % (len(added_audio), attachments_dir))
    return 0


def last_line_of(new_text, delta):
    if not delta.added:
        return 0
    last = delta.added[-1]
    return last.line + last.raw.count("\n")


def default_out_dir(new_zip):
    stem = os.path.splitext(os.path.basename(new_zip))[0]
    return os.path.join(os.path.dirname(os.path.abspath(new_zip)), stem + "-delta")


def cmd_transcripts(args):
    """Fold what the transcriber wrote back into the digest, under the audio heading."""
    out_dir = args.dir
    digest_path = os.path.join(out_dir, "delta.md")
    if not os.path.exists(digest_path):
        fail("%s has no delta.md — run `diff` first." % out_dir)
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

    messages = []
    records_path = os.path.join(out_dir, "delta.jsonl")
    if os.path.exists(records_path):
        with open(records_path, encoding="utf-8") as handle:
            messages = [json.loads(line) for line in handle if line.strip()]

    section = [TRANSCRIPT_HEADING, "", "%d voice note(s), transcribed locally." % len(by_file), ""]
    for name in sorted(by_file):
        owner = owner_of(name, messages)
        who = owner["sender"] if owner and owner.get("sender") else "—"
        when = "%s %s" % (owner["date"], owner["time"]) if owner else "—"
        section.append("### `%s`" % name)
        section.append("")
        section.append("_%s · %s_" % (who, when))
        section.append("")
        section.append(by_file[name] or "_(silence: the transcriber returned no text)_")
        section.append("")

    with open(digest_path, encoding="utf-8") as handle:
        digest = handle.read()
    head, sep, _tail = digest.partition(TRANSCRIPT_HEADING)
    if not sep:
        fail("%s has no %r section." % (digest_path, TRANSCRIPT_HEADING))
    with open(digest_path, "w", encoding="utf-8") as handle:
        handle.write(head + "\n".join(section))
    print("folded %d voice notes into %s" % (len(by_file), digest_path))
    return 0


def owner_of(name, messages):
    """Same two passes as `owning_message`, over the records `diff` wrote."""
    exact = os.path.basename(name).translate(INVISIBLE).strip()
    for message in messages:
        for named in message.get("attachments", []):
            if os.path.basename(named).translate(INVISIBLE).strip() == exact:
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
