# The window: the quota wall and orchestrator generations

Two ceilings end an unattended package before its work does. The **quota wall** is the
rolling usage window running out; the **context ceiling** is the orchestrator's own window
filling. Neither is a failure to recover from. Both are arrivals to be ready for, and
readiness is the same three things every time: the tree is pushed, the handoff is current,
and the claims say which items belong to this package.

Read this file at package open, beside `AFK.md`. Every rule here fires at a moment nobody
gets to choose.

## The checkpoint invariant

**Dispatch a review only over committed, pushed work**, and hold the same rule at every seam
of the package — a run verified, an item closed, an audit returned. It is the cheapest of the
three, and it is what makes the other two worth writing.

The subagent's half of the invariant is generated, not written here: the role table in
`../../reference/subagent-policy.md` carries a `checkpoint` cell, and `../../bin/tk-contract`
puts the invariant in the block of every role marked `required`. Dispatching with a block
generated per run is therefore how a run gets told; there is nothing to add to the prompt.

What collects on it: on 2026-08-18 the wall landed mid-dispatch and killed the five runs then
in flight. What survived was exactly what had been committed and pushed.

## The wall

**Read the quota before dispatching, not only after it fails.** `../../bin/tk-quota` prints
what is left of the rolling windows — `5h 63% used, 1h21m left · 7d 61% used, 4d11h left` — and
it is the only way an agent has of knowing: the percentages reach the statusline script at
render time and are written to no transcript (measured 2026-09-03 across 302 files: zero
occurrences). A package whose remaining items cost more than the window has left is a package
planning its own wall, and the cheapest moment to know that is the cut.

It **exits 2 rather than report a figure it cannot vouch for**, and two independent things can
make it unvouchable. The window may have RESET, its `resets_at` now past. Or the reading may
belong to a **previous window** — the sidecar is written only while a session renders a statusline, so a
stretch nobody sat through leaves an old reading in place, and the weekly window stays open for
seven days, which is how long a wrong figure can look current. **A reading that survives both
and is still old SAYS SO**: `(read 4d02h ago)` on the line means nothing has rendered since, so
the percentage is a floor on what has been spent, never the current figure.

**Exit 0 can still be a partial answer: it prints one window where it can only vouch for one.**
The line, on **stdout**, carries what survived; **stderr** names what did not, and why. A seam
reading stdout alone sees a shorter line and no error — so read what it refused before treating the
line as the whole picture. Where the window it refused is the one the decision needed, the seam
owes what *Generations* owes without a context number: judgement, said aloud as judgement.
Asking the user for the statusline's limits line is the other way, where there is a user to ask.
Exit 64 is a mistyped flag, never a missing number.

The wall announces itself twice — a dispatched run comes back a **terminal failure**, and the
error text names the moment the window resets. Both matter. A run the wall killed delivered
nothing and refuted nothing, so it is **not** one of the three attempts `../verify/SKILL.md`
counts: charge it to the item and the wall spends an item's whole budget on a fact about the
clock.

On the first quota failure, in this order:

1. **Stop dispatching.** The runs in flight are already dead; the ones not yet sent stay
   unsent.
2. **Refresh one handoff** — `tk-queue handoff "<id>" --dir "<queue dir>" --objective "..."
   --state "..." --blockers "..."`, in the form `../verify/SKILL.md` prescribes (*Three
   attempts, then the queue*), **then run the `edit` it prints** (same file, *The item
   points at the briefing*). That warning goes to stderr at exit 0, and the wall is the
   moment nobody is watching that stream. The id is the item in flight; with nothing in
   flight, it is the head of what the package has left. One handoff, not one per item: the
   package's remaining state has a single home, and a copy per item is a copy to go stale.
   The PACKAGE's own state is `LEDGER.md` beside this file, which owns it and the lane restart.
