---
name: review
description: "One lens over a committed slice. Use when a diff hits a trigger item, a handoff names an unfired lens, or a skill needs the ruler, inventory or prose rule."
---

A **lens** is a subagent that attacks the slice from one angle. The **parent** is the session
that acts on the findings. The lens fires **once**, on the committed slice, before the repo's
mandatory two-axis review.

**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` if they exist —
they name the tier and every rule's proof. Read the trigger items in the site's CLAUDE.md, or
wherever the extension points; where neither carries a list, §1 decides.

## 1. Decide whether it fires

The lens covers code and the data that code writes. Prose an agent follows — a skill, a
CLAUDE.md, a runbook — takes the mandatory review alone, in one round. One exception: where the
changed paragraphs prescribe commands, one lens may fire. Its brief adds two constraints to
`BRIEF.md`. Report only findings proven by RUNNING a prescribed command, and refuse a finding
whose fix is more prose about the prose. A firing the trigger allowed that returns nothing
runnable retires the exception, said in the PR body and edited here through its own PR. A
report or document a human reads gets no review: the reader is the review.

Inside a code slice the same line holds. Prose is what the artifact says ABOUT ITSELF and no
program reads: a comment, a contract doc. A docstring a program consumes — generated help, a
parser — is the lens's, and so is everything else the slice carries, identifiers and emitted
strings alike.

The trigger is judged per diff, not per file: a mixed file counts only what changed. Measure the
diff against the site's trigger items at the slice's **base**: the branch point of the work
item. A rewrite split across pull requests then measures as one. Capture the command once, `git
diff <base>...HEAD`, confirming `<base>` resolves first. Three dots exclude the working tree, so
the slice is committed before the lens fires. A hit item fires the lens, unless the parent
declines it in one line as worth less than it costs.

Two **exemptions** cancel every item they answer, each a one-line **exemption receipt** in the
PR that the wrap-up gate shows the user:

- A behaviour-preserving refactor with mutation proved: enumerated tests, no vacuous kill. It
  answers every item except the user-data one.
- A change whose every finding would be a nit (§3).

No item hit: the mandatory review is the whole review; the parent may still fire, stating
why. No site list at all: the parent decides, stating why.

**Done when:** the PR carries either the firing receipt (§2) or the reason it did not fire.
Where the slice has no PR, the item's note carries it.

## 2. Fire the lens

Check that the window fits (§5). Announce the **firing receipt**: the item hit, the base, the
estimated cost. Fire **one** `Agent`, `subagent_type: "tk:lens"`: that definition pins `model:
opus` and `effort: high`, an effort no dispatch can carry. A site extension naming another tier
passes it as `model:`. Findings live in the parent's context, so the parent fires it directly.
Pick the angle from the slice's class; a slice matching two rows, or none cleanly, takes
`system`.

| Slice class | Angle |
|---|---|
| arithmetic or a transform over real data | **data** |
| a rewrite of an existing file | **regression** |
| anything else, a contract or a state machine included | **system** |

Hand the lens the block in `BRIEF.md`, filled in, carrying its angle's attack line.

**Done when:** the report is in, or the lens died and §5 hands it off.

## 3. Grade and correct

Reproduce each finding first: lens grades err in both directions. Then grade it by **impact**
against the base; the size of the fix is not a grade. A **nit** changes nothing a reader or a run
depends on. Everything else is a **defect**, a one-character boundary bug included. Fix nits on
the spot and list them.

A finding that reproduces at the **branch point** is the repo's backlog, not this slice's. It
takes the slice's ticket, failing that ONE item per firing (`../../reference/session-finding.md`).
`tk-queue edit --text` REPLACES the item's text, so a later finding reads it and writes the union.

A mismatch between run and words is graded by the **wrong side**. A wrong run is a code defect;
stale words are prose, fixed on the spot like a nit.

Defects force a **correction batch**: fix each one, or reject it with a reason specific to the
finding, recorded in the inventory. A defect has a fourth exit: a `fixer` dispatched on the spot
(`../../reference/subagent-policy.md`), committing into the slice's branch in a window of its
own. Two conditions hold together: the defect is in THIS session's diff, and it carries a
criterion a run can check.

**One `fixer` cycle per firing**, never resumed: `../kickoff/AFK.md`'s *The fixer cap* counts
it. One dispatch carries every eligible defect, and what it leaves unclosed goes to ONE item
carrying its inventory.

**The correction batch goes to the repo's mandatory two-axis review, never to another lens**. Its
brief carries the invariant each finding violated: the spec of a repair is the finding. A batch
that grows a file past a size ceiling the repo declares owes a line in the PR body.

**A repeated mechanism is a design signal**. Two findings violating the same guard, or a
correction that writes one statement in one more place, means the next instance is already
written. An incomplete repair is a correction, not a signal.

A design signal blocks the merge, and the repository decides who answers. Where its code handles no
business data, the call is the parent's own (`../../reference/subagent-policy.md`). The cycle
consolidates the mechanism into a single source, lifting the block; the close reports the call
with a veto line. Handling business data, the unattended slice stays **blocked** and parks
(`../../reference/session-finding.md`).

**Done when:** every finding carries a grade the parent reproduced, and a fix, a dispatched
`fixer`, a rejection or a carried-over item naming its destination.

## 4. Close

The lens ships an **attack inventory**:

- the attacks run, the artifact each one touched, and the run that shows it ran;
- the trigger item on the firing receipt, and the attack that answers it;
- every finding: its guard or invariant, its grade (both, when the parent's differed), its fix,
  its recorded rejection, or the item it was carried to.

A lens that found nothing ships the inventory too: the artifacts prove the work. An empty
or one-line inventory is a failure, not approval. Merge stays with the user.

**Done when:** the inventory is in the PR body (unattended: there or on the item's handoff
briefing), and every finding appears in it.

## 5. Window and handoff

**The lens and the review of its correction batch may not cost more window together than the
implementation they review**. Where the lens alone would breach that ceiling, the slice takes
the mandatory review alone, the reason in the PR.

Reviews serialize: the lens fires only when the remaining window fits it and every review
already running. One that does not fit waits whole, as a queue item for the next window.

A lens is **dead** when the window ended, the subagent failed or the wall killed it before its
report arrived. A handoff then names the slice, the base and the angle. The lens has not run:
the next session fires it whole.
