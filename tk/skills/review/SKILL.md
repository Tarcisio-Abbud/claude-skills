---
name: review
description: "Lens campaign over a delivered code or data slice: five subagents attack the diff from distinct angles on top of the repo's mandatory code review, with a nit/defect ruler, a re-lens loop on a 3-round budget, a design signal and an attack inventory. Use when a diff hits a trigger item named in the site's CLAUDE.md, when the parent claims an exemption or fires it by choice, when a campaign resumes from a handoff, or when another skill needs the severity ruler or the inventory. Prose (a skill, a CLAUDE.md, a report) gets the mandatory review only."
---

A **lens** is a subagent that attacks the slice from one angle. The **parent** is the session
that acts on the findings. A **round** is one firing of lenses; a **campaign** is the rounds
until one comes back clean or the user stops it. The campaign runs after the repo's mandatory
review passed.

**Site extensions:** read `~/.claude/tk/review.md` and `.claude/tk/review.md` (project root) if
they exist. They carry the user-data directories, the lens memories, a stronger lens, and the
provenance of every threshold below. The **trigger items** live in the site's CLAUDE.md.

## Process

### 1. Decide whether it fires

The campaign covers code and the data that code writes. Prose an agent follows or a human
reads (a skill, a CLAUDE.md, a runbook, a report) is reviewed by the mandatory review alone.

Measure the diff against the site's trigger items at the slice's **base**: the branch point of
the work item, so a rewrite split across PRs measures as one rewrite. Capture the command once,
`git diff <base>...HEAD`, and confirm `<base>` resolves before anything else. One item hit fires
the campaign.

Two **exemptions** cancel every item they answer. Each is a one-line **exemption receipt** in the
PR; the wrap-up gate shows it to the user, who is the second pair of eyes on it:

- A behaviour-preserving refactor with mutation proved: enumerated tests, no vacuous kill. It
  answers every item except the user-data one.
- A change whose every finding would be a nit (§3).

No item hit: the mandatory review is the whole review. The parent may still fire, stating why in
one line. No site list at all: the parent decides on its own judgement, stating why.

**Done when:** the PR carries either the firing receipt (§2) or the reason it did not fire.

### 2. Fire round 1

Check that the window fits (§7). Announce the **firing receipt**: the item hit, the base, the
estimated cost.

Pick five lenses from the pool below. Mandatory ones come from the slice type; rows stack, the
rest is the parent's pick for this slice.

| Slice type | Mandatory |
|---|---|
| plain source | regression, vacuity/mutation |
| rewrite of an existing file | regression |
| writes data a later reader consumes (config, queue, record, memory, wiki), in the diff or when it runs | data or corruption |

The pool:

- **data**: feed the ugly, duplicated, real input and watch what comes out.
- **corruption**: interrupt or replay every write path and read what it left behind.
- **vacuity/mutation**: switch each new guard off in a copy and run the suite; green is a finding.
- **regression**: a KEEP / MOVE / DROP table of every behaviour against the base.
- **adversarial**: find the input or state that walks past each new guard.
- **system**: extract the state machine; every state needs a named entry and exit; find the pair
  of paths that double-fire.

Fire the five yourself, in parallel, blind to each other: one subagent each, Sonnet at
`effort: "high"` (the logged deviation from the parent-model default; the site extension may add
one stronger lens). Findings live in the parent's context, so the parent fires them directly.
Each prompt is this block, filled in:

```
You are the <LENS> lens on <slice>. Base: <base>. Diff: git diff <base>...HEAD.
Invariants the slice must hold: <list them>.
Firing receipt: <receipt>. A receipt that is wrong is itself a defect: report it.
Attack: <the lens's line from the pool>.
Prove every finding against the real artifact: run the binary, the fixture, the file.
A code reading is not proof.
Report each finding as: grade (nit | defect), the guard or invariant it violates,
and a concrete failure scenario (input or state → wrong output).
An empty answer is a failure: if you find nothing, list the attacks you ran.
Under 400 words.
```

**Done when:** five reports are in, or a dead lens is named for §7.

### 3. Grade

Reproduce each finding, then grade it by **impact** against the base. A **nit** changes
nothing a reader or a run depends on. Everything else is a **defect**, a one-character boundary
bug included. When the parent's grade differs from the lens's, the inventory records both.

Fix nits on the spot and list them; they reopen nothing. A nit in a queue file goes through
the queue's one writer.

**Done when:** every finding carries a grade the parent reproduced.

### 4. Correct and re-lens

