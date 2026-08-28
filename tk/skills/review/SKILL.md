---
name: review
description: "One lens over a delivered code or data slice: a single strong subagent attacks the diff from the angle the slice's class calls for, on top of the repo's mandatory review, with a severity ruler and an attack inventory. Use when a diff hits a trigger item in the site's CLAUDE.md, when the parent claims an exemption or fires by choice, when a pass resumes from a handoff, or when another skill needs the ruler or the inventory. Prose gets the mandatory review only."
---

A **lens** is a subagent that attacks the slice from one angle. The **parent** is the session
that acts on the findings. The lens fires **once**, after the repo's mandatory review passed.

**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` (project root) if
they exist. They carry the user-data directories, the stronger tier, and the measurement behind
every rule below. The **trigger items** live in the site's CLAUDE.md.

## 1. Decide whether it fires

The lens covers code and the data that code writes. Prose an agent follows or a human reads
(a skill, a CLAUDE.md, a runbook, a report) is reviewed by the mandatory review alone.

Inside a code slice the same line holds, as a test rather than a list. Prose is what the
artifact says ABOUT ITSELF and no program reads: a comment, a docstring, a contract doc.
Everything else the slice carries is the lens's, its identifiers and the strings a run emits
alike. A docstring some program consumes (generated help, a parser) is read by a program, so it
is the lens's too.

Measure the diff against the site's trigger items at the slice's **base**: the branch point of
the work item, so a rewrite split across PRs measures as one rewrite. Capture the command once,
`git diff <base>...HEAD`, and confirm `<base>` resolves before anything else.

Two **exemptions** cancel every item they answer. Each is a one-line **exemption receipt** in
the PR; the wrap-up gate shows it to the user, who is the second pair of eyes on it:

- A behaviour-preserving refactor with mutation proved: enumerated tests, no vacuous kill. It
  answers every item except the user-data one.
- A change whose every finding would be a nit (§3).

No item hit: the mandatory review is the whole review. The parent may still fire, stating why in
one line. No site list at all: the parent decides on its own judgement, stating why.

**Done when:** the PR carries either the firing receipt (§2) or the reason it did not fire.

## 2. Fire the lens

Check that the window fits (§5). Announce the **firing receipt**: the item hit, the base, the
estimated cost.

Fire **one** subagent, on the site's strongest tier at `effort: "high"` — the logged deviation
from the parent-model default. Findings live in the parent's context, so the parent fires it
directly. Pick the angle from the slice's class:

| Slice class | Angle |
|---|---|
| a contract, a protocol, a state machine, prose a program parses | **system** |
| arithmetic or a transform over real data | **data** |
| a rewrite of an existing file | **regression** |
| anything else | **system** |

- **system**: extract the state machine; every state needs a named entry and exit; find the
  seam where two parts must agree and neither is wrong alone.
- **data**: feed the ugly, duplicated, real input and watch what comes out.
- **regression**: a KEEP / MOVE / DROP table of every behaviour against the base.

The brief is this block, filled in:

```
You are the <ANGLE> lens on <slice>. Base: <base>. Diff: git diff <base>...HEAD.
Invariants the slice must hold: <list them>.
Firing receipt: <receipt>. A receipt that is wrong is itself a defect: report it.
Attack: <the angle's line>.
You are alone. Cover what carries the worst failure, not what is cheapest to check.
Run the artifact — the binary, the fixture, the file — on inputs you build yourself.
Reproduce every finding and paste the run: a code reading is not proof.
Switch each new guard off in a copy and run the suite; green is a finding.
Ask what the code does with input it never enumerated: a default that absorbs the
unknown destroys data in silence, a default that refuses is recoverable.
Report each finding as: grade (nit | defect), the guard or invariant it violates, a
concrete failure scenario (input or state -> wrong output), and the run that proves it.
Close with the class of defect this slice keeps producing, where there is one.
Finding nothing is a full answer: list the attacks you ran and the artifact each one touched.
```

**Done when:** the report is in, or the lens is named dead for §5.

## 3. Grade and correct

Reproduce each finding first: lens grades err in both directions. Then grade it by **impact**
against the base; the size of the fix is not a grade. A **nit** changes nothing a reader or a
run depends on. Everything else is a **defect**, a one-character boundary bug included. When the
parent's grade differs from the lens's, the inventory records both. Fix nits on the spot and
list them. A nit in a queue file goes through the queue's one writer.

A finding that reproduces at the **branch point** is the repo's backlog, not this slice's: carry
it to the item or the ticket and say so in the inventory.

A mismatch between what the program does and what its words say is graded by the **wrong
side**. When the run is the wrong side, it is a code defect. When the code is right and only
the words are stale, it is prose, fixed on the spot like a nit.

Defects force a **correction batch**: fix each one, or reject it with a reason specific to the
finding, recorded in the inventory. **The correction batch goes to the repo's mandatory two-axis
review, never to another lens.** One pass is the whole budget.

**A repeated mechanism is a design signal.** Two findings violating the same guard, or a
correction that writes one statement in one more place, means the next instance is already
written. The parent answers one question before correcting: should the artifact exist as built?
Code earns its form where the answer must be identical every run or fail loudly; everywhere else
the form is prose. Then consolidate the mechanism into a single source. A design signal blocks
the merge and goes to the user with the findings.

**Done when:** every finding carries a grade the parent reproduced, and a fix, a rejection or a
carried-over item.

## 4. Close

The pass ships an **attack inventory**:

- the attacks run and the artifacts each one touched;
- every finding: its guard or invariant, its grade (both, when they differed), its fix, its
  recorded rejection, or the item it was carried to.

A pass that found nothing ships the inventory too: the artifacts are the proof of work, and an
empty or one-line inventory is a failure, not approval. Merge stays with the user.

**Done when:** the inventory is in the PR body (unattended: there or on the item's handoff
briefing), and every finding appears in it.

## 5. Window and handoff

**A pass costs at most the window the implementation it reviews cost.** That ceiling binds.
Where the lens alone would breach it, the slice takes the mandatory review alone, with the
reason in the PR.

Passes serialize: one starts only when the remaining window fits it and every pass already
running. One that does not fit waits whole, as a queue item heading the next window's review
line; the slice stays implemented, unreviewed, unmerged.

A handoff mid-pass names the slice, the base and the angle. The lens has not run: the next
session fires it whole.
