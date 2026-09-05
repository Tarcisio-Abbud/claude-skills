---
name: wrap-up
description: "Session close before /compact or /clear: resolves pendings, updates memory and docs, runs tests, settles every commit/push/merge in one gate, reports on a fixed template. Arg: afk (unattended, strict merge)"
disable-model-invocation: true
argument-hint: "[afk]"
---

A **wrap-up** leaves the external state (memory + docs + tests + version control)
reflecting what this session did — a close that leaves silent pendings is not a close.
Execute the steps in order; each ends on a checkable criterion, and every skip is stated.

Two disciplines run through every step. **Resolve the pending item HERE, with the context
still warm** — a **gate** is what lets it leave the session unresolved instead: step 2's
survival gates admit an item to the queue, step 5's versioning gate admits work to version
control, and what passes neither is resolved now. And the close is a **fixed template**
(step 6, `REPORT.md` beside this file): where a response-style preference disagrees with
that structure, the template wins.

**Argument:** `afk` — the user is leaving now; see "The `afk` argument" at the end.
**Site extensions:** read `~/.claude/tk/wrap-up.md` and `.claude/tk/wrap-up.md` (project
root) if they exist — documentation targets, flow recommendations, the afk merge's repo
list. (A project's own `.claude/skills/wrap-up` overrides this skill entirely.)

## 1. Inventory the session's changes

Fire the sweep as ONE parallel batch — `git fetch`, `git status`, `git diff --stat`,
`git log --branches --not <default> --oneline` and, if `gh`/forge CLI exists, the open
PRs — and print the inventory. The fetch comes first: every other signal reads this disk
only, and a sibling session in another clone is a fact to know now, not a rejected push
at the end of the gate. Add the **facts/decisions/learnings** from the conversation, not
just code. The inventory drives the rest: no code change → step 4 skips the suite;
nothing behaviour- or knowledge-changing → step 3 shrinks to nothing; the version-control
actions feed step 5.

**Then the session findings** — term, triage ladder and unattended form:
`../../reference/session-finding.md`. The inventory carries a section of every point the
session RAISED and left unanswered; right after printing it, ONE batched
`AskUserQuestion` closes it whole — each answer can still change memory, docs or the
queue below, and a finding whose answer turns into work goes to step 2's survival gates.
**Done when:** the user saw the touched files/commits, branches/PRs and new
decisions/facts, every session finding was answered, discarded or carried to step 2 as
work, and each later step is marked run/skip.

## 2. Update memory, and gate what survives into the queue

For each durable and **non-obvious** fact from step 1, create/update ONE file in the
project's auto-memory (dir `memory/`, index `MEMORY.md`); prefer updating over
duplicating, delete what proved wrong, make relative dates absolute, link with `[[slug]]`.

**Pending items go through `tk-queue`** — contract, commands and the pointer rule:
`../../reference/queue.md`. Decide each new item's `--criterion` here rather than leaving
"done" as the next closer's self-report, and ask a DECISION's decision here: with the
user still in the room the item registers AUTONOMOUS. That queue is what `/tk:kickoff`
dispatches at the next session's open.

An item survives into the queue only when at least ONE **survival gate** holds, and the
item RECORDS which one — in its own text ("waiting on the vendor's token"), except where
a field already carries it:

| Survival gate | Holds when | The class it arrives as |
|---|---|---|
| **decision** | the item needs a human verdict that cannot be had now | `DECISION`, and `--deferred` carries it |
| **effort** | the work exceeds what is left of this session | `AUTONOMOUS`, and the text names what would not fit |
| **dependency** | a third party, a credential, or a machine that is not this one holds it | `BLOCKED` or `EXTERNAL` — or `--env <name from the site roster>` when the block is only WHERE it runs — and the text names what is awaited |

The survival gates are a disjunction: where two hold, the item records the FIRST in the
order above — a tie-break, nothing more. `--effort` is required on every `add`, so a size
alone marks nothing. An item that passes none is resolved in this session; "I will do it
later" is not one. **RECURRING is convert-or-resolve, before the gates are asked** — no
gate can justify parking it, and creating a routine is an external effect: with the user
present, offer the conversion as a check of its own (the check IS the authorization) and
close with `done --how "<the routine>"`; unattended, a DECISION carrying the routine
ready to paste. Never discarded: a discard answers a question, this one needs a routine.

**Encode into the system:** a correction the user repeated or a check they did by hand is
a system signal, not an instance signal — propose encoding it (project skill, hook rule,
test) so it holds in every future iteration.
**Done when:** every durable fact has a memory file (pointer in `MEMORY.md`), every open
item names its survival gate, no RECURRING item is parked, and every recurring correction
has an encoding proposed or discarded.

## 3. Update the repo documentation

Runs when the inventory shows changed behaviour or new knowledge. Make the documentation
reflect the current implementation: `README`, the project's instruction file
(`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`), glossary (`CONTEXT.md`), `docs/` and ADRs — no
command, count or path may stay stale. Site extensions add further targets — and this is
where conversation-only understanding gets a written address, making the `/clear` cheap.
**Done when:** every changed behaviour is reflected in every documentation target — or
nothing doc-relevant changed and that was said.

## 4. Verify

Runs when code changed. Run the project's test suite, detecting the runner from the
manifest (`pytest`, `npm test`, `cargo test`, `go test ./...`, `make test`, …); with an
end-to-end verification skill in the project and changed runtime behaviour, run it too —
a green test doesn't prove the real flow works. A session closing a queue item also owes
that item's **criterion**, re-run here on the final tree — the implementer's report is an
input to that run, never a substitute. The rite, the three attempts and the evidence
block belong to `/tk:verify` (`../verify/SKILL.md`), which writes the block ONCE; step 5
displays that block rather than re-deriving it.
**Done when:** the tests pass — or the failures are reported with the output, or the skip
was stated — and every item closed by this session carries its evidence block.

## 5. The versioning gate

Settle every version-control decision NOW — this gate is what makes the wrap-up a real
close. From the inventory, list the pending actions per repo: uncommitted work, unpushed
branches, PRs to open, PRs awaiting merge. **The gate's whole procedure is the
`merge-gate` skill, `../merge-gate/SKILL.md` — read it whenever that list is
non-empty**: the digest,
its five verdicts of safe-to-merge, the triple check of the closing line, the action
menu, stack order, and the accumulated lane's per-item form.

**What this session DELIVERED — an item it closed, carrying its evidence block — arrives
here as an action, never as a new item**. Merging its own PR is one line of the list above,
and the menu is the authorization. Reclassifying to `DECISION` belongs to an item still
open from before this session. Where the menu leaves the merge unchecked, the DECISION it
writes carries that action, and the delivered item stays closed.
**Done when:** `../merge-gate/SKILL.md`'s own "Done when" holds — every action executed or an
explicit DECISION, none merely implied — or the list was empty and that was said.
`tk-queue list` then names no item this session delivered — a deferred merge sits there as
that action, never as the item back open.

## 6. Close: the report, the handoff, and the next step

**The report follows the template in `REPORT.md` beside this file — read it before
writing the close.** It is written for a cold reader, and the structure is what travels.

**The handoff** comes at two levels. The default is the pair that already exists: the
queue item, in executable order, plus the opening sentence of the next session. Escalate
to the five-field handoff file when the understanding the next session needs lives only
in this conversation — a task mid-flight, open hypotheses, a campaign spanning several
items. That file is written and removed only by `tk-queue handoff <id> --objective "..."
--state "..." --blockers "..."`; run the `edit` it prints (rule: `../verify/SKILL.md`,
*The item points at the briefing*), and a campaign gets ONE handoff file, pointed at by
every item in it. The file carries **CONCLUSIONS, never a reading list**: this session
holds them hot; every successor pays full price to rediscover them.

**The next step — ALWAYS close by recommending ONE path**, the why in 1–2 sentences, by
where the understanding lives: written down, `/clear` is cheap; conversation-only,
document it in step 3 or write the handoff file, leaving genuine nuance to `/compact`.

- **`/clear`** — the default when the wrap-up ended clean: state 100% externalized,
  nothing mid-flight, next task discrete. **Every PR this session opened is anchored** —
  merged, or carried as a DECISION whose evidence block sits in the PR body; a PR with no
  anchor gets its DECISION on the spot. Give 1–3 ready sentences to open the next
  conversation, in the two shapes `REPORT.md`, *The opening sentences*, prescribes.
- **`/compact`** — a live thread resists being written down: a half-made negotiation,
  hypotheses still forming. Write the handoff file first and this list usually empties; a
  session reopened by a spawn has no history to compact at all.
- **`/tk:docs-audit` (before the clear)** — drift beyond the session's scope: stale
  statements this session did NOT cause, or several sessions since the last audit.
- **None (continue)** — only when the user will immediately chain a related task and the
  context is still short enough to beat a clean restart.

**Done when:** the report followed `REPORT.md`, the handoff is at the level its trigger
demands, every open PR is anchored, and the user received ONE clear recommendation with
its justification — on `/clear`, with the opening sentences.

## The `afk` argument

`/tk:wrap-up afk` — the user typed it and left; run every step without a single menu. One
exception closes the package: the batched question over its parked DECISIONs
(`../kickoff/AFK.md`), asked after the work is pushed and gating nothing.

- **Concurrent-session guard** first, in the form `../kickoff/AFK.md` defines — the claim
  on the queue's items leads, tree signals follow: another live session working this
  repo → leave the tree untouched and report it.
- Steps 1–4 and 6 run as written, every menu turning into a queue entry: each unanswered
  choice becomes a DECISION carrying `--deferred afk` — the flag for a decision nobody
  could ask, against one nobody bothered to ask. A session finding takes the three rungs
  of `../../reference/session-finding.md` instead.
- Step 5 runs on `../merge-gate/SKILL.md`, *The strict form*: commit and push before any review —
  `afk` IS that authorization — the digest in the PR body, merge only under the hardened
  verdicts; whatever is not merged enters the queue as a DECISION with its digest
  reference ready.
- The step-6 report ends with the ready pair for the user's return: `/clear` +
  `/tk:kickoff afk`.

**Done when:** the state is externalized and one of three holds — the work is committed,
pushed, and every item ended merged under the strict form or at an open PR carrying its
evidence block and digest; or the guard stopped the run with the tree untouched, and the
report says so; or there was nothing to commit. Whatever was not merged sits in the queue
as a DECISION, and no other external effect happened.
