---
name: wrap-up
description: "Session close before /compact or /clear: kills the session's pendings, updates memory and docs, runs the tests, settles every commit/push/merge decision in one gate and reports on a fixed template. Arg: afk (no menus, strict merge)"
disable-model-invocation: true
---

A **wrap-up** leaves the external state (memory + docs + tests + version control)
reflecting what this session did, so /compact loses nothing and the next session starts
aligned — a close that leaves silent pendings is not a close. Execute the steps in order;
each ends on a checkable criterion. The step-1 inventory decides how much of steps 3–4
runs; every skip is stated, never silent.

Two disciplines run through every step. **The default is to resolve the pending item HERE,
with the context still warm** — the queue takes only what passes a survival gate in
step 2. And the close is a **fixed template** (step 6): where a response-style preference
disagrees with that structure, the template wins.

**Argument:** `afk` — the user is leaving now; see "The `afk` argument" at the end.

**Site extensions:** read `~/.claude/tk/wrap-up.md` and `.claude/tk/wrap-up.md` (project
root) if they exist — they add site-specific documentation targets, flow recommendations
and, where the site has one, the repo list the afk merge reads. (A project's own
`.claude/skills/wrap-up` overrides this skill entirely.)

## 1. Inventory the session's changes

Fire the sweep as ONE parallel batch — `git fetch`, `git status`, `git diff --stat`,
`git log --branches --not <default> --oneline` (commits still outside the default branch)
and, if `gh`/forge CLI exists, the open PRs — and print the inventory before going deeper.
The fetch comes first because every other signal here reads this disk only: a session
working from another clone leaves no local trace at all, and without it the divergence
surfaces as a rejected push at the end of the gate instead of a known fact at the start.
Add the **facts/decisions/learnings** from the conversation (not just code — user choices,
discoveries, external pending items). The inventory drives the rest: no code change →
step 4 skips the suite; nothing behaviour- or knowledge-changing → step 3 shrinks to
nothing; the version-control actions found here feed the step-5 gate.

**Then the session findings.** The inventory carries a section of its own: every point the
session RAISED and left unanswered — a question the user asked back, an option weighed and
not chosen, a defect noticed in passing. **Session finding** is the term, qualified because
a bare "finding" is a code-review finding throughout this repo. Right after printing the
section, ONE batched `AskUserQuestion` closes it whole, since each answer can still change
memory, docs or the queue in the steps below. A finding leaves this menu answered or
discarded; one the answer turns into work travels to step 2, which is where the survival
gates decide whether it may enter the queue at all.
**Done when:** the user saw a concrete list of touched files/commits, of the branches/PRs
in play, and of the new decisions/facts — with nothing material omitted — every session
finding was answered, discarded, or carried to step 2 as work, and each later step is
marked run/skip.

## 2. Update memory, and gate what survives into the queue

For each durable and **non-obvious** fact from step 1, create/update ONE file in the
project's auto-memory (dir `memory/`, index `MEMORY.md`), with the right frontmatter and
type (`user`/`feedback`/`project`/`reference`). Prefer updating an existing file over
duplicating; delete what proved wrong. Convert relative dates to absolute. Link with
`[[slug]]`.

**Pending items go through `tk-queue`** (`../../bin/tk-queue` relative to this file) — the
only writer of `next-steps.md` and `done-log.md`. Every change to either file arrives as one
of its subcommands, run from this session: new items enter via `add` (with **Class**,
**Effort** and **Criterion**, plus **Risk**, **Env** and **Project** where they apply — the
**Env** only when the item runs on a machine that is NOT this one, since an item that names
another environment is never dispatchable here; the criterion
is required, so decide it here rather than leaving "done" as the next closer's self-report;
a DECISION also demands `--deferred`, so ask the decision here and register the item
AUTONOMOUS wherever the user is still in the room);
a field of an open item changes via `edit`; resolved ones leave via `done --how "<pointer>"`
and discarded ones via `cancel --why`, which move them to `done-log.md`. This holds for the
one-word fix as much as for the new item: rewriting either file through Edit/Write/shell
breaks what the script guarantees — the ID sequence, the item actually LEAVING the queue,
and the log line that survives it. Contract, commands and the pointer rule:
`../kickoff/SKILL.md`.
That queue is what `/tk:kickoff` dispatches at the next session's open.

