# The queue contract: `next-steps.md` + `done-log.md`, written only by `tk-queue`

Single source for a project's queue of pending items. Two sibling files in the project's
auto-memory (`~/.claude/projects/<cwd-slug>/memory/`, each with a pointer in `MEMORY.md`):

- **`next-steps.md`** — OPEN items only, the queue `/tk:kickoff` dispatches.
- **`done-log.md`** — what left the queue (FEITO or DESCARTADO), when, and how. Feeds
  progress reports; consult it when a queue item touches ground already worked.

Both are written ONLY through the deterministic script **`tk-queue`** (`../bin/tk-queue`
relative to this file) — never by hand-editing. The script is what guarantees a resolved
item actually LEAVES the queue: `done`/`cancel` move it to the log in one command, log
written first. A crash between the two writes is recognised by the next `done`, `cancel`
or `migrate`, which finishes the queue write, leaves the entry standing and adds no
second line. Any session where an item is born or dies calls the script on the spot.

**The commands, the flags and each field's shape live in `tk-queue --help` and the
subcommands' own `--help`** — this file carries only what those helps do not confess.
`<id>` is accepted as displayed (`T006`) or bare (`6`). What a `--criterion` may ANCHOR on is
one of those: `../skills/verify/SKILL.md`, *The anchor outlives the tree*.

## Priority, claims and two writers

**Priority is the ORDER of the file, global** — no score, no hidden heuristic. `add`
appends; `bump "<id>"` moves one to the top, and the last bump wins it; the package modes
take the top of what `tk-queue pack` reports eligible. A real queue's `##` headings are
cosmetic: `list` groups by the **Project:** field.

A second `claim` is REFUSED naming the owner and the moment — that refusal is how two
sibling sessions on one queue stop executing the same item. `release "<id>"` does NOT
demand the owner's name — a dead session would leave the item unreachable — so it prints
WHOSE claim it dropped. There is deliberately no `edit --claimed`, and `done` on an item
claimed by ANOTHER owner succeeds silently.

Two writers at once are safe: every mutating command holds an exclusive lock on the memory
dir for its whole read-modify-write, `migrate --dry-run` included. When an id is not among
the open items the script says WHY — already in the done-log, still ticked `[x]`, never
allocated, or removed by another writer. None of those mean "invent it again": re-read with
`tk-queue list` instead of adding a replacement, which is how a queue grows duplicates.

## The stderr lines

Every command but `report` prints the memory dir it resolved on **stderr** before acting —
`list` and `pack` too. That target is INFERRED, from `--dir` or the cwd, and a shell that
kept its cwd has landed an `edit` on a homonymous item of another project. Read it.

**A preview's report is not evidence.** `migrate --dry-run` prints a report byte-identical
to a real run's; the banner that tells them apart is on **stderr**.

## The two size ceilings

An item is a pending action, not an essay — durable context goes to a memory file or wiki
page, linked with `[[slug]]`. The script enforces two ceilings:

- **the block ceiling**, on the whole item: `add` always; `edit` whenever a prose flag
  (`--text`, `--criterion`, `--risk`, `--deferred`) grows the item.
- **the field ceiling**, on each field VALUE, on `add`, `edit` and the closes
  (`--how`/`--why`/`--summary`/`--note`) alike — small for the fields short by construction
  (`--class`, `--effort`, `--project`), larger for prose.

The short fields are the only ones exempt from the block ceiling, deliberately: gating them
meant a legacy oversized item needed `--force` merely to gain a project tag, which trains
the caller to type `--force` and disarms the guard where it matters. It is safe only
because those fields are small AND replaced rather than appended. Neither ceiling holds
alone: each has let an item past the other. `--force` raises both, for the rare exception.

## The WIP cap

A third ceiling bounds the QUEUE, not an item: `add` is refused once the open items reach
`max-open-items` in the site file, counted across every queue on this machine's roster.
Summing the roster stops `--dir` naming another queue to get past it; unset means NO cap.
No bypass, `--force` included. Room is made by taking an item out, `done` or `cancel`, and
the refusal names both. Still open at the cap: `edit --text` on an item that exists, and
`handoff`.

## The field chain

An item is free text followed by its **field chain** — the run of `**Field:** value.`
segments ENDING the first line, beginning at `**Class:**`. Every reader and writer locates
a field there, never at "the last marker in the block": a legacy item can carry the marker
shape in prose, and the last match is then the note, edited and reported as the field. A
segment ahead of the anchor is prose, and so is any marker inside a **code span** — the way
OUT for an item whose text quotes one. Unquoted, the mutating commands refuse it and ask
for a rephrase; ambiguity left over is REFUSED, never guessed, because `--risk none`
guessing wrong deletes prose that cannot be recovered. `migrate` is the repair, and the
repair writes NO done-log line: it folds a chain off the first line onto it, writes a
class value in Portuguese as the enum, and names every item it declines, with the
reason. Only what it declines needs `cancel` + re-add.

One `parse_item` reads the block — head, title, chain, prose — and one `render_item` writes
it back byte for byte; nothing else reads it by regex. That ambiguity answered twice, by
the reader that found a field and then by the writer that amended it, overwrote an item's
prose and deleted a real `**Risk:**`. Bytes no reader can see (a BOM below byte 0, a
non-breaking space after the checkbox, UTF-16) are repaired at the door, in the two heads an
ID lives in and nowhere else, and announced.

## Which IDs are taken

The script counts an ID as allocated only where a WRITER puts one: at an item's marker in
either file (`- [ ] **T007** — …`) and in a done-log entry's ID column. A T-number anywhere
else is PROSE — a note, a summary, a sibling tracker's ticket — and burns no number. Two
tolerances at the marker, both one-way (they only make MORE IDs count as taken):

- **Decoration before the ID counts; a word does not.** `- [x] ✅ **T020** — …` and
  `- [x] ~~**T012**~~ — …` are allocations; one word before the ID and the line is prose.
- **The checkbox is not read.** A `- [ ] **T005**` line parked in the done-log is still
  spent: refusing to see it is the direction that hands a number out twice.

Both decide what `add` hands out next and what the "never allocated" diagnostic means.
Neither is a licence to hand-edit the files.

## Born, and the age column

**Born** is written by the script and by no flag: `add` stamps today, and `migrate`
backdates from a `YYYY-MM-DD` date a **Source:** states — neither ever infers one. `list`
subtracts it into the age column and prints `?` where there is no stamp. There is
deliberately no `edit --born`: an age a session can rewrite is an age no reader can act on.

## The done-log pointer rule

`--how` points at the most durable address available — commit/PR (immutable) > wiki page or
repo doc (versioned) > memory file (prunable). The line must make sense on its own even if
the pointer dies; when the work left no artifact at all, `--note` carries the substance,
because the line IS the only record.
