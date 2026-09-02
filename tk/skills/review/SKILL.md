---
name: review
description: "One lens over a committed slice. Use when a diff hits a trigger item, a handoff names an unfired lens, or a skill needs the ruler, inventory or prose rule."
---

A **lens** is a subagent that attacks the slice from one angle. The **parent** is the session
that acts on the findings. The lens fires **once**, on the committed slice, before the repo's
mandatory two-axis review.

**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` if they exist
(README, "Site extensions") — they name the tier and every rule's proof. Read the trigger items
in the site's CLAUDE.md, or wherever the extension points; where neither carries a list, §1's
site-list line decides.

## 1. Decide whether it fires

The lens covers code and the data that code writes. Prose an agent follows — a skill, a
CLAUDE.md, a runbook — takes the mandatory review alone, in one round. One exception: where the
changed paragraphs prescribe commands, one lens may fire. The exception's brief adds two
constraints to the block in `BRIEF.md`. Report only findings proven by RUNNING a prescribed
command, and refuse a finding whose fix is more prose about the prose. A firing the trigger
allowed that returns nothing runnable retires the exception. Say so in the PR body, and edit this
paragraph through its own PR. A report or document a human reads gets no review: the reader is
the review.

Inside a code slice the same line holds. Prose is what the artifact says ABOUT ITSELF and no
program reads: a comment, a docstring, a contract doc. A docstring a program consumes —
generated help, a parser — is the lens's. So is everything else the slice carries, its
identifiers and the strings a run emits alike.

The trigger is judged per diff, not per file: a mixed file counts only what changed. Measure the
diff against the site's trigger items at the slice's **base**: the branch point of the work
item. A rewrite split across PRs then measures as one rewrite. Capture the command once,
`git diff <base>...HEAD`, and confirm `<base>` resolves first. Three dots exclude the working
tree, so the slice is committed before the lens fires. A hit item fires the lens, unless the
parent declines it in one line in the PR as worth less than it costs.

Two **exemptions** cancel every item they answer. Each is a one-line **exemption receipt** in
the PR, which the wrap-up gate shows to the user:

- A behaviour-preserving refactor with mutation proved: enumerated tests, no vacuous kill. It
  answers every item except the user-data one.
- A change whose every finding would be a nit (§3).

No item hit: the mandatory review is the whole review. The parent may still fire, stating why in
one line. No site list at all: the parent decides on its own judgement, stating why.

**Done when:** the PR carries either the firing receipt (§2) or the reason it did not fire.
Where the slice has no PR, the item's note carries it.

## 2. Fire the lens

Check that the window fits (§5). Announce the **firing receipt**: the item hit, the base, the
estimated cost. Fire **one** subagent, on the tier the site extension names, at
`effort: "high"`; where no site names one, the tier is `opus`. Findings live in the
parent's context, so the parent fires it directly. Pick the angle from the slice's class,
`system` by default: a slice matching two rows, or none of them cleanly, takes it.

| Slice class | Angle |
|---|---|
| arithmetic or a transform over real data | **data** |
| a rewrite of an existing file | **regression** |
| anything else, a contract or a state machine included | **system** |

Hand the lens the block in `BRIEF.md`, filled in, carrying its angle's attack line.

**Done when:** the report is in, or the lens died and §5 hands it off.

## 3. Grade and correct

Reproduce each finding first: lens grades err in both directions. Then grade it by **impact**
against the base; the size of the fix is not a grade. A **nit** changes nothing a reader or a
run depends on. Everything else is a **defect**, a one-character boundary bug included. Fix nits
on the spot and list them.

A finding that reproduces at the **branch point** is the repo's backlog, not this slice's. Carry
it to the item or the ticket and say so in the inventory. A mismatch between what the program
does and what its words say is graded by the **wrong side**. A wrong run is a code defect; stale
words are prose, fixed on the spot like a nit.

Defects force a **correction batch**: fix each one, or reject it with a reason specific to the
finding, recorded in the inventory. **The correction batch goes to the repo's mandatory two-axis
review, never to another lens**. Its brief carries the invariant each finding violated: the spec
of a repair is the finding. Where the repo declares a size ceiling for the file, a batch that
grows it past the ceiling owes a line in the PR body.

**A repeated mechanism is a design signal**. Two findings violating the same guard, or a
correction that writes one statement in one more place, means the next instance is already
written. An incomplete repair is a correction, not a signal.

A design signal blocks the merge. The parent answers one question and takes the answer to the
user, with the findings: should the artifact exist as built? Code earns its form where the
answer must be identical every run or fail loudly; everywhere else the form is prose. The repair
that follows the user's call consolidates the mechanism into a single source. Unattended, the
slice is **blocked**: a queue item carrying the findings, through the queue's one writer.

**Done when:** every finding carries a grade the parent reproduced, and a fix, a rejection or a
carried-over item.

## 4. Close

The lens ships an **attack inventory**:

- the attacks run, the artifact each one touched, and the run that shows it ran;
- the trigger item on the firing receipt, and the attack that answers it;
- every finding: its guard or invariant, its grade (both, when the parent's differed), its fix,
  its recorded rejection, or the item it was carried to.

A lens that found nothing ships the inventory too: the artifacts are the proof of work. An empty
or one-line inventory is a failure, not approval. Merge stays with the user.

**Done when:** the inventory is in the PR body (unattended: there or on the item's handoff
briefing), and every finding appears in it.

## 5. Window and handoff

**The lens and the review of its correction batch may not cost more window together than the
implementation they review**. Where the lens alone would breach that ceiling, the slice takes
the mandatory review alone, with the reason in the PR.

Reviews serialize: the lens fires only when the remaining window fits it and every review
already running in this session. One that does not fit waits whole, as a queue item heading the
next window's review line.

A lens is **dead** when the window ended, the subagent failed or the wall killed it before its
report arrived. A handoff then names the slice, the base and the angle. The lens has not run:
the next session fires it whole.