Defects force a **correction batch**: fix each one, or reject it with a reason specific to the
finding, recorded in the inventory. A recorded rejection stays rejected in later rounds; a lens
re-raising it reopens the rejection with the user, not the loop.

Then **re-lens the finders**: exactly the lenses that found a defect, against the batch. Add a
lens when a correction enters ground no finder covered (a moved block, a new write path); from
then on it is a finder. The correction commit is a round of this campaign, never a new trigger.

The **budget** is 3 rounds, round 1 included; the mandatory review is round 0, outside it.

**Done when:** the re-lens round reported, and the campaign is at one of the states in §5.

### 5. Escalate

A round is **clean** when it produced no defect. Three stops block the merge and go to the user
with the round-by-round findings:

- **Design signal**, from round 2: two or more defects, or a mechanism an earlier round already
  found (the same guard or invariant violated, a new instance each time). An incomplete repair is
  a correction, not a signal. Before asking, the parent writes whether the artifact should exist
  as built: code only when the answer must be identical every run or fail loudly, otherwise prose
  in a skill. The user picks **correct and continue**, **redesign**, **cut** or **block**.
- **Ceiling**: round 3 (or any later round) not clean. The user picks **one more round**,
  **redesign** or **block**. Signal and ceiling together: the signal's menu.
- **All rejected**: every defect of a round rejected. The ceiling's menu; outranks the signal.

A **redesign** reruns the round-1 composition on the rounds left, never fewer than one; when none
remain the parent asks how many the user grants. It inherits the budget and the signal's history.
A **cut** drops the artifact; the deletion is a slice of its own, and this campaign ends blocked.
A **blocked** slice becomes a queue item carrying the findings; the user reopens it into the
next round, on the rounds they grant, with the signal's history intact.

| State | Entry | Exit |
|---|---|---|
| not fired | no item hit, or an exemption receipt | mandatory review only → merge-ready; parent fires by choice → round 1 |
| round N | trigger or parent's choice (N=1); correction batch; redesign; granted round; resumed handoff | clean → inventory; defects → correction batch, design signal (N≥2), all rejected, or ceiling (N≥3) |
| correction batch | a round with defects, none escalated | re-lens the finders → round N+1 |
| design signal | round N≥2: 2+ defects, or a repeated mechanism | correct and continue → correction batch; redesign → round N+1; cut or block → blocked |
| ceiling | round N≥3 not clean | one more round → round N+1; redesign → the rounds granted; block → blocked |
| all rejected | every defect of a round rejected | as at the ceiling |
| waiting for window | the campaign does not fit the remaining window (§7) | next window → round N, unchanged |
| handed off | the window ends mid-campaign | next session re-fires the named pending round |
| blocked | the user's pick | queue item with the findings; the user reopens → round N+1 |
| clean | a round with no defect | attack inventory → merge-ready |

**Done when:** the slice is merge-ready, blocked, waiting or handed off, and the PR says which.

### 6. Close

A clean round ships the **attack inventory**:

- the attacks run and the artifacts touched;
- every finding of every round: its guard or invariant, its grade (both, when they differed),
  its fix or its recorded rejection;
- the ground the corrections opened, with the lens added or declined.

An empty or one-line inventory is a failure, not approval. Merge stays with the user.

**Done when:** the inventory is in the PR body, and every finding of every round appears in it.

### 7. Window and handoff

A campaign costs at least as much window as the implementation; that floor is the plan's review
line. Campaigns serialize: one starts only when the remaining window fits it and every campaign
already running. One that does not fit waits whole, as a queue item heading the next window's
review line; the slice stays implemented, unreviewed, unmerged.

A handoff mid-campaign names the pending round, the lenses that reported and the lenses that
died. The partial round has not run: the next session re-fires every lens of that round, and the
reports it inherits are context, not findings. Unattended, findings and verdicts land on the
slice's PR or on the item's handoff briefing.

## Why

- **Five lenses with distinct prompts, picked per slice.** They keep finding what two fixed axes
  approve: thirteen defects headed for main in nineteen campaigns over code and data.
- **Re-lens the finders, not a fixed count.** The fix is new code nobody reviewed; pointing the
  finders at it has caught a defect born in the repair six times running.
- **A repeated finding is a design signal, not a coverage gap.** Another round on the same
  mechanism buys a new instance of the same defect; the question is whether the artifact should
  exist as built.
- **Prose gets the mandatory review only.** Four campaigns over the rule's own prose found zero
  defects that would have reached main, at 2.1–2.3M tokens; a lens over prose produces prose.