### The three survival gates

An item survives into the queue only when at least ONE **survival gate** holds — a
different object from the versioning gate of step 5 — and the item RECORDS which one. The
contract has no `Gate` field, so that record is the item's own text, in the writer's words
("waiting on the vendor's token"), except where a field already carries it:

| Survival gate | Holds when | The class it arrives as |
|---|---|---|
| **decision** | the item needs a human verdict that cannot be had now | `DECISION`, and `--deferred` carries it |
| **effort** | the work exceeds what is left of this session | `AUTONOMOUS`, and the text names what would not fit |
| **dependency** | a third party, a credential, or a machine that is not this one holds it | `BLOCKED` or `EXTERNAL` — or `--env <name from the site roster>` when the block is only WHERE it runs, matched exactly and refused otherwise — and the text names what is awaited |

`--effort` is required on every `add`, so a size alone marks nothing: the effort gate is
named in the text like any other. The survival gates are a disjunction, not a partition: two
can hold at once, and then the item records the FIRST in the order above — that order is the
tie-break, and nothing more. An item that passes none is resolved in this session;
"I will do it later" is not one.

**RECURRING is convert-or-resolve, and it is decided before the survival gates are
asked.** The class means the item is not a one-off, so no survival gate can justify parking
it. Creating a routine is an external effect, so with the user present the conversion is
put to them as a check of its own here — the check IS the authorization — and the item then
closes with `done --how "<the routine>"`. Unattended, it becomes a `DECISION` carrying the
routine ready to paste. Either way it is converted or resolved, never discarded as a session
finding: a discard answers a question, and this one needs a routine.

**Encode into the system:** a correction the user repeated or a check they did by hand is a
system signal, not an instance signal — propose encoding it (project skill, hook rule,
test) so it holds in every future iteration.
**Done when:** every durable fact of the session has a memory file (with a pointer in
`MEMORY.md`), every session finding carried here from step 1 is either resolved in this
session or in the queue behind a named gate, every item left in `next-steps.md` names the
survival gate that kept it there, no RECURRING item is parked, and every recurring
correction has an encoding proposed or discarded.

## 3. Update the repo documentation

Runs when the inventory shows changed behaviour or new knowledge. Make the documentation
reflect the current implementation: `README`, the project's instruction file
(`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`, whichever exists), glossary (`CONTEXT.md`), `docs/`
and ADRs. New commands, test counts, design sections, decisions — no command/count/path may
stay stale. Site extensions add further targets (wikis, status artifacts).
This is also where understanding that lives only in the conversation gets a written address,
which is what makes the `/clear` of step 6 cheap.
**Done when:** every behaviour changed in the session is reflected in every documentation
target — or nothing doc-relevant changed and that was said.

## 4. Verify

Runs when code changed. Run the project's test suite. **Detect the runner** from the
manifest/files: `pytest`/`python3 -m pytest`, `npm test`/`pnpm test`/`yarn test`,
`cargo test`, `go test ./...`, `make test`, etc. Changed runtime behaviour and the project
has an end-to-end verification skill (e.g. `verify`)? Run it too — a green test doesn't
prove the real flow works.

A session closing a queue item also owes that item's **criterion**, re-run here on the final
tree — the implementer's report is an input to that run, never a substitute. The rite, the
three attempts and the evidence block belong to `/tk:verify` (`../verify/SKILL.md`), which
writes the block ONCE, in the body of the PR or in the item's `--note`. Step 5 displays that
block; re-deriving the proof there would be a second measurement nobody asked for.
**Done when:** the tests pass — or the failures are reported to the user with the output —
or the skip was stated ("no code changed" / "project has no suite"); and every item closed
by this session carries its evidence block.

