---
name: review
description: "Lens campaign over a delivered slice — the second pair of eyes on top of the repo's mandatory code review, with the severity ruler (nit/defect), the re-lens loop, the design signal and the attack inventory. Use when a diff hits a trigger item named in the site's CLAUDE.md, when a diff edits prose an agent follows (to sort amendment from campaign), when the parent claims an exemption, when the parent fires it by choice, when a campaign resumes from a handoff, or when another skill needs the severity ruler or the inventory."
---

A **campaign** is one or more **rounds** of **lenses** — subagents, each attacking the slice
from one angle — fired by the **parent** (the session that acts on the findings) on top of the
repo's mandatory review. It exists because five lenses with distinct prompts keep finding what
two fixed axes approve, and because a repeated finding is a design signal, not a coverage gap.

**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` (project root) if
they exist. They carry the site's user-data directories, lens memories and the provenance of
every threshold below. The **trigger items** live in the site's CLAUDE.md; without a site list,
the parent fires on its own judgement, stating why. Everything else in this file holds unchanged.

## 1. Decide whether it fires

An **executable document** — prose an agent follows: a skill, a CLAUDE.md, a runbook — is
decided by one test, before the items: **would any agent following the document act
differently?** No, provably from the diff: an **amendment**, the mandatory review only, run on
the prose. Yes, or in doubt: a campaign. A new or rewritten executable document always fires;
the test cannot be proved from a diff that replaces the text. The PR carries the **amendment
receipt** — the sentences touched, old → new; no receipt, campaign.

Every other diff is measured against the site's trigger items, at the **slice's base** — the
branch point of the work item, never the previous PR or commit, so a rewrite split across PRs
still measures as one rewrite. A hit item fires the campaign and is never skipped or downgraded.
Two exemptions erase every item they answer, when the PR carries the **exemption receipt** in
one line — the wrap-up gate shows it to the user, who is the second pair of eyes on it:

- a behaviour-preserving refactor with **mutation proved** — enumerated tests, no vacuous
  kills; a refactor receipt never answers a user-data item;
- a change every finding of which would be a **nit** (defined in §3).

No item hit, no firing; the parent may still fire, stating why in one line. A slice that did
not fire answers to the mandatory review alone.

## 2. Round 1

The parent announces the **firing receipt** — the item hit, the base, and the cost, estimated
by the window floor of §6 — then fires the lenses itself, never through a nested subagent:
findings die inside a subagent's context. Five lenses, picked per slice from the pool below,
never a fixed reviewer set; in parallel, blind to each other; each a subagent at `high` effort.
**All rounds run at `high`.** Sonnet is the default tier for lens work (the logged deviation
from the parent-model default); the site extension may add one stronger lens for contract or
design slices.

Mandatory lenses by slice type. Rows stack: a slice matching several rows carries every
mandatory lens of each; the rest come from the pool.

| Slice type | Mandatory |
|---|---|
| plain source | regression, vacuity/mutation |
| rewrite of an existing file | regression |
| executable document, new or edited | execution |
| rewritten agent-facing prose | prose×code |
| writes, in the diff or when it runs, anything a later reader consumes as data — config, queues, records, memory, wiki | data or corruption |

The pool:

- **data** — what happens when the input is ugly, duplicated, real.
- **corruption** — what a write path can leave behind.
- **vacuity/mutation** — switch each new guard off in a copy and run the suite; green is a finding.
- **prose×code** — does every claim match the artifact it points at.
- **regression** — a KEEP / MOVE / DROP table of every order against the base.
- **execution** — read the document as the agent that will run it unattended: where would you
  be stuck, guess, or destroy.
- **adversarial** — be the agent that wants to skip the rule; find the reading that lets you.
- **system** — extract the state machine; every state needs a named entry and exit; find the
  pair of sentences that double-fire.

Every lens prompt carries five things:

1. the invariants the slice must hold, named;
2. a demand for proof against the real artifact — the binary run, the fixture, the file —
   never a code reading;
3. the base to compare against, and the firing receipt: a lens that contradicts the receipt
   reports it as a defect on the receipt;
4. a grade per finding (nit or defect, §3), the guard or invariant it violates, and a concrete
   failure scenario;
5. the sentence "an empty answer is a failure — if you find nothing, list the attacks you ran".

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
the finding, recorded in the inventory. A recorded rejection is not a defect in the rounds
that follow; a finder re-raising it reopens the rejection with the user, not the loop. Then
**re-lens the finders** — exactly the lenses that found a defect, never a fixed count —
against the batch. Add a lens when a correction enters ground no finder covered (a moved
block, a new write path); the added lens is a finder from then on. The correction commit is a
round of this campaign, never a new trigger.

A round is **clean** when it produced no defect. The **budget** is 3 rounds, round 1 included;
the mandatory review is round 0, outside it. Three signals stop the loop. Each blocks the
merge, escalates with the round-by-round findings, and the slice moves only on the user's
answer:

- **Design signal**, checked at every round from round 2: two or more defects, or a mechanism
  an earlier round already found — the same guard or invariant violated, a new instance each
  time; an incomplete repair is a correction, not a signal. Before asking, the parent writes
  whether the artifact should exist as built: code only when the answer must be identical
  every run or fail loudly, otherwise prose in a skill. The user picks **correct and
  continue**, **redesign**, **cut** or **block**.
- **Ceiling**: round 3 not clean, or any later round not clean. The user picks **one more
  round**, **redesign** or **block**. When the ceiling and the signal fire together, the
  signal's menu governs.
- **All rejected**: a round whose defects were all rejected is not clean; it goes to the user
  with the ceiling's menu, and outranks the signal.

A **redesign** is reviewed by the round-1 composition — five lenses, mandatory by slice type —
because the artifact changed. It runs on the rounds left, never fewer than one: when none
remain, the parent asks how many rounds the user grants, at least one. It never opens a new
budget, and the design signal's history carries over. A **cut** drops the artifact: the
deletion is a slice of its own, decided by §1 like any diff, and this campaign ends blocked.
A **blocked** slice is recorded as a queue item carrying the round-by-round findings; the user
reopens it into the round after the block, on the rounds they grant, with the signal's history
intact.

| State | Entry | Exit |
|---|---|---|
| not fired | no item hit, an amendment, or an exemption receipt | mandatory review only → merge-ready; or the parent fires by choice → round 1 |
| round N | trigger or the parent's choice (N=1); correction batch; a redesign; a granted round; a resumed handoff | clean → inventory; defects → correction batch, design signal (N≥2), all rejected, or ceiling (N≥3) |
| correction batch | a round with defects, none escalated | re-lens the finders → round N+1 |
| design signal | round N≥2: 2+ defects, or a repeated mechanism | user: correct and continue → correction batch; redesign → round N+1; cut → blocked; block → blocked |
| ceiling | round N≥3 not clean | user: one more round → round N+1; redesign → the rounds granted; block → blocked |
| all rejected | a round whose defects were all rejected | user: as at the ceiling |
| waiting for window | the campaign does not fit the remaining window (§6) | the next window → round N, unchanged |
| handed off | the window ends mid-campaign | the next session re-fires the named pending round |
| blocked | user's pick | queue item with the findings; the user reopens → round N+1 |
| clean | a round with no defect | attack inventory → merge-ready |

## 5. Close

A clean round ships the **attack inventory**; an empty or one-line inventory is a failure, not
approval:

- the attacks run and the artifacts touched;
- every finding of every round — its guard or invariant, its grade, both grades when they
  differed, its fix or its recorded rejection;
- the ground the corrections opened, with the lens added or declined.

A slice that fired is merge-ready only after a clean round; merge stays with the user.

## 6. Window

A campaign costs at least as much window as the implementation — that floor is the plan's
review line, and a plan without one hides half the slice. Campaigns serialize: a campaign
starts only when the remaining window fits it and every campaign already running, at that
floor. A campaign is never trimmed to fit; the slice waits — implemented, unreviewed, unmerged
— as a queue item heading the next window's review line.

A handoff mid-campaign names the pending round, the lenses that reported and the lenses that
died. The partial round has not run: the next session re-fires every lens of that round, and
the reports it inherits are context, not findings. Unattended, findings and verdicts land on
the slice's PR or on the item's handoff briefing, never only in a subagent transcript.
