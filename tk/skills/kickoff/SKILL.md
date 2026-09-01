---
name: kickoff
description: "Session opening — mirror of /tk:wrap-up: gathers the project's pending items, verifies each against reality, triages and dispatches what the user checks. Args: afk, pack (unattended package), --budget N (orchestrator generations)"
disable-model-invocation: true
---

A **kickoff** opens the session that `/tk:wrap-up` closed: it builds the **agenda** of the
project's pending items, checks what is still real, triages item by item and **dispatches**
what the user checks. Execute the steps in order; each ends on a checkable criterion.

**Arguments:** `afk` and `pack` replace steps 4–5 with the package flow — after step 3,
switch to `AFK.md` beside this file. `--budget N` (default 1) rides with either, read in `WINDOW.md`.

**Site extensions:** read `~/.claude/tk/kickoff.md` and `.claude/tk/kickoff.md` (project
root) if they exist — they add site-specific agenda sources and dispatch commands. (A
project's own `.claude/skills/kickoff` overrides this skill entirely.)

**A session opening on a package handoff takes `AFK.md` ahead of this file's step 1** — a
briefing whose `--state` names a package in flight has paid for steps 1–3 already. Enter at
*A resumed generation starts here* in `AFK.md`. A handoff reached from an item's
`[[handoff-T<id>]]` takes the same route: it is this session's agenda, and the queue waits.

## 1. Gather the agenda

**Open on a clean tree.** Run `../../bin/tk-hygiene` first — it audits every roster repo for
`delete_branch_on_merge` and prunes local branches whose remote is gone and which carry no
commit of their own; safe to run twice, and it asks nothing. Report it in one or two lines. Exit 1 (a repo reads
`delete_branch_on_merge=false`): queue an item, never a question. Exit 3: name the repo it
could not audit and carry on. Exit 2: the run did not happen — the audit is unread, not clean.

Sources, in this order: **`next-steps.md`** in the project's auto-memory — the canonical
queue (contract: `../../reference/queue.md`); absent it (first kickoff), the memory files
the index flags as having pending items. Then **open issues and PRs** (`gh issue list`,
`gh pr list`) when there is a tracker, then the site extensions' sources. Wiki and repo
docs are NOT agenda sources — a pending item found there is stale doc, not queue.

**Open with what left the queue this week:** `tk-queue report --since <today minus 7 days>`
(`../../bin/tk-queue`; a literal `YYYY-MM-DD`), shown as a short block — context, not
agenda: it catches an item about to be re-opened by mistake. A single-project session
leaves `--all` off; the sweep is for a session opened over several projects, paid against
the planning threshold (`WINDOW.md`, *The two planning seams*). No lines → the week was quiet, one line.

**Done when:** the hygiene result is in the report, and the user saw the week's closed items
with a single list of candidate items, each with its source — or a package handoff was found
here, and its contents are the agenda.

## 2. Verify against reality

Memory reflects the moment it was written. Before any item enters the agenda, check the
current state (`gh pr list`, `gh issue view`, `git log`, read the code). An
already-resolved item leaves via `tk-queue done "<id>" --how "<what resolved it>"` ON THE
SPOT, and the memory citing it is fixed in the same breath.
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

While triaging, fill or refresh each item's **Effort**, **Risk** and **Env** — the package
modes (`AFK.md`) and the dispatch choice read them. Env names the machine that can execute
the item (absent = this one); an item half here and half elsewhere is SLICED, one item per
machine. A refused `--env` value is actionable output — read it to the user.

**Ask before writing BLOCKED — the user is in the room.** Ask whether they can supply the
missing thing NOW: supplied → AUTONOMOUS, the answer in its text and `--criterion`; still
missing → BLOCKED stands as an exception someone tested. A DECISION takes the same move
one step earlier: ask the choice, and the item leaves triage AUTONOMOUS. An item too big
and foggy to triage is not forced into a class — propose charting it first.

**Done when:** every item has a class, Effort, Risk and Env where due, every mixed item is
sliced, every BLOCKED and DECISION was asked out loud, and each actionable item carries a
recommended dispatch from the palette (step 5).

## 4. Build the menu

Before asking, show the **full triaged agenda** — ALL items, one line each, with class — so
the user sees nothing was lost before checking. **Brief each DECISION first, in prose**,
two to four lines from what the item already carries — its text, its `**Criterion:**`, the
memory file behind a `[[slug]]` at ONE hop, its handoff. Retransmission, not synthesis:
context in none of those is a **missing handoff**, and the briefing says exactly that.

Then one multiSelect `AskUserQuestion` with the actionable items (AUTONOMOUS + RECURRING)
in the queue's own order — that order IS the priority — recommendation first. DECISION
items become their own questions, the options the choices themselves. Tool limit: 4
questions × 4 options; the overflow becomes report lines. BLOCKED, EXTERNAL and items
bound to another environment ("runs on: X", from **Env** — read off the item itself, since
`tk-queue list` does not print it) are never options — the last go
to block (d), though their DECISIONs stay in the menu: deciding is machine-agnostic.
**Done when:** the whole agenda was shown, every DECISION was briefed before its question,
and the user's selection is captured.

## 5. Dispatch

The menu check IS the authorization — execute in sequence, without re-confirming; read the
palette in `../dispatch/SKILL.md` before the first dispatch, and `../dispatch/LOOP.md` for
the `loop.md` contract. Each run carries the contract block from `../../bin/tk-contract
--role <row>`. When its item names a ticket, it also carries the closing line from
`../../bin/tk-ticket-ref <id> --closing-line`, composed there and never here; exit 3 says
the item names none, and the run is dispatched saying so. Close with: (a) what is
running/scheduled, (b) BLOCKED items and what is missing, (c) EXTERNAL items and who to
chase, (d) items bound to ANOTHER environment, each "runs on: X" with its ready-to-paste
line — nothing here can run those, so the user is the only path, (e) the **session
findings** discarded here, one line each — the only trace a discard leaves — and (f) the
**age** of the items left standing: the oldest get one line each naming what they wait
for, the cut read off `list`'s own distribution and named in the report. Age is shown,
never asked; name a DECISION's written deferral beside its age — work the user parked on purpose.
**Done when:** every checked item is running or scheduled, the report covers (b)–(f), and
`next-steps.md` reflects the post-kickoff queue.

## A session finding, and the queue

Session findings — definition, the hydra, the ladder, the unattended form — live in
`../../reference/session-finding.md`; triage each at the moment of discovery, discards
feeding block (e). The queue contract and gotchas: `../../reference/queue.md`; commands
and flags: `tk-queue --help` and each subcommand's own `--help`.