## 5. The versioning gate

Settle every version-control decision NOW — this gate is what makes the wrap-up a real
close. From the inventory, list the pending actions per repo: uncommitted work, unpushed
branches, PRs to open, PRs awaiting merge.

**The digest is what the user reads instead of the diff.** Any PR offered as "merge" gets
one: a per-file summary of the change, the forge link, the evidence block from step 4 — and
the four verdicts of **safe-to-merge**, one line each:

| # | Verdict | Green when |
|---|---|---|
| 1 | **Tests** | the suite ran on the final tree and passed |
| 2 | **Review** | the review flow ran, and every finding is fixed, or accepted with its justification written down |
| 3 | **Criterion** | the item's criterion was re-run here and passed |
| 4 | **Reversal** | the way back is named in one line (revert, flag, restore) |

Four green → merge is the recommended action. Any red → the digest says which one, and the
merge is not offered. Verdict 3 has a second shape: a **type-B criterion** ends at proof
ready, because the verdict is the user's, and it is GIVEN rather than inferred. The digest
displays the proof and the one-line claim it carries; the menu below then offers the verdict
as an option worded to say what checking it means — "the proof settles it; merge" — never a
bare "merge" that would read a verdict out of a checkbox. Verdict 3 stays amber until that
option is checked, so it is never the recommended-first one. The unattended path has nobody
to check it, which is why it defers.
A small diff (guidance: ≲150 lines) is still shown whole in the terminal and a large one
gets the link, but the diff is a courtesy: what authorizes the merge is the four verdicts,
which is the point of a user who does not read code.

**A package gets a vista beside its digest** — one self-contained HTML page in the site's
outbox, presenting the same close: stats, a card per PR with its risk tag and a link to its
proof, and the balance of the queue. It is written when this wrap-up closes an afk package and
in any session where the user asks for one; an ordinary close stays textual. The digest remains
the source, the vista only presents it — the five blocks, the outbox address and the checker
that gates the file are in `../../reference/vista.md`.

**Review fixes rewrite the PR body.** A PR whose body still describes the version before the
fixes tells the reviewer something the branch no longer does, so the body is rewritten in the
same breath as the fix commit.

Then ONE multiSelect `AskUserQuestion` with the actions, recommended first — the check IS
the authorization (this is how "commit/push only when the user asks" is satisfied). Execute
what was checked, following the project's conventions (required trailer lines; on the
default branch, branch first). Every unchecked action enters the queue as a DECISION item
via the full `add` line, since `--effort` and `--criterion` are required of every class:

```
tk-queue add "<the action>" --class DECISION --deferred "<why it waits for the user>" \
         --effort "<S/M/L + estimate>" --criterion "<A: a command | B: the user's verdict>"
```

A merge carries its digest reference (forge link + review status); any other action carries
the branch/paths involved. It is deferred by choice, not by omission, and the script demands
that choice in writing.

**Merging a stack, in this order:** retarget each child PR onto the new base BEFORE deleting
the base branch — deleting it first CLOSES the child (measured twice) — and remove the
worktrees of the branches in play before the merge round, since `--delete-branch` fails on a
branch that is still checked out somewhere.
**Done when:** every pending version-control action was executed or recorded as an explicit
DECISION — none merely implied — every merged PR's body describes what it merged, and the
user has the summary: what changed, what was verified, what was deferred.

## 6. Close: the report, the handoff, and the next step

### The closing template

The report follows this structure, and it is the structure that travels — a response-style
preference that disagrees with it loses:

```
**<N> closed · <M> carried · <K> blocked · <D> discarded**

**Closed** — everything that left the queue, FEITO or DESCARTADO alike
- <item> — <the one or two concrete gains it bought>
- <item> — <gains>  ·  risk: <what could still bite, in one clause>

**Carried**
- <item> — <the survival gate that kept it in the queue>

**Blocked**
- <item> — what is missing, and from whom

**Discarded** — session findings, which never entered the queue
- <session finding> — why it was dropped

**Blockers and notes for the next session:** <text — or "none", spelled out>

**Suggestions:** <what you would do next, if you have one — last, never mixed in above>
```

