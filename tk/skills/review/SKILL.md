---
name: review
description: "Lens campaign over a delivered slice — the second pair of eyes on top of the repo's mandatory code review, with the severity ruler (nit/defect), the re-lens loop, the design signal and the attack inventory. Use when a diff hits a trigger item named in the site's CLAUDE.md, when the parent fires it by choice, when a campaign resumes from a handoff, or when another skill needs the severity ruler or the inventory."
---

A **campaign** is one or more **rounds** of **lenses** — subagents, each attacking the slice
from one angle — fired by the **parent** (the session that acts on the findings) on top of the
repo's mandatory review. It exists because five lenses with distinct prompts keep finding what
two fixed axes approve, and because a repeated finding is a design signal, not a coverage gap.

**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` (project root) if
they exist. They carry the site's trigger items, user-data directories, lens memories and the
provenance of every threshold below. Without them the defaults here hold.

## 1. Decide whether it fires

The site's CLAUDE.md names the **trigger items**. Measure the diff against the **slice's
base** — the branch point of the work item, never the previous PR or commit, so a rewrite
split across PRs still measures as one rewrite. A hit item fires the campaign; the parent
announces the item and the estimated cost, then runs. A hit item is never skipped or
downgraded. Two exemptions erase every item they answer, when the PR names them in one line:

- a behaviour-preserving refactor with **mutation proved** — enumerated tests, no vacuous
  kills; a refactor receipt never answers a user-data item;
- a change every finding of which would be a **nit** (defined in §3).

An **executable document** — prose an agent follows: a skill, a CLAUDE.md, a runbook — has one
test in place of the items: **would any agent following the document act differently?** No,
provably from the diff: an **amendment**, the mandatory review only. Yes, or in doubt: a
campaign. A new executable document is a rewrite. The PR carries the receipt — the sentences
touched, old → new; no receipt, campaign.

No item hit, no firing; the parent may still fire, stating why in one line. A slice that did
not fire answers to the mandatory review alone.

## 2. Round 1

Five lenses, in parallel, blind to each other, each a subagent at `high` effort. **All rounds
run at `high`.** Sonnet is the default tier for lens work (the logged deviation from the
parent-model default); the site file may add one stronger lens for contract or design slices.

Mandatory lenses by slice type; the rest come from the pool:

| Slice type | Mandatory |
|---|---|
| plain source | regression, vacuity/mutation |
| rewrite of an existing file | regression |
| executable document (new or edited) | execution |
| rewritten agent-facing prose | prose×code |
| writes anything a later reader consumes as data — config, queues, records, memory, wiki | data or corruption |

The pool: **data** (what happens when the input is ugly, duplicated, real) · **corruption**
(what a write path can leave behind) · **vacuity/mutation** (switch each new guard off in a
copy, run the suite: green is a finding) · **prose×code** (does every claim match the
artifact it points at) · **regression** (KEEP / MOVE / DROP table of every order against the
base) · **execution** (read the document as the agent that will run it unattended: where
would you be stuck, guess, or destroy) · **adversarial** (be the agent that wants to skip the
rule; find the reading that lets you) · **system** (extract the state machine; every state
needs a named entry and exit; find the pair of sentences that double-fire).

Every lens prompt carries five things: the invariants the slice must hold, named; a demand
for proof against the real artifact — the binary run, the fixture, the file — never a code
reading; the base to compare against; a grade per finding (nit or defect, §3) with a concrete
failure scenario; and the sentence "an empty answer is a failure — if you find nothing, list
the attacks you ran". Each lens also checks the parent's trigger receipt against the diff.

## 3. Grade

The parent grades every finding by IMPACT against the slice's base, never by the size of the
fix. A **nit** changes nothing a reader or a run depends on. Everything else is a **defect**;
a one-character boundary bug is a defect. Reproduce a finding before grading it: lens grades
have been wrong in both directions. When the parent's grade differs from the lens's, the
inventory records both.

Nits are fixed on the spot and listed; they reopen nothing. A nit in a queue file goes through
the queue's one writer.

## 4. Loop

Defects force a **correction batch**: fix every one, or reject it with a reason specific to
the finding, recorded in the inventory. Then **re-lens the finders** — exactly the lenses that
found a defect, never a fixed count — against the batch, adding a lens when a correction enters
ground no finder covered (a moved block, a new write path); the added lens is a finder from
then on. The correction commit is a round of this campaign, never a new trigger.

A round is **clean** when it produced no defect. A round whose defects were all rejected is not
clean: its rejections escalate to the user like the ceiling. The **budget** is 3 rounds, round
1 included; the mandatory review is round 0, outside it. Two signals stop the loop. Both block
the merge, both escalate with the round-by-round findings, and the slice moves only on the
user's answer:

- **Design signal**, checked at every round from round 2: two or more defects, or a mechanism
  any earlier round already found — the same guard or invariant violated, whatever the input.
  The design is wrong, not the coverage. Before asking, the parent writes whether the artifact
  should exist as built: code only when the answer must be identical every run or fail loudly,
  otherwise prose in a skill. The user picks **cut**, **redesign** or **block**.
- **Ceiling**: round 3 not clean. The user picks **one more round**, **block** or **redesign**.

A **redesign** runs on the rounds left; at the ceiling, on the rounds the user grants. It never
opens a new budget, and the design signal's history carries over. A **cut** drops the artifact;
the deletion commit is a round. Every round past the budget needs the user's word and returns
to the ceiling's choice when it is not clean. A **blocked** slice is recorded as a queue item
carrying the round-by-round findings.

| State | Entry | Exit |
|---|---|---|
| not fired | no item hit, or an amendment, or an exemption receipt | mandatory review only → merge-ready; or the parent fires by choice → round 1 |
| round N | trigger (N=1); correction batch (N≥2); user grants a round (N≥4) | clean → inventory; defects → correction batch, design signal (N≥2), or ceiling (N=3) |
| correction batch | a round with defects, none escalated | re-lens the finders → round N+1 |
| design signal | round N≥2: 2+ defects or a repeated mechanism | user: cut → deletion round; redesign → round N+1 on the rounds left; block → queue item |
| ceiling | round 3 not clean, or any later round not clean | user: one more round → round N+1; redesign → the rounds granted; block → queue item |
| all rejected | a round whose defects were all rejected | user: as at the ceiling |
| handed off | window ends mid-campaign | the next session resumes at the named pending round |
| blocked | user's pick | queue item with the findings; reopened only by the user |
| clean | a round with no defect | attack inventory → merge-ready |

## 5. Close

A clean round ships the **attack inventory**: the attacks run, the artifacts touched, every
finding of every round with its grade — both grades when they differed — and its fix or its
recorded rejection, and the ground the corrections opened with the lens added or declined. An
empty or one-line inventory is a failure, not approval. A slice that fired is merge-ready only
after a clean round; merge stays with the user.

## 6. Window

A campaign costs at least as much window as the implementation — that floor is the plan's
review line, and a plan without one hides half the slice. Campaigns serialize: a campaign
starts only when the remaining window fits it and every campaign already running, at that
floor. A campaign is never trimmed to fit; the slice waits — implemented, unreviewed, unmerged
— as a queue item heading the next window's review line.

A handoff mid-campaign names the pending round, the lenses that reported and the lenses that
died; the partial round has not run. Unattended, findings and verdicts land on the slice's PR
or on the item's handoff briefing, never only in a subagent transcript. The lenses are fired by
the parent, never by a nested subagent: findings die inside a subagent's context.
