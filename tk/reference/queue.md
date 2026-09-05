# The queue contract: `next-steps.md` + `done-log.md`, written only by `tk-queue`

Single source for a project's queue of pending items. Two sibling files in the project's
auto-memory (`~/.claude/projects/<cwd-slug>/memory/`, each with a pointer in `MEMORY.md`):

- **`next-steps.md`** — OPEN items only, the queue `/tk:kickoff` dispatches.
- **`done-log.md`** — what left the queue (FEITO or DESCARTADO), when, and how. Feeds
  progress reports; consult it when a queue item touches ground already worked.

Both are written ONLY through the deterministic script **`tk-queue`** (`../bin/tk-queue`
relative to this file) — never by hand-editing. The script is what guarantees a resolved
item actually LEAVES the queue: `done`/`cancel` move it to the log in one command, log
written first, so a crash between the two writes can duplicate a line but never lose the
item. Any session where an item is born or dies calls the script on the spot.

**The commands, the flags and each field's shape live in `tk-queue --help` and the
subcommands' own `--help`** — this file carries only what those helps do not confess.
`<id>` is accepted as displayed (`T006`) or bare (`6`).

## Priority, claims and two writers

**Priority is the ORDER of the file, global** — no score, no hidden heuristic. `add`
appends; `bump "<id>"` moves one to the top, and the last bump wins it; the package modes
take the top of what `tk-queue pack` reports eligible. A real queue's `##` headings are
cosmetic: `list` groups by the **Project:** field, so an item under a foreign heading
changes nothing a reader acts on.

A second `claim` is REFUSED naming the owner and the moment — that refusal is how two
sibling sessions on one queue stop executing the same item. `release "<id>"` deliberately
does NOT demand the owner's name (a dead session would leave the item unreachable), so it
prints WHOSE claim it dropped, which keeps a wrongful release visible. There is
deliberately no `edit --claimed`: a flag that could write the field would take a held item
in a second command, which is what `claim` refuses in one. `done` on an item claimed by
ANOTHER owner succeeds silently — a caller who cares asks `list` for the claim first.

Two writers at once are safe: every mutating command holds an exclusive lock on the memory
dir for its whole read-modify-write, `migrate --dry-run` included. When an id is not among
the open items the script says WHY — already in the done-log, still ticked `[x]`, never
allocated, or removed by another writer. None of those mean "invent it again": re-read with
`tk-queue list` instead of adding a replacement, which is how a queue grows duplicates.

## The stderr lines

Every mutating command prints the memory dir it resolved on **stderr** before acting —
`migrate --dry-run` too. That target is inferred from `--dir` or the cwd, and a shell that
keeps its cwd between calls has already made an `edit` land on a homonymous item in ANOTHER
project's queue while reporting success. Read that line before trusting the result.

**The preview's report is not evidence that the migration happened.** `migrate --dry-run`
prints a report byte-identical to a real run's — past tense and all — and the
discriminator, the `--dry-run` banner, is on **stderr**: a caller that captures only stdout
cannot tell a preview from a completed rewrite.

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
alone: with only the block ceiling, one exempt field edit took a 100-char item to 1014
chars; with only the field ceiling, three prose fields in one call took an item past a 700
block ceiling with no `--force`. `--force` raises both, for the rare exception.

## The WIP cap

A third ceiling bounds the QUEUE, not an item: `add` is refused once the open items reach
`max-open-items` in the site file, counted across every queue on this machine's roster.
Summing the roster stops `--dir` naming another queue to get past it; unset means NO cap, the
number being the user's. No bypass, `--force` included: an unattended one is a string no gate
can judge. Room is made by taking an item out, `done` or `cancel`, and the refusal names both,
counting this queue apart from the rest, which it never names. Still open at the cap:
`edit --text` on an item that exists, and `handoff`.

## The field chain

Free text may not contain a bold field marker (`**Project:**`, `**Risk:**`, …) — it would
be read as the real field and silently hijack it, so the mutating commands refuse it and
ask for a rephrase; naming a field in plain prose is fine. Items written before that guard
can still carry the shape, so `edit` locates the field it is changing by the item's **field
chain** — the run of `**Field:** value.` segments ending the item's first line — never by
"the last marker in the block". When the chain is ambiguous (a marker only outside it, or
one field twice inside it) `edit` REFUSES and says so instead of guessing: a refusal costs
one command, and `--risk none` guessing wrong deletes prose that cannot be recovered. The
fix for such an item is `cancel` + `add`.

`edit --class` is the one writer that positions itself against the chain instead of
reading it: the anchor goes AHEAD of any run already ending the item's first line,
because a class written after that run leaves every field in it unreadable to every
gate and every report, silently and for good. Where such a run exists the command
NAMES it on stderr — the anchor makes those segments fields, and prose merely wearing
a marker is promoted with the rest.

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
backdates from a `YYYY-MM-DD` date a **Source:** states — neither ever infers one, since an
item stamped with the wrong year reports an age nobody can tell from a right one. `list`
subtracts it into the age column and prints `?` where there is no stamp. There is
deliberately no `edit --born`: an age a session can rewrite is an age no reader can act on.

## The done-log pointer rule

`--how` points at the most durable address available — commit/PR (immutable) > wiki page or
repo doc (versioned) > memory file (prunable). The line must make sense on its own even if
the pointer dies; when the work left no artifact at all, `--note` carries the substance,
because the line IS the only record.
