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

While triaging, fill or refresh each item's **Effort** and **Risk** (contract below) — the
package modes (`AFK.md`) and the dispatch choice read them.

An AUTONOMOUS item that already lives as an agent-ready ticket on the tracker has its
dispatch pre-made by the site's per-ticket flow (site extensions name it). An item too big
and foggy to triage cleanly — a whole effort, not a slice — isn't forced into a class:
propose charting it first (site extensions may name a mapping flow).

**Done when:** every pending item has a class, Effort, Risk where due and, if actionable, a
recommended dispatch from the `dispatch` skill's palette (step 5).

## 4. Build the menu

Before asking, show the **full triaged agenda** — ALL items, one line each, with class — so
the user sees nothing was lost before checking (BLOCKED/EXTERNAL show up here; their detail
waits for the final report).

Then one multiSelect `AskUserQuestion` with the actionable items (AUTONOMOUS + RECURRING)
prioritized by impact/urgency, recommendation first with "(Recommended)". DECISION items
become their own questions — the options are the choices themselves, not "yes/no". Tool
limit: 4 questions × 4 options; what doesn't fit becomes a line in the final report, not an
option. BLOCKED and EXTERNAL are never options.
**Done when:** the whole agenda was shown and the user's selection is captured.

## 5. Dispatch

The menu check IS the authorization — execute in sequence, without re-confirming. The
task→mechanism matching (palette), the `/goal` recipe, the mechanism boundaries and the
`loop.md` contract live in the `dispatch` skill: read `../dispatch/SKILL.md` (relative to
this file) before the first dispatch. Dispatches that are user-native commands don't block
the flow — they enter the final report as ready-to-paste lines.
Close with: (a) what is running/scheduled, (b) BLOCKED items with what's missing from the
user, (c) EXTERNAL items with who to chase — and settle the resulting queue through
`tk-queue` (`done`/`cancel`/`edit`/`add`; contract below).
**Done when:** every checked item is running or scheduled, the report covers (b) and (c),
and `next-steps.md` reflects the post-kickoff queue.

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
tk-queue add "<action>" --class DECISION --effort "M (~30min)" \
         --criterion "A: <command that proves it> | B: user verdict" \
         [--risk "..."] [--project slug] [--source "..."]
tk-queue done <id> --how "PR #82 · [[slug]]"   [--summary "..."] [--note "..."]
tk-queue cancel <id> --why "..."               [--summary "..."] [--note "..."]
tk-queue edit <id> [--text ...] [--class ...] [--effort ...] [--risk ...] [--criterion ...] [--project slug] [--force]
tk-queue report [--since YYYY-MM-DD] [--all]   # done-log entries, grouped by project tag
tk-queue migrate                               # one-time: moves legacy [x] to the log, assigns IDs
```

`<id>` is accepted in the form the queue displays (`T006`) as well as bare (`6`).

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

Item fields (every recorded field is the writer's guess — kickoff always re-verifies and
re-triages; tracker tickets are referenced, not mirrored):

- **Class** — one of the five triage classes above.
- **Effort** — S/M/L plus a rough wall-clock estimate; the package modes use it to size a
  session.
- **Risk** — present ONLY when running the item unsupervised can do damage (production
  data, irreversible effects, anything externally visible): one line naming the damage. No
  Risk line = safe to run unattended; an item carrying a Risk line never enters an afk
  package.
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

An item is a pending action, not an essay — the script enforces a size ceiling. Durable
context goes to a memory file or wiki page, linked from the item with `[[slug]]`.

**The done-log pointer rule:** `--how` points at the most durable address available —
commit/PR (immutable) > wiki page or repo doc (versioned) > memory file (prunable). The
line must make sense on its own even if the pointer dies; when the work left no artifact
at all (conversation-only), `--note` carries the substance, because the line IS the only
record.
