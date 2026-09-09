# Where an unattended finding goes

Read from `AFK.md` beside this file, at any step, by the ORCHESTRATOR.
`../../reference/session-finding.md` defines the term and carries both ladders, attended and
unattended; the unattended one's second rung points here. This file decides which VEHICLE a
finding takes, never whether the finding survives.

**No new queue item is born while a package runs.** The hydra is measured, on the queue this rule
was written against. Of the 110 open items, 74 — 67% — were born in seven days, every one of them
out of a review campaign or an afk package. 43 of them name a review mechanism in their own
`Source:` line, and one package left 11 items behind 5 slices. The mechanical refusal already exists — the WIP
cap, and the hook that asks before an `add` — and what this file retires is the rung that kept
feeding it.

Nothing is discarded here, because discard is the user's judgement and stays theirs. The finding
changes vehicle instead, and the vehicle is one of the three below.

## The three destinations

Read them in order and take the FIRST that holds. The choice is made at the moment of discovery,
with the rest of the package still to run.

1. **A correction commit, inside the lane's scope.** The finding reproduces in the diff this lane
   owns, and a run can check it. It goes to a `fixer` under `AFK.md`'s *The fixer cap*, committed
   where that file's *The lane's tail* puts a fix. The commit is its whole trace.
2. **A line in the pull request's body, under "Achados não tratados".** The lane's diff no longer
   holds the finding, or the cap is spent, and the pull request is there to carry it. The line
   names the defect, the file and what the lane's scope could not reach, so the reader acts
   without reopening the session. `LANE-CONTRACT.md` beside this file owns that section's format.
3. **A sweep lane over the UNION of the package's pull requests, still inside the package.** The
   finding repeats across lanes, or destination 2 would hand it to nobody. Dispatch it as any
   other lane, under `LANE-CONTRACT.md`, and cut it over the union of what the package opened.
   The union is the point: one lane's branch does not hold a defect the package spread across
   several.

**A report line is not a destination.** "Linha de relatório é adiamento com outro nome" — the
user's verdict, 2026-09-06. A finding written down for a reader nobody asked to act is a
deferral, and that deferral is invisible to every count the close makes.

## The one exit that leaves the package without code

Only a NAMED human decision takes it. Park the finding: a DECISION carrying `--deferred afk`, its
branch pushed, and the handoff of `WINDOW.md` written. That `add` is REFUSED at `max-open-items`
past every flag — fold with `edit --text` or `handoff`, never by closing an item to make room.
The package never waits on a parked finding.

At the close, never mid-package, ONE `AskUserQuestion` batches every parked DECISION. The
report comes out FIRST, and the question then quotes its **What changed** lines
(`../wrap-up/REPORT.md`). Portuguese, these labels verbatim:

- `O que é:` the item or pull request in plain words, never a bare `T123` or `#n`;
- `O que muda para você:` what each option means for the user;
- `Se você não responder:` the default the agent takes, and when.

## Before the first run: the audit's own moment

`AUDIT.md`'s **backlog** outcome routes here from a moment the three destinations above cannot
reach. The wave audit stands between the claim and the first run, so there is no lane, no pull
request and no union of pull requests to put anything into. Two destinations hold there, and
neither is the queue. A finding that reshapes what the package will run goes into the **wave's
plan** — the package the orchestrator is about to dispatch. A finding belonging to one ticket goes
into that **ticket's own body**, edited as the **resolve here** outcome edits it, recording what
the text said before.

REGRILL is not this exit. It halts the package with no run fired, so the `add` its recipe prints
is the one item the rule above does not forbid. No package is left to give the finding a vehicle.

**Done when:** every finding of the package names, in the close, the destination that took it;
the parked ones are in one question, with the veto
`tk-queue cancel "<id>" --dir "<queue dir>" --why "<the veto>"`.
