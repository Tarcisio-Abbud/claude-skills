---
name: export-delta
description: Read a WhatsApp conversation export (.zip) by its DELTA against the last export — only the messages and attachments that arrived since, with the new voice notes transcribed. Use when a .zip export of a chat has to be processed, when a conversation is the evidence for something (a payment, a decision, who is who), or when a second export of a conversation already read arrives.
---

# Read a WhatsApp export by its delta

Every export of a conversation carries the **whole** history again. Re-reading one to learn
the fifty lines that arrived since the last export burns the window on text already read, and
the reader who skims instead misses the one message that mattered. `wa_export.py` hands over
the delta: new messages, new attachments, and a place to put the transcripts.

## Run it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/wa_export.py" diff <NEW.zip>
```

`${CLAUDE_PLUGIN_ROOT}` is set only while this skill runs as an installed PLUGIN. Anywhere
else it expands to nothing and the line dies as `python3 /bin/wa_export.py`; then spell the
path from THIS file, where the script is `../../bin/wa_export.py`.

Stdlib only — the system `python3` runs it. The previous export is found beside the new one
by the conversation's own name; `--previous OLD.zip` names it when the two sit apart. Every
flag is in `--help`.

The run writes `<NEW-stem>-delta/` beside the zip: `delta.md` to read, `delta.jsonl` to
process, `attachments/` holding the new attachments extracted, and `context.json`, the data
both files were rendered from. A directory that already holds a run is refused: `--overwrite`
replaces it, `--out` writes elsewhere.

## The four steps

1. **Diff.** Run the command above. It prints what it found and where it wrote it.
2. **Transcribe, when it reports voice notes.** Point `asr:transcribe-audio` at the
   `attachments/` directory it names. In a working conversation the voice note is where *who is
   who* lives — a supplier's real name behind a payment, the identity a bank statement
   spells as somebody else.
3. **Fold the transcripts back**, so one file carries the whole delta:
   `wa_export.py transcripts <the delta directory>`.
4. **Read `delta.md`.** Done when `## New voice notes` names no pending transcription and
   every new attachment has been opened or ruled out.

## What the digest tells you, and what it does not

**An `## Anomalies` section means the pair is suspect.** A WhatsApp export only grows, so an
edited or vanished message — or an attachment the previous export had and this one does not —
says the two zips are probably different conversations, or the "new" one is the older. Settle
that before trusting a single line of the delta.

**The `Unaccounted` line is the digest's own confession.** It counts what the run could not
place: lines before the first message, other `.txt` members, attachment markers naming a file
the zip does not carry, new files no message announces, names that collided on extraction,
attachments the previous export had. `nothing` means every line and every file is placed.
Anything else is a document somebody is waiting for, or a sender the delta cannot name — and
it is read BEFORE the delta, because it says how much of the delta to believe.

**A file under `## Attachments whose CONTENT changed` was read before under that name.**
Same name, different bytes: whatever was concluded from the old one is unproven.

**The attachment is usually worth more than the message that carries it.** The message says
a payment was requested; the PDF beside it says the amount, the due date and who is being
paid. Open them.

**A message proves what was REQUESTED, never what happened.** The delta is one side's
account. Confirm anything consequential against the system that records the fact.

## Five things the format does, that a naive diff gets wrong

Every one is measured on a real export, and every one is already handled — they are here so a
surprising digest reads as expected behaviour rather than a bug.

- **The clock drifts between exports.** An untouched message moved from `16:04` to `16:05`
  across two exports eleven days apart. Messages are matched on date, sender and text; the
  minute is decoration.
- **A repeated filename gains a suffix.** A second `invoice (1).pdf` is stored as
  `invoice (1)-1.pdf`, and the message names the suffixed form. The exact name wins over the
  folded one, so the new file is credited to the message that actually sent it.
- **There are two attachment markers.** Android writes `NAME (arquivo anexado)`, iOS and
  `_chat.txt` write `<anexado: NAME>`, each translated per locale. One export of 151
  attachments uses the second shape alone.
- **A filename can arrive as mojibake.** A zip declares UTF-8 with one flag bit, and an
  export writes UTF-8 bytes with the bit clear: `ALTERAÇÃO` then reads as `ALTERAC╠ºA╠âO` and
  matches no message. The name is repaired, and an accent is composed before comparing —
  iOS stores it decomposed while the chat text composes it.
- **The conversation is not always the biggest `.txt`.** A bank return file sent as an
  attachment outweighs the transcript. The member is chosen by NAME first, so the export
  does not silently parse to zero messages.

## What the pair check refuses

The two exports must look like one conversation, measured as the share of the OLD export the
new one still carries — an export only grows, so the question is containment. Below
`--min-overlap` (0.5 by default) the run refuses rather than diff two unrelated zips;
`--force` diffs them anyway. Measuring the other direction — the share of the NEW export that
is old — refuses a real pair whose conversation exploded between exports.

**A refusal is not always a wrong pair.** Two exports of one conversation saved under
different phone locales spell every date differently (`8/19/26` against `19/08/2026`), so no
message matches and the run refuses a pair that is real. The refusal is the safe direction —
the delta would otherwise be the whole history — and the fix is to export both sides again
from one locale, not `--force`. Two exports can also share a title and be different
conversations: same contact, two threads. The message the run prints names the file it
refused; check that file before overriding it.