3. **Say what is left, in `--state`.** Seven contents, because each one is something the next
   generation otherwise rediscovers by doing the work twice:
   - the items still to dispatch, in order;
   - the item in flight, and the branch its work is pushed to;
   - the reset time the error named;
   - the claims this package holds;
   - **the review still owed** — the slice, its base and the lens's angle, for a lens the wall
     killed before it reported; a lens that did not report is re-fired whole. A slice whose
     lens never ran waits implemented, unreviewed and unmerged, and says so;
   - **the large files already read, and the verdict on each.** A successor that knows a
     source is 1,500 lines and what it holds takes it distilled from a subagent; one that
     knows only "we were at 200k" reads it again at full price;
   - **the queue dir** — every `tk-queue` call the successor runs names it
     (`AFK.md`, its opening paragraph), and the successor's cwd is no evidence of it.

   **A package holding an accumulated lane owes five contents in the same field** — four of them
   new, and the fifth one of the seven above doing a second job there. The section below names them.
   A lane package's `--state` is not written until they are in it, and the successor's very first
   command cannot be composed without the first of them.
4. **Keep the claims.** They are how the next generation knows which items are its own, and
   releasing them here invites a sibling session to take work that is half done. This is the
   one place the release rule of `AFK.md` step 3 does not apply.
5. **Stop.** Report the wall, the reset time and the handoff's path.

**Done when:** the tree is pushed, one handoff carries the seven contents of step 3 — and, where
the package holds an accumulated lane, the five contents the section below names for it — the
claims are intact, and the report names the reset time.

## An accumulated lane: the five contents `--state` carries for it

A package holding a spec's accumulated lane (`AFK.md` step 3) writes five things into `--state`
for that lane. Four are additions to the seven above and the fifth is one of the seven, doing a
second job here. **`--state` gains no flag for any of them** — it is one field of prose, and the
additions are four more paragraphs inside it.

- **The lane's identity** — the address of the repository its items land in, its branch
  `spec/<m>-<slug>`, its worktree path, and its pull request's number once one exists. It is
  written when the lane OPENS (`AFK.md` step 3), not when the first item merges, because the
  successor needs it before there is a map to read: in the state where nothing has merged yet, a
  map pinning the branch would be empty, and `git -C "<path>/spec-<m>" fetch --prune origin` —
  the successor's first command — could not be composed. Only two of the four are recoverable
  from elsewhere: `<m>` from the WIP branch the second content names, and the address from the
  item's own `Repo:` field. The slug and the worktree path are recoverable from nothing. Where
  the slug alone was lost, `AFK.md` step 1's
  `git ls-remote --heads "<the item's repo address>" 'refs/heads/spec/<m>-*'` names the branch —
  the fallback, and never the contract.
- **The item→merge map** — one line per lane item that reached the branch, its `T<id>` against the
  merge commit that carried it, under the branch's pushed tip. Each line is written **after the
  push** of `AFK.md` step 5 stage 5, and before that item's `done`. That order is what makes a
  death between those two cost nothing: the tip already carries the merge, and the successor
  closes the item from the tip.
- **The item in flight** — the ticket, the branch its work is pushed to, and the stage of step 5's
  cycle it reached. The second content above already asks for the branch; the stage is this lane's
  addition, because it decides whether the successor dispatches a run for that item at all or
  takes it straight into step 5's cycle.
