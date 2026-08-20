---
name: kickoff
description: "Session opening — mirror of /tk:wrap-up: gathers the project's pending items, verifies each against reality, triages and dispatches what the user checks. Args: afk (auto-dispatch, zero menus), pack (same package, one confirmation)"
disable-model-invocation: true
---

A **kickoff** opens the session that `/tk:wrap-up` closed: it builds the **agenda** of the
project's pending items, checks what is still real, triages item by item and **dispatches**
what the user checks. Execute the steps in order; each ends on a checkable criterion.

**Arguments:** `afk` and `pack` replace steps 4–5 with the autonomous package flow — after
step 3, switch to `AFK.md` in this skill's folder.

**Site extensions:** read `~/.claude/tk/kickoff.md` and `.claude/tk/kickoff.md` (project
root) if they exist — they add site-specific agenda sources and dispatch commands. (A
project's own `.claude/skills/kickoff` overrides this skill entirely.)

## 1. Gather the agenda

Sources, in this order:

- **`next-steps.md`** in the project's auto-memory (dir `memory/`; the `MEMORY.md` index is
  already in context) — the canonical queue, contract at the end of this file. If it doesn't
  exist yet (project's first kickoff), fall back to the memory files the index flags as
  having pending/NEXT/waiting/idea items.
- **Open issues and PRs** on the repo (`gh issue list`, `gh pr list`), when there's a
  tracker.
- Any additional sources the site extensions name.

Wiki and repo docs are NOT agenda sources — volatile state doesn't live there; a pending
item found there is stale doc, not queue.

**Open with what left the queue this week.** Before the agenda itself, run
`tk-queue report --since <today minus 7 days>` (`../../bin/tk-queue`; the date is a literal
`YYYY-MM-DD`) and show its lines as a short **"saiu da fila esta semana"** block. It is
context, not agenda: it says what moved while the user was away and catches an item about to
be re-opened by mistake. The report prints one `### <project>` heading per memory dir — add
`--all` to sweep every project's log, which is how a session opening on one project still
sees the week whole. No lines in the window → say the week was quiet, in one line, and move
on.

**Done when:** the user saw the week's closed items (or the quiet week stated), and there is
a single list of candidate items, each with its source.

## 2. Verify against reality

Memory reflects the moment it was written. Before any item enters the agenda, check the
current state: is the PR still open? did a commit/merge already resolve it? did the issue
close? does the cited file/flag/script still exist? (`gh pr list`, `gh issue view`,
`git log`, read the code). An already-resolved item leaves the agenda via
`tk-queue done <id> --how "<what resolved it>"` ON THE SPOT — don't leave it for the next
wrap-up — and the memory citing it is fixed in the same breath.
**Done when:** every remaining item is confirmed genuinely open and no known-stale memory is
left uncorrected.

## 3. Triage

Each item gets exactly ONE class:

| Class | Criterion |
|---|---|
| **AUTONOMOUS** | well-specified; an agent executes it without the user |
| **DECISION** | missing a user choice; once decided, becomes AUTONOMOUS |
| **BLOCKED** | depends on data/action/credentials only the user has |
| **EXTERNAL** | waiting on a third party; at most chase/remind |
| **RECURRING** | not a one-off item — should become a scheduled routine |

While triaging, fill or refresh each item's **Effort**, **Risk** and **Env** (contract
below) — the package modes (`AFK.md`) and the dispatch choice read them.

**Env is filled here, and a mixed item is sliced here.** Env names the machine that can
execute the item, and absent means this one (field contract below) — so triage writes it
only in the exception, and clears it with `tk-queue edit <id> --env none` the moment it
stops being true. An item half here and half elsewhere has no honest single value: slice it
before it gets a class, one item per machine — `tk-queue edit <id> --text "<the half that
runs here>"` plus `tk-queue add "<the other half>" --env <machine>`. A refused value is
actionable output, not a wall: it names the roster it was matched against, and when no site
file exists at all it names the file to create and its format. Read that refusal to the
user rather than re-deriving what it already says.

**Ask before writing BLOCKED — the user is in the room.** BLOCKED means only the user can
supply what is missing, and with them present that supply is one question away: ask whether
they can give the data, the credential or the action NOW. Supplied → the item is
AUTONOMOUS, carrying the answer in its text and `--criterion`. Still missing → BLOCKED
stands as an exception someone tested, not a default nobody questioned. A DECISION takes
the same move one step earlier: ask the choice, and the item leaves triage AUTONOMOUS.

