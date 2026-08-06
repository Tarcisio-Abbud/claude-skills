---
name: kickoff
compatibility: "Designed for Claude Cowork. In Claude Code the `tk` plugin's own kickoff covers this instead: there the queue is a different file, owned by a script rather than written by hand."
description: "Kickoff — open a Claude Cowork session from the project's queue: verify, triage, dispatch. Use when a session opens without a defined task, the user asks what is pending in this project, wants to pick up where the last session stopped, or when another skill needs the agenda built. Arg: afk (runs the autonomous items alone). COWORK ONLY — in Claude Code this is the wrong skill: there the queue is a different file, written by a script rather than by hand, and the `tk` plugin's own kickoff dispatches it. Do not fire this skill in a session that has a repository."
---

A **kickoff** opens the session that `wrap-up` closed: it builds the **agenda** from the
project's queue, checks what is still real, triages item by item and dispatches what the
user picks. Execute the steps in order; each ends on a checkable criterion.

**Argument:** `afk` — the session runs alone; see the last section.

**Wrong surface?** One plugin list can serve both Claude Cowork and Claude Code, so this
skill can load where it does not belong. Before step 1: a version-controlled repository in
the working folder, or a sibling `tk` kickoff reachable as a command, means this is a Claude
Code session — **stop here**, say which skill covers it, and let the user fire that one.
Its queue is a different file, and hand-writing this one's format over it corrupts the
queue a script owns.

**The queue** is `next-steps.md` at the project folder's root. Read `CONTRACT.md` — beside
this file, or at the plugin root (`${CLAUDE_PLUGIN_ROOT}/CONTRACT.md`) when this skill ships
inside the `tk-cowork` plugin. The classes, the fields and the legacy-file rule live there. No queue and no
legacy file → report that the project has none yet and offer to start one from the
project's own documents.

## 1. Gather the agenda

Sources, in order: the queue; then, when it is empty or clearly stale, the project's own
documents — an open decision log, a file marked draft, a section written as a to-do; then
whatever the user names at the open.
**Done when:** there is one list of candidate items, each carrying its source.

## 2. Verify against reality

The queue reflects the moment it was written. Before an item enters the agenda, check the
current state: does the file it cites still exist, and does it already contain what the
item asks for? Was the email already answered, the document already shared, the decision
already taken in a later conversation? A resolved item leaves the queue **on the spot**, per
the contract — the next wrap-up is too late.

An item you cannot check is reported as unverified, with the fact that would settle it.
**Done when:** every item on the agenda was checked against the current state of the folder
and the ones already resolved are in `## Concluídos`.

## 3. Triage

Give each item exactly one class from the contract, and write the class back to the file
when it changed. Refresh **Effort** too — it is what makes the dispatch honest about how
much fits in this session.
**Done when:** every agenda item carries a class and an effort in the file.

## 4. Present and dispatch

Ask ONE multi-select question with the agenda, **recommended first**: the item that unblocks
the most, or the one whose criterion is closest. Give each option its class and effort in a
few words, so the user picks knowing the size.

Execute what was checked, one item at a time, finishing each before opening the next. An
item that turns out bigger than its Effort said gets reported as such and its Effort
corrected in the file.

Handing an item to a subagent is allowed; handing it the queue is not. Under the contract's
**one writer** rule, subagents execute and report back — you verify each result against the
thing itself, not against the report, and then make **one** pass over the queue and the
project's shared documents knowing every outcome. Confirm that pass per the contract.

A `DECISION` item is dispatched by asking the decision itself. Irreversible actions — send,
share, schedule, post — happen only on an explicit go-ahead in this session, the same rule
the wrap-up gate applies.
**Done when:** every checked item was executed or has its blocker named, and the queue
reflects what happened.

## 5. Hand over to the work

State what is now in flight and what stayed in the queue. From here the session is ordinary
work; `wrap-up` closes it.
**Done when:** the user knows what is being worked on and what was deliberately left.

## The `afk` argument

`afk` — no questions. Skip the step-4 menu and execute **only** `AUTONOMOUS` items, in
effort order (`P` before `M`, leaving `G` for a supervised session), under the same hard
ceiling as the wrap-up: **every irreversible action becomes a `DECISION` item** instead of
happening. `DECISION`, `BLOCKED` and `EXTERNAL` items stay untouched and are listed in the
closing report.

Finish by running `wrap-up afk`, so the session closes with the queue written.
**Done when:** the autonomous items were executed or reported as blocked, the queue is up to
date, and the project folder is the only thing the session touched.