The stats line opens the report, and its first three counts are the queue's balance: what
left it against what is still in it. The fourth counts a different object — session findings
dropped in step 1, which never entered the queue — so the group is labelled and the two are
never summed. Discarding needs a user to do it, so an unattended run reports no discards and
carries its findings to the gates instead. Items group by outcome, never by chronology, and
a group of three or more becomes a table with those same columns. The gains are concrete —
"the queue can no longer lose a resolved item" beats "improved the queue" — and a case that
closed with no gain worth a line closed with nothing worth reporting, which is itself worth
one. The blockers line
is unskippable: "none" written out is an answer, an absent line is a rediscovery the next
session pays for. It is also the one line of the report that must survive the terminal —
it lands in the affected item's text, and a blocker too big for the item's size ceiling is
itself the signal that the briefing below is due.

### The handoff

The handoff comes at two levels. The default is the pair that already exists: the queue
item, in executable order, plus the opening sentence of the next session. **Escalate to the
five-field briefing when the understanding the next session needs lives only in this
conversation** — a task mid-flight, open hypotheses, a campaign spanning several items. The
briefing is the file `tk-queue handoff` writes — the sibling skills reach for it by that
command's name — and it is written and removed by that command alone:

```
tk-queue handoff <id> --objective "..." --state "..." --blockers "..." \
         [--skills "..."] [--pitfalls "..."]
```

It writes `handoff-T<id>.md` beside the queue files and warns that the item does not yet
point at it; run the `edit --text` line it prints, because `[[handoff-T<id>]]` in the item
is the briefing's only discovery path. A campaign gets ONE briefing, named for its anchor
item and pointed at by every item in it. The file dies when the LAST open item reaching it
closes — its own, or any pointing at it — which is measured behaviour of `done`/`cancel`,
not a step to perform: a briefing is never removed by hand.

**What the briefing carries is CONCLUSIONS, never a reading list.** This session holds them
hot and pays nothing to write them down; every successor pays full price to rediscover them,
and a prompt that says "read the parent and six neighbours" bills that price on every run.
Write the interface contract the next slice needs into the item, the briefing or the
tracker ticket, and say the ticket is self-sufficient. Reading that genuinely remains goes to
a subagent that returns a brief.

### The next step: /clear, /compact or /tk:docs-audit

ALWAYS close by explicitly recommending ONE path, with the why in 1–2 sentences. The
criterion is **where the understanding lives**: written down in docs or memory, relearning
it is reading, and `/clear` is cheap; living only in the conversation, it is documented in
step 3 or written as a briefing, and only genuinely conversational nuance is left for
`/compact`. There is no numeric estimate here — the cost of relearning is not measurable,
and a written handoff is what converts a `/compact` into a `/clear`.