An AUTONOMOUS item that already lives as an agent-ready ticket on the tracker has its
dispatch pre-made by the site's per-ticket flow (site extensions name it). An item too big
and foggy to triage cleanly — a whole effort, not a slice — isn't forced into a class:
propose charting it first (site extensions may name a mapping flow).

**Done when:** every pending item has a class, Effort, Risk and Env where due, every
mixed item is sliced, every BLOCKED and DECISION was asked out loud before its class was
written, and, if actionable, each item carries a recommended dispatch from the `dispatch`
skill's palette (step 5).

## 4. Build the menu

Before asking, show the **full triaged agenda** — ALL items, one line each, with class — so
the user sees nothing was lost before checking (BLOCKED/EXTERNAL show up here; their detail
waits for the final report).

**Brief each DECISION before asking it, in prose.** Two to four lines per item: what it
is, where it came from, what is already decided — so the user answers a question they
recognise instead of a hypertechnical one. The briefing is **retransmission, not
synthesis**: its lines come from what the item already carries — its text, its
`**Criterion:**`, the memory file behind a `[[slug]]` at ONE hop, and `handoff-T<id>.md`
beside the queue files when it exists. Searching wiki, git or code to fill a gap is the
move to avoid: context that is in neither the item nor its handoff is a **missing
handoff**, and the briefing says exactly that in its own line, because a gap named is
cheap and a gap papered over with plausible synthesis is a decision taken on invented
ground. Anything the session inferred rather than read is marked as inference right in the
line that carries it.

Then one multiSelect `AskUserQuestion` with the actionable items (AUTONOMOUS + RECURRING)
in the queue's own order — that order IS the priority, and `tk-queue bump <id>` is what
changes it — recommendation first with "(Recommended)". DECISION items
become their own questions — the options are the choices themselves, not "yes/no". Tool
limit: 4 questions × 4 options; what doesn't fit becomes a line in the final report, not an
option. BLOCKED and EXTERNAL are never options.

**An item bound to another environment is not an option either.** Its agenda line carries
the marker "runs on: X" — derived from the item's **Env** field, read off the item itself
since `tk-queue list` does not print it — and nothing here can execute it, so it leaves the
menu and enters block (d) of the report (step 5). **Its DECISION stays in the menu:**
deciding is machine-agnostic, only the execution waits for the machine, so an item that is
both DECISION and bound elsewhere appears twice on purpose — as a question here, and as a
line in (d), now decided and ready to run there. Dropping it from the menu is how a choice
the user could have made in one keystroke ends up waiting for a trip to another machine.
**Done when:** the whole agenda was shown, every DECISION was briefed before its question,
and the user's selection is captured.

## 5. Dispatch

The menu check IS the authorization — execute in sequence, without re-confirming. The
task→mechanism matching (palette), the `/goal` recipe, the mechanism boundaries and the
`loop.md` contract live in the `dispatch` skill: read `../dispatch/SKILL.md` (relative to
this file) before the first dispatch. Dispatches that are user-native commands don't block
the flow — they enter the final report as ready-to-paste lines.
Close with: (a) what is running/scheduled, (b) BLOCKED items with what's missing from the
user, (c) EXTERNAL items with who to chase, (d) items bound to ANOTHER environment, each
marked "runs on: X" and carrying its ready-to-paste line where one fits, and (e) the
findings discarded in this session — "discarded: N" plus one line each. (d) is not a
variant of (b): nothing on this machine can run those items, so the user is the only path
to the machine that can. (e) is the only trace a discard leaves, which is what keeps
"discarded" from becoming the silent outcome — settle the rest of the queue through
`tk-queue` (`done`/`cancel`/`edit`/`add`; contract below).
**Done when:** every checked item is running or scheduled, the report covers (b) through
(e), and `next-steps.md` reflects the post-kickoff queue.

## A finding during the session

A **finding** is work this session discovered and did not come for. What tells it from a
**pendency** is the criterion of the item in hand: work that item's `**Criterion:**` needs
in order to pass is a pendency, and it is resolved in the session. Everything else is a
finding, and a finding never inherits that default — that inheritance IS the hydra: three
heads die and six items are born, which is how a quick job became three weeks.