- **The tail's state** — which of the tail's three steps had run, what the review returned, and
  which fixes are committed and pushed. The tail (`AFK.md` step 5, *The lane's tail*) is a merge of
  `origin/main`, one review over the accumulated diff, then the suite and every lane criterion; a
  successor told only that the tail had started re-runs all three. What the review returned is the
  fifth content above read at lane scope, so a review that never reported is re-fired whole here
  too.
- **The claims** — the fourth of the seven above, written exactly as they are there and gaining
  nothing on this lane. What they gain is a second reader: they are what tells the successor that
  the branch it finds on the remote belongs to its own package rather than to a sibling, which no
  question put to the remote can answer (`AFK.md` step 3).

**The item→merge map is what the predecessor believed; the pushed tip is what is true.** A
successor closes items by reading `git log --merges` on that tip and never by reading this map,
because the map stops at the last handoff its writer got to. What the map buys is the report: it
is the only record of what the predecessor thought it had merged, and a disagreement between it
and the tip is named there.

The procedure the successor runs from this whole field is `RESUME.md`, which `AFK.md`'s
*A resumed generation starts here* enters.

## Review is a first-class consumer of the window

Budget the review as its own line, beside the implementation it reviews and never as its tail.
The lens is one agent and it fires once, so the line is one agent's window; measured
2026-08-28, that was 144k subagent tokens against a 1,534-line slice. Where the lens would
cost more window than the implementation did, the slice takes the mandatory review alone.

**The slope decides whether the next review fits, and the height alone cannot say.**
`../../bin/tk-context --curve` prints the occupancy at intervals across the session, so a
seam can read 15k a step apart from 40k a step. Measured on one orchestrator: 59k at the
open — a kickoff is born carrying the CLAUDE.md and the memory index — 113k at the cut,
154k at the first lens, 210-232k while the handoff was written.

**Reviews serialize** — one at a time per orchestrating session. So review time is a **sum**
over the package's slices, not a maximum across them, and that serialized tail is the part of
a package the wall reaches first. A package planned as though review rode along inside
implementation is a package whose last third is unfunded.

## After the reset, the package finishes and stops

A resumed package runs out the items it already claimed and ends there. The queue waits for
the next kickoff, which is the user's.

**A successor opened at a planning seam holds no claim, and its scope is the cut its predecessor
wrote into the handoff** — that package and no item beyond it. It claims that package itself, at
`AFK.md` step 3, which is the one thing this scope rule's ordinary reading does not cover.

The reason is the window it wakes into. A resumed package eats a window the user has not
opened yet, and holding it to the items already claimed puts a ceiling on that appetite that
needs no number.

## Auto-continue buys nothing unattended

Claude Code continues a session when the usage limit resets (`/config`, "Continue
automatically at usage limit"). Measured on 2026-08-18, on the version that introduced it, it
is **focus-gated**: it fires on a window-focus event, not on a timer at the reset. On a
desktop it fired when the user focused the window, ~40 minutes after the reset. In a `tmux`
session over SSH, where focus never arrives, it never fired at all.

So it is a convenience for a session someone is sitting with, and it covers **no** part of an
unattended package. Budget the wall as though the feature were off.

## The vehicle that opens the next generation

The orchestrator's skill carries `disable-model-invocation: true`, and that lock decides what
can open a successor. A subagent cannot invoke the command, so a subagent is not a generation
(`../dispatch/SKILL.md`, *Mechanism boundaries*). Two vehicles remain:

- **A scheduled fire** whose prompt points at this skill's files by path rather than by
  command name — the route that same section documents for a locked skill — naming the
  handoff to resume from. For the wall, `reset + 5 min`.
- **The user's own first line**, when they return.

Which of the two this machine has is the site's answer, in `~/.claude/tk/kickoff.md`. **Where
neither is available unattended, the handoff IS the ending**: the package stops with its state
on disk, and the next kickoff finishes it. That ending is a good one — it costs a night, and
it costs nothing else.

## Generations, and `--budget N`

`/tk:kickoff afk --budget N` (default 1) is how many orchestrator **generations** the package
may spend, this one included. At `--budget 1` the orchestrator writes the handoff and stops;
above it, a successor may be opened by a vehicle above, carrying `--budget N-1`.

The design gives up on keeping the parent sharp. The **smart zone** is roughly the first ~100k
tokens of a session, and the orchestrator measured on 2026-08-18 closed at 410k: there is no
orchestrating a package from inside the smart zone. So the package stops depending on the
parent being sharp — fine judgement goes to a fresh subagent at pinned effort, state lives
outside the session (the queue, the handoff, git), and the parent is **replaced before it
degrades** rather than nursed.

The rule, at every seam — **the cut, the `pack` confirm**, an item closed, the wall, the end of
the package:

- **Refresh the handoff.** Always, whatever the context reads — from the first dispatch on. At
  the two planning seams nothing is dispatched yet and there is nothing to refresh: the handoff
  is written there only when the threshold is crossed, and it is what crossing it buys.
- **Read the context number on purpose**, at each of those seams: `../../bin/tk-context` prints it,
  from this session's own transcript. It is not in the statusline — that is rendered to the
  user's terminal and never enters an orchestrator's context, and three generations in a row
  reported the number as estimated, unread or `n/m` while this rule asked for it. Between one API
  response and the next the reading lags the live one by about a turn, and lags it LOW, so a
  seam sitting on the threshold reads the lag as room it does not have. Across a compaction it
  does not lag: the command reads the boundary the compaction wrote, and says it did.
- **Where there is no number, the judgement says so.** `tk-context` exits 2 when it cannot
  read one. Deciding by judgement is allowed there; presenting that judgement as this rule is
  not, and the report names it as judgement. Measured 2026-09-03: a generation stopped a
  lane's tail citing this threshold two lines after writing "context at the cut: unread".
  Read afterwards from that session's own transcript, it had been at ~210-232k against a
  ceiling of ~150-200k: the call was RIGHT. A right answer wearing a rule's clothes is
  still the defect, and that is why this bullet exists rather than a ban on estimating.
- **Compare absolutes, never a fraction.** The threshold is the smart zone's edge — judgement
  degrading — and not the window running out, so it does not scale with the window's capacity.
  That is why `tk-context` prints tokens and no percentage: on a 1M-context model a measured
  293k renders as 29%, the same ceiling wearing the look of room.
- **Above the threshold**, open the next generation and end this one. It is ~100k at the two
  planning seams, for the reason the section below gives, and ~150–200k once the package has
  begun dispatching.
- **Below it**, carry on.

**That ~150–200k threshold is a simple slice's ceiling, not a slice's.** One real slice — one
`tk-queue` subcommand, 8 commits, five files — closed its session at **372k**, roughly twice that ceiling,
with no overflow and no compaction, on six correction cycles. Why a slice costs what it does
is the cut's question and has one home, in `AFK.md` step 1: correction cycles are the
multiplier there, and the same rule sizes a generation here. So read the zone as the ceiling
of a slice the audit sends round once, and expect an item it sends round more to reach the
zone early.

**Estimating the implementation before it runs**, when there is no subagent to measure: inside
a package the question does not arise, because the orchestrator implements nothing inline and
every implementation therefore has a run of its own to be measured against. Outside one — a
session implementing in the parent — the measure is that parent's own context delta across the
slice, read at the same close-of-item point as above. Carry the delta into the handoff; it is
the only number a successor can plan the next slice from.

Generations are **sequential**: one orchestrator at a time, so the single-writer rule over the
queue survives, and the claims pass to the successor inside the handoff. One package, one live
orchestrator.

**Write the handoff rather than compacting.** An auto-compacted orchestrator carries a machine
summary of a long context; a fresh one carries a briefing its predecessor wrote on purpose,
against a contract, with the queue and git behind it. The second is strictly better, and
writing it is already step 2 of the wall.

### The two planning seams

The cut (`AFK.md` step 1) and the `pack` confirm (step 2) are the seams a package has before it
dispatches anything, and a session that fattens while planning closes no item, so every other
seam on the list is out of its reach. Measured 2026-08-28: a `pack` reached **~130k at the cut
with zero items dispatched**, leaving 20–70k — about one item — for the whole package. `afk`
has no step 2, so the cut is its only planning seam; the enumeration above covers both modes
with no special case. The confirm earns its place on the `pack` path by being the **last seam
before any claim**, and because the round of questions after the cut is not free: a checkpoint
at the cut alone is blind to it.

**The threshold here is the smart zone's edge, ~100k** — the number this file already declares,
borrowed rather than recomputed. Reading ~150–200k at a planning seam would authorise exactly the
session that failed. Like the cut's own sizes in `AFK.md` step 1, it is an **opening bid**: step
6 measures what planning cost this package, and the next cut reads that line.

**Over the threshold at a planning seam, the action is not the wall's.** Nothing is claimed yet,
so *The wall*'s fourth step — keep the claims — has nothing to keep, and claiming here would
leave an orphan claim every later package refuses. Under the threshold the seam costs one
`tk-context` and nothing else. Over it:

1. **Record the triage through `tk-queue`** — `add`, `edit`, `cancel` — so the verification
   against reality and the re-triage survive the session that paid for them.
2. **Write one `tk-queue handoff` on the head item**, in the form `../verify/SKILL.md`
   prescribes, and run the `edit` it prints (same file, *The item points at the
   briefing*). Its `--state` carries the seam this session stopped at — which is what tells
   the successor where to enter (`RESUME.md`, through `AFK.md`'s section of that name) — the cut's
   order, the context number just read, and whichever of *The wall*'s seven contents a package
   that dispatched nothing still has to say.
3. **Leave the remote as it stands.** The lane's branch opens at `AFK.md` step 3; a branch
   pushed early takes its spec out of the next package's election (`AFK.md` step 1).
4. **Hand back the line that resumes the package**, and stop. The successor opens on that
   handoff and reads no queue (`SKILL.md`, *A session opening on a package handoff*).