- **`/clear`** — the default when the wrap-up ended clean: state 100% externalized (memory +
  docs + green tests + the gate settled), nothing mid-flight, and the next task is
  discrete.
  **Every PR this session opened is anchored** — merged, or carried in the queue as a
  DECISION whose evidence block sits in the PR body. A PR with no anchor gets its DECISION
  created on the spot, or is resolved before the clear; an open PR is a normal outcome, an
  invisible one is not. When recommending, **give 1–3 ready sentences to open the next
  conversation** — two shapes, chosen by what the sentence does:
  - **Invokes a slash command** (`/tk:kickoff afk`, `/implement`, …) — the command leads the
    sentence alone, no prose before it, and does NOT name the project: `tk-queue` and similar
    resolve state from the session's `cwd`, so the project is carried by telling the user
    where to open the session, e.g. "open the session in `/workspace/projects/foo` and type
    `/tk:kickoff afk` as the first line" — never by naming it inside the command line.
  - **Describes a task, no slash command** — name the project by path or name in the prose,
    e.g. "in `/workspace/projects/foo`, take T012", not "take T012". The next session may
    open anywhere (on the desktop it does not start in the project's folder), so a cold
    sentence that names no project points at nothing.
  Site extensions may add flow-specific opening lines.
- **`/compact`** — when a live thread resists being written down: a half-made negotiation,
  debugging whose hypotheses are still forming, conversation nuance that makes no sense as a
  memory file. Write the briefing first and this list usually empties; a session that will
  be reopened by a spawn has no history to compact at all, so the briefing is the only
  handoff that reaches it.
- **`/tk:docs-audit` (before the clear)** — when there's *drift* beyond the session's
  scope: step 3 hit stale statements this session did NOT cause, or a lot of code piled up
  since the last audit (several sessions/loops without a `docs-audit`). Audit first, then
  `/clear`.
- **None (continue)** — only when the user will immediately chain a related task and the
  current context is still short enough to beat a clean restart.

**Leaving rather than continuing?** Close with the ready pair: `/clear` now, then open the
next session in the project's directory and type `/tk:kickoff afk` as its first line — the
slash-command shape above, project carried by the `cwd`, not named in the sentence.
**Done when:** the report followed the template above, the handoff is written at the level
its trigger demands, every open PR is anchored, and the user received ONE clear
recommendation (not a neutral menu) with its justification — and, when the path is `/clear`,
the next conversation's opening sentences, each in the shape that fits.

## The `afk` argument

`/tk:wrap-up afk` — the user typed it and left; run every step without a single menu.

- Steps 1–4 and 6 run as written, with every menu turning into a queue entry: each session
  finding of step 1 and each unanswered choice becomes a `DECISION` item, carrying
  `--deferred afk` — the flag that separates a decision nobody could ask from one nobody
  bothered to ask.
- **Concurrent-session guard** first, in the form `../kickoff/AFK.md` defines — the claim on
  the queue's items leads, and the tree signals follow it: another live session working this
  repo → leave the tree untouched and report it.
- **Commit and push before the review; merge after it.** Commit the work to a branch —
  never the default branch — and push that branch BEFORE dispatching any review, so a
  session that dies on the quota wall leaves nothing uncommitted and nothing unpushed. Fix
  the findings in a follow-up commit, push again, and open the PR — or rewrite the body of
  the one already open — so the body describes the branch as it now stands and carries the
  evidence block. Invoking `afk` IS that authorization.
- **Merge runs on the strict version of the four verdicts**, with verdict 2 hardened: every
  finding FIXED, zero accepted, since accepting a finding is human judgment. Two cases keep
  the merge away from an unattended session, and each is checked by itself:
  - **A type-B criterion** — verdict 3 cannot turn green without the user, so the item ends
    at an open PR carrying its proof and waits.
  - **A repo whose default branch is consumed as it lands** — a marketplace serving it live,
    a boot script reading it — merges only with the user. Those repos are named in the site
    extension (`~/.claude/tk/wrap-up.md`), and a merge decided from a machine with no such
    file, or with no such list, is deferred: an unattended merge is authorized by a list
    that was READ, never by the silence of a file that was missing.
  Whatever is not merged enters the queue as a DECISION with its digest reference ready.
- **The vista is written after the merge round**, once every slice has its outcome, and it is
  named in the report only after `tk/bin/tk-vista-check` passes on it.
- The step-6 report ends with the ready pair for the user's return: `/clear` +
  `/tk:kickoff afk`.

**Done when:** the session state is externalized and one of three holds — the work is
committed, pushed, and every item ended either merged under the strict four verdicts or at
an open PR carrying its evidence block; or the concurrent-session guard stopped the run and
the report says so with the tree untouched; or there was nothing to commit. Whatever was
not merged sits in the queue as a DECISION, the package's vista is in the outbox with a green
`tk-vista-check`, or the report says which site address was missing, and no other external
effect happened.