Every finding is triaged at the moment of discovery, and with the user present the triage
is a menu (`AskUserQuestion`, which waits for them — a question in prose scrolls away in
the terminal's wall of text). Three outcomes, and the **recommended** one is the first that
holds, read in order:

1. **Resolve now** — leaving it breaks something already delivered: a live defect in what
   this session just shipped, data the user will read as correct, a command they will type
   as written.
2. **Queue with a gate** — someone will act on it later and it has a gate to name: human
   decision · effort · external dependency. `tk-queue add` on the spot, gate in the item.
3. **Discard** — neither of the above holds. Nothing is written: the finding's whole trace
   is its line in block (e) of the report. A discard that deserved more than one line was
   not a discard.

The ladder recommends and the user picks; their pick IS the authorization, including for a
resolve-now the ladder had placed third. Unattended, this menu has no one to answer it, and
neither the discard nor the resolve-now is a session's call to take without the user — read
`AFK.md` before acting on a finding there.

## The queue contract: `next-steps.md` + `done-log.md`, written only by `tk-queue`

Single source for a project's queue of pending items. Two sibling files in the project's
auto-memory (`~/.claude/projects/<cwd-slug>/memory/`, each with a pointer in `MEMORY.md`):

- **`next-steps.md`** — OPEN items only, the queue this skill dispatches.
- **`done-log.md`** — what left the queue (FEITO or DESCARTADO), when, and how. Feeds
  progress reports; consult it when a queue item touches ground already worked.

Both are written ONLY through the deterministic script **`tk-queue`**
(`../../bin/tk-queue` relative to this file) — never by hand-editing. The script is what
guarantees a resolved item actually LEAVES the queue: `done`/`cancel` move it to the log
in one command (log written first, so a crash between the two writes can duplicate a line
but never lose the item), and finished work cannot silently accumulate as `[x]` lines
again (25 of them had, before 2026-08-03). Any session where an item is born or dies
calls the script on the spot — `/tk:wrap-up` guarantees it at close; `/tk:kickoff`
verifies the queue at open.

```
tk-queue list                                  # open items with IDs (T001…)
tk-queue add "<action>" --class AUTONOMOUS --effort "M (~30min)" \
         --criterion "A: <command that proves it> | B: user verdict" \
         [--deferred "<why the decision could not be asked>"]   # REQUIRED by --class DECISION
         [--risk "..."|none] [--env <name from the site roster>|none] [--project slug] [--source "..."]
tk-queue done <id> --how "PR #82 · [[slug]]"   [--summary "..."] [--note "..."] [--force]
tk-queue cancel <id> --why "..."               [--summary "..."] [--note "..."] [--force]
tk-queue edit <id> [--text ...] [--class ...] [--effort ...] [--risk ...|none] [--env ...|none] [--criterion ...] [--deferred ...] [--project slug] [--force]
tk-queue bump <id>                             # move the item to the top of the global order
tk-queue claim <id> --as <session/host label>  # take it, so a sibling session does not work it too
tk-queue release <id>                          # hand a claimed item back, WITHOUT closing it
tk-queue handoff <id> --objective "..." --state "..." --blockers "..." \
         [--skills "..."] [--pitfalls "..."]   # the item's full briefing, in handoff-T<id>.md
                                               # beside next-steps.md; DELETED when the item
                                               # is closed (`tk-queue handoff --help`)
tk-queue pack                                  # candidates for an unattended package:
                                               # eligible items in queue order, plus every
                                               # exclusion with the value that caused it
tk-queue report [--since YYYY-MM-DD] [--all]   # done-log entries grouped by project tag; --all sweeps every project
tk-queue migrate                               # one-time: moves legacy [x] to the log, assigns IDs
```

`<id>` is accepted in the form the queue displays (`T006`) as well as bare (`6`).

**Priority is the ORDER of the file, global** — no score, no hidden heuristic. `add` puts a
new item at the end; `bump <id>` moves one to the top; the package modes take the top of
what `tk-queue pack` reports as eligible. Re-prioritising means bumping, in that order (the last bump wins the top). The `##`
headings a real queue carries are cosmetic: `list` groups by the **Project:** field, so a
bumped item landing under a foreign heading changes nothing a reader acts on.

**Who is working on an item** — `claim <id> --as <name>` marks it under the exclusive
lock the queue already has, and a second `claim` is REFUSED naming the owner and the
moment: that is how two sibling sessions on one queue stop executing the same item
(collisions measured 2026-08-18). `list` shows the mark. `done`/`cancel` take it with the
item, and `release <id>` hands the item back to the queue without closing it. Release does
NOT demand the owner's name — a session that died holding a claim would otherwise leave
the item unreachable by anyone — so it prints WHOSE claim it dropped, which is what keeps
a wrongful release visible. There is deliberately no `edit --claimed`: a flag that could
write the field would take a held item in a second command, which is what `claim` refuses
in one.

**Which IDs are taken** — the script counts an ID as allocated only where a WRITER puts
one: at an item's marker in either file (`- [ ] **T007** — …`) and in a done-log entry's
ID column (`- 2026-08-13 — FEITO — T072 …`). A T-number anywhere else is PROSE — a note,
a summary, an item citing a sibling ticket from another tracker — and burns no number.
Two tolerances at the marker, both one-way (they can only make MORE IDs count as taken):

- **Decoration before the ID counts; a word does not.** `- [x] ✅ **T020** — …` and
  `- [x] ~~**T012**~~ — …` are allocations, and so is `**~~T012~~**`; a strikethrough or
  an emoji is how a human ticks off or flags a legacy item. `- [x] feito junto com o
  **T900** do outro tracker` is not — one word before the ID and the line is prose.
- **The checkbox is not read.** An ID sits at a marker whether the box is `[ ]` or `[x]`,
  in next-steps.md or in done-log.md alike. A `- [ ] **T005**` line parked in the log is
  still spent: refusing to see it is the direction that hands the number out twice.

Both matter to a session because they decide what `add` hands out next and what the
"never allocated" diagnostic means. Neither is a licence to hand-edit the files.

Every mutating command (`add`/`edit`/`done`/`cancel`/`migrate`) prints the memory dir it
resolved on **stderr** before acting. That target is inferred — from `--dir`, or from the
cwd when it is absent — and a shell that keeps its cwd between calls has already made an
`edit` land on a homonymous item in ANOTHER project's queue while reporting success. Read
that line before trusting the result.

Two writers at once are safe: every mutating command holds an exclusive lock on the
memory dir for its whole read-modify-write. When an ID is not among the open items the
script says WHY — already in the done-log, still ticked `[x]`, never allocated, or
allocated and since removed by another writer. None of those mean "invent it again":
re-read with `tk-queue list` instead of adding a replacement, which is how a queue grows
duplicates.

Free text may not contain a bold field marker (`**Project:**`, `**Risk:**`, …) — it would
be read as the real field and silently hijack it, so `add`/`edit`/`done`/`cancel` refuse
it and ask for a rephrase. Naming a field in plain prose is fine; only the bold-plus-colon
shape is refused.

Items written **before** that guard can still carry the shape, so `edit` locates the field
it is changing by the item's **field chain** — the run of `**Field:** value.` segments that
ends the item's first line — never by "the last marker in the block", which reaches into
continuation lines. When the chain is ambiguous (a marker only outside it, or the same
field twice inside it) `edit` **refuses and says so** instead of guessing: a refusal costs
one command, and `--risk none` guessing wrong deletes prose that cannot be recovered.
The fix for such an item is `cancel` + `add`.

Item fields (every recorded field is the writer's guess — kickoff always re-verifies and
re-triages; tracker tickets are referenced, not mirrored):

- **Class** — one of the five triage classes above.
- **Deferred** — the justification `--deferred` demands whenever an item BECOMES a DECISION,
  on `add` and on `edit` alike (`add AUTONOMOUS` + `edit --class DECISION` would otherwise
  reach in two commands what one refuses). A DECISION parks the queue until the user is
  back, so ask the decision NOW and write it into the item's text and `--criterion` — the
  item is then AUTONOMOUS and an afk session can run it. That is the default path; deferring
  is the exception, and an unattended session that cannot ask passes `--deferred afk`. The
  field is dropped by LEAVING the class (`edit <id> --class AUTONOMOUS` takes it along and
  says so), never by `--risk`-style clearing: a DECISION with no deferral on the record is
  the one state the gate exists to forbid.
- **Effort** — S/M/L plus a rough wall-clock estimate; the package modes use it to size a
  session.
- **Risk** — present ONLY when running the item unsupervised can do damage (production
  data, irreversible effects, anything externally visible): one line naming the damage. No
  Risk line = safe to run unattended; an item carrying a Risk line never enters an afk
  package. **`--risk none` DELETES the field** (on `add`, writes none in the first place):
  a Risk recorded when it was true goes stale — the branch it names gets merged, the
  migration it fears already ran — and a stale Risk keeps the item out of every afk package
  forever. `--risk ''` cannot do that job: it is indistinguishable from "flag not passed",
  so it is a silent no-op. Re-triaging a Risk means clearing it, not rewording it.
- **Env** — WHERE the item runs, when that is not "here". Orthogonal to the class: the
  class says what the item is waiting for, Env says which machine can execute it. Absent =
  the machine that owns this queue (queues are per machine and do not sync, so that is the
  natural default and the field appears only in the exception). One environment per item —
  an item that is half here and half elsewhere is SLICED in triage, one item per machine.
  The value is validated by exact equality against the roster in the **site file**
  (`~/.claude/tk/env`), and a value outside it is refused, never warned: an environment
  nothing validated is a phantom one — an item no machine ever picks up, with no error to
  say why. No site file, no `--env`: the flag is refused with the file to create, since the
  plugin ships no machine name of its own (same design as git's `user.name`). That file also
  carries this machine's identity and its two subagent ceilings, local and cloud; its format
  is documented in `bin/tk_site.py`. **`--env none` DELETES the field** (on `add`, writes
  none in the first place) — the stale-Risk failure again: an item pinned to a machine it
  needed before it was re-sliced would sit out every package here forever.
- **Criterion** — acceptance criterion, required on `add` (and it must not be blank): `A:`
  a deterministic check (a command whose pass proves the item done) or `B:` the user's
  verdict. `edit` keeps it optional, because items created before the field was mandatory
  still have to be editable without one being invented for them.
- **Project** — optional short lowercase slug (letters, digits, `-`/`_`) tagging which
  project the item belongs to, for a workspace-root queue that mixes several projects'
  items in one file. Anything outside that shape (`.ambiente`, `Casa Nostra`) is rejected
  outright, not warned about. Within it, `add` warns on stderr — not an error, the item
  still enters — when the tag matches no currently-open item's tag, naming the tags already
  in use, so a near-miss (`ambiente` × `anbiente`, `tk` × `tooling`) surfaces before it
  splinters the grouping. `tk-queue list` groups items by this tag once any item carries one
  (untagged items land in a final "no project" group); with no tagged items at all, `list`
  is unchanged from the flat format. There is no `list --project X` filter and no
  per-project file — a single project-scoped queue simply never sets the tag. The tag
  follows the item into the done-log when it is closed, and `report` groups by it under
  `####` headers (untagged last, same convention) — that grouping is what makes the weekly
  closed-items block legible in a root queue that mixes projects. `###` remains the memory
  dir, a different axis: one per project repo, `####` the tags within it.

An item is a pending action, not an essay — the script enforces **two** size ceilings, and
durable context goes to a memory file or wiki page, linked from the item with `[[slug]]`:

- **the block ceiling**, on the whole item. `add` always. `edit` whenever a **prose** flag
  is used — `--text`, `--criterion`, `--risk`, `--deferred` — and the edit grows the item.
- **the field ceiling**, on each field VALUE, on `add`, `edit` and the closes
  (`--how`/`--why`/`--summary`/`--note`) alike. It comes in two sizes: a small one for the
  fields that are short by construction (`--class` an enum, `--effort` "M (~30min)",
  `--project` a slug) and a larger one for prose.

The **short** fields are the only ones exempt from the block ceiling, and that exemption is
deliberate: gating them meant a legacy oversized item needed `--force` merely to gain a
project tag, which trains the caller to type `--force` on edits and disarms the guard where
it matters. It is safe only because those fields are small AND replaced rather than
appended, so repeated edits cannot accumulate.

Neither ceiling holds alone, and both gaps were measured, not imagined: with only the block
ceiling, one field edit was exempt and `--criterion` took a 100-char item to **1014** chars;
with only the field ceiling, three prose fields at 199 chars **in a single call** took an
item to **709**, past a 700 ceiling, with no `--force`.

`--force` raises both, for the rare exception.

**The done-log pointer rule:** `--how` points at the most durable address available —
commit/PR (immutable) > wiki page or repo doc (versioned) > memory file (prunable). The
line must make sense on its own even if the pointer dies; when the work left no artifact
at all (conversation-only), `--note` carries the substance, because the line IS the only
record.
