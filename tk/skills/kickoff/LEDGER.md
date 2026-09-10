# The package ledger: one line per event, and the lane restart

`RESUME.md` beside this file resumes a GENERATION of the orchestrator; the recipe here resumes
one LANE, inside a generation that is still alive. The two are read at different moments and
one is not a fallback for the other: a generation that died reads `RESUME.md` first, and the
lane restart below is what it then runs per dead lane.

Read from `WINDOW.md` beside this file, by the ORCHESTRATOR. What lives here is the FORMAT and
the recipe. The ledger itself is a file of the run's own outbox, one per package, and nothing
in the skill writes it: the orchestrator appends to it as the package runs.

The ledger is the PACKAGE's and the `tk-queue` handoff is the ITEM's — thirteen lanes carry
thirteen live states at once, and one item's briefing is not their home — and the queue's
single-writer rule does not change. Nothing here is written by running a queue command.

What it bought, measured on the package of 05-07/09/2026: the ledger survived two compacts and
three quota walls, and restarting a dead lane from it cost a prompt of twelve lines. Of the
four lanes the first wall killed, four closed with a pull request.

## The event line

One line per event, appended, never edited once written. Seven fields, pipe-separated:

```
<hh:mm> | <lane> | <agent> | <model> | <event> | <result> | <quota>
```

- **`<hh:mm>`** — the hour, READ and never counted. The rule and what it cost are below.
- **`<lane>`** — the lane the event belongs to, by the name its row carries in the state
  table. `(orquestrador)` for the orchestrator's own acts, `(sistema)` for a wall nobody
  dispatched.
- **`<agent>`** — the role dispatched, by the name it has in
  `../../reference/subagent-policy.md`. A role name is what lets a later reader ask
  `tk-contract` what that run was handed.
- **`<model>`** — model and effort as DISPATCHED, `opus/high`, not the role's default. The
  default is in the policy file; what a run actually got is only here.
- **`<event>`** — what was dispatched or observed, in one clause.
- **`<result>`** — what came back: the pull request number, the branch and the commits
  pushed, the reason it died, or `-` while it is still running. A line written at dispatch
  and a line written at return are two lines, each with its own hour.
- **`<quota>`** — the line `../../bin/tk-quota` printed, pasted whole, or the tick's own
  reset-anchored floor said as one. Its own section below, with the invocation each shape needs.

**Every hour is read from `date`, never counted in the head.** Run `date '+%H:%M'` and paste
what it printed. Four lines of that package's ledger were written from the orchestrator's own
sense of elapsed time and were an hour wrong. They were caught and corrected from the
transcripts hours later, and until then every rate computed off them was wrong by the same
hour. The rate below is a difference between two hours, so an estimated hour does not
merely misdate a row: it corrupts the only sensor the package has.

## The quota field: a reading and a floor are not the same claim

Paste the line the bin printed and never a percentage retyped from it. Which invocation depends
on what the field is claiming: bare `../../bin/tk-quota` for a reading,
`../../bin/tk-quota --estimate --opus <n>` for a floor. The lines say different things, and each
says which it is:

- a READING — `5h 63% used, 1h21m left`, and past ten minutes `(read 1h00m ago)` beside it;
- a FLOOR — `5h estimate: at least 91% used, 2h09m left (floor from 41% read 1h00m ago,
  50 pp/h = 5 Opus x 10)`, which carries the word `estimate`, the qualifier `at least`, the
  anchor's own percentage, the anchor's AGE, and the rate applied. It speaks for the 5h
  window alone: no rate was ever measured for the weekly one, and the bin says so on stderr.
  A floor may only ever FORBID a dispatch and never authorise one — `../kickoff/WINDOW.md`
  owns that rule, and this file does not restate it;
- a RESET-ANCHORED FLOOR — the same `--estimate` invocation, where the window's reset has
  already passed with nobody rendering since. The READING stays refused; the boundary the
  sidecar carries does not, so the bin anchors 0% at that reset and climbs from there:
  `5h reset-anchored floor: at least 20% used (0% at the 20:30 reset, 1h00m ago,
  20 pp/h = 2 Opus x 10)`. The words `reset-anchored floor` and the anchor `0% at the <hh:mm>
  reset` are what keep it from reading as either line above. Past one whole window the bin
  refuses instead — the window that opened at the anchor may itself have reset, and no floor
  spans both. With no sidecar at all it prints nothing, and a floor the tick then computes by
  hand carries `computed by the tick` beside those words, because that one no bin vouched for.

**A bare number in this field is refused**, because nothing downstream can tell the three apart
once the words are gone. What that costs is measured: one reading 1h25m old said 8% while the
account stood near 70%, and the ledger lines written from it read as current.

The rate is recalibrated per package FROM this file: two lines, their hours, their anchors'
percentages. It started at 50-65 pp/h with five live Opus agents on the package above. A rate
carried over from another package is an assumption, and it is named as one in the line.

## The state table

One row per lane, rewritten in place. The event lines are the history; this table is the
present, and it exists so the orchestrator can say who is standing without asking anyone.

```
| lane | repo | worktree | branch | state |
```

The `state` cell takes one of four, in the order a lane passes through them:

1. **alive** — a run is dispatched and has not returned. The cell names the run's model.
2. **pull request open** — the lane returned and opened one, `#<n>`; nothing reviews it yet.
3. **review dispatched** — a cold review is running over that pull request.
4. **verdict** — the review reported. The word is the colour `REVIEW-CONTRACT.md` beside this
   file assigns, and this table takes it from there rather than minting one of its own.

A lane whose run died has no fifth state: it goes back to **alive** when the restart below is
dispatched, and the death is an event line, where its hour and its quota reading are.

## The lane restart

The prompt that resumes one dead lane. It reconstructs nothing: what the lane did is on the
remote, and why it stopped is in the ledger. Fill the slots and paste it.

```
RESUME.md resumes the orchestrator's GENERATION; this resumes one LANE of a live generation.
You RESUME lane <lane> of package <package>. Nobody is watching; ask nobody.
Contract: <path to>/tk/skills/kickoff/LANE-CONTRACT.md — read it whole first; it binds you.
Worktree <path>/<lane>, branch <branch>, pushed. Do not recreate it and do not reset it.
Delivered already: run `git log --oneline "origin/main..HEAD"` there and read it. Reconstruct
nothing else — the remote is the record.
In progress: run `git status --porcelain`. Inspect that diff: keep it if it is coherent, else
`git checkout -- .` and redo that slice whole.
Still to do, in order: <the remaining item ids>. Their full text: <items file>.
Ledger: <ledger file> — your lane's rows say why the last run stopped. Write none of them.
Base notes: <notes dir>. Suite: <the suite command>, FOREGROUND, timeout 900.
One slice = one commit, pushed. At the end ONE pull request, per the contract. Never merge.
Contract block, pasted verbatim from `tk-contract --role lane-implementer`: <the block>
Report back: the pull request URL, per item DONE / PARTIAL / NOT DONE, and the suite numbers.
```

**Done when:** every dispatch and every return is a line with an hour read from `date`, and
every quota field is a line the bin printed — or, for the reset-anchored floor alone, one the
tick computed and marked as computed — with its nature and, being a floor, its
anchor's age. The state table has one row per lane. A successor restarting a lane needs this
file and the remote, and nothing that was in the session.
