# The window: the quota wall and orchestrator generations

Two ceilings end an unattended package before its work does. The **quota wall** is the
rolling usage window running out; the **context ceiling** is the orchestrator's own window
filling. Neither is a failure to recover from. Both are arrivals to be ready for, and
readiness is the same three things every time: the tree is pushed, the handoff is current,
and the claims say which items belong to this package.

Read this file at package open, beside `AFK.md`.

## The checkpoint invariant

**Dispatch a review only over committed, pushed work**, and hold the same rule at every seam
of the package — a run verified, an item closed, an audit returned.

The subagent's half of the invariant is generated, not written here: the role table in
`../../reference/subagent-policy.md` carries a `checkpoint` cell, and `../../bin/tk-contract`
puts the invariant in the block of every role marked `required`. Dispatching with a block
generated per run is therefore how a run gets told; there is nothing to add to the prompt.

## The wall

**Read the quota before dispatching, not only after it fails.** `../../bin/tk-quota` prints
what is left of the rolling windows — `5h 63% used, 1h21m left · 7d 61% used, 4d11h left` — and
it is the only way an agent has of knowing: the percentages reach the statusline script at
render time and are written to no transcript. A package whose remaining items cost more than
the window has left is a package planning its own wall, and the cheapest moment to know that is
the cut.

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

**The wall arrives in one of two shapes, and only one of them leaves a turn to act in.** A
dispatched run comes back as that terminal failure, and the orchestrator's own turn survives to
run the five steps below. A rejection that lands on the orchestrator's OWN thread — the tick's
turn, between one tool call and the next — ends that turn where it lands, and nothing below
runs. What covers that shape is the handoff the last seam already wrote, which is why
*Generations, and `--budget N`* asks for one at every seam rather than at the wall alone.

On the first quota failure, in this order:

1. **Stop dispatching.** The runs in flight are already killed, and the ones not yet sent stay
   unsent. Under the Agent-tool fallback, the tick resumes the killed runs after a 5-hour reset
   (*Who meets the wall on the main thread is the tick*).
2. **Refresh one handoff** — `tk-queue handoff "<id>" --dir "<queue dir>" --objective "..."
   --state "..." --blockers "..."`, in the form `../verify/SKILL.md` prescribes (*Three
   attempts, then the queue*), **then run the `edit` it prints** (same file, *The item
   points at the briefing*). That warning goes to stderr at exit 0, and the wall is the
   moment nobody is watching that stream. The id is the item that closes LAST, never the item in
   flight: `AFK.md` step 5 owns that rule, and names what a handoff on the head item costs at the
   first close. One handoff, not one per item: the package's remaining state has a single home,
   and a copy per item is a copy to go stale.
   The PACKAGE's own state is `LEDGER.md` beside this file, which owns it and the lane restart.
   **This step is best-effort**, for the two shapes above: it is reached where the failure came
   back as a tool result, and where the turn ended first the last seam's handoff IS the wall's.
3. **Say what is left, in `--state`.** Eight contents, because each one is something the next
   generation otherwise rediscovers by doing the work twice:
   - the items still to dispatch, in order;
   - the item in flight, and the branch its work is pushed to;
   - the reset time the error named;
   - the claims this package holds;
   - **the review still owed** — the slice, its base and the lens's angle, for a lens the wall
     killed before it reported. That lens is resumed first (*Who meets the wall on the main
     thread is the tick*), and re-fired whole only where no agent answers or it shows no work.
     A slice whose lens never ran waits implemented, unreviewed and unmerged, and says so;
   - **the large files already read, and the verdict on each.** A successor that knows a
     source is 1,500 lines and what it holds takes it distilled from a subagent; one that
     knows only "we were at 200k" reads it again at full price;
   - **the queue dir** — every `tk-queue` call the successor runs names it
     (`AFK.md`, its opening paragraph), and the successor's cwd is no evidence of it;
   - **the workflow's resume handle**, where the dynamic workflow of `AFK.md` step 3 is the
     vehicle: the script's path, the run id, the file the `args` were written to, and the
     transcript directory holding that run's record and its journal — and whether the run was
     still in flight when the handoff was written. Resuming a workflow across sessions is
     unmeasured, so the successor reads the lane's pushed tip and that journal, and treats the
     item→merge map below as EMPTY: what a dead run merged is on the tip or nowhere.

   **A package holding an accumulated lane owes five contents in the same field**, which the
   section below names.
   A lane package's `--state` is not written until they are in it, and the successor's very first
   command cannot be composed without the first of them.
4. **Keep the claims.** They are how the next generation knows which items are its own, and
   releasing them here invites a sibling session to take work that is half done. This is the
   one place the release rule of `AFK.md` step 3 does not apply.
5. **End the turn, claims kept.** Report the wall, the reset time and the handoff's path. Where
   the session wakes on a line carrying `origin.kind: "auto-continuation"`, that line is a seam
   like any other: re-read the current handoff and carry on, under the budget the package
   already held. **Which handoff that is follows the shape** — the path this step reported, or,
   where the turn ended before this step ran, the one the last seam wrote. Where it does not
   wake, the state is on disk and the next kickoff finishes the package. Plan for the second
   (*Auto-continue is a fail-safe, never a plan*). On a 5-hour wall, the tick's first fire after
   the reset resumes the runs (step 1) and the package continues. Auto-continue and the next
   kickoff cover a lost tick; the next kickoff alone covers the weekly wall, which deletes the
   tick (*The tick*).

**Done when:** the tree is pushed, one handoff carries the eight contents of step 3 — and, where
the package holds an accumulated lane, the five contents the section below names for it — the
claims are intact, and the report names the reset time.

## An accumulated lane: the five contents `--state` carries for it

A package holding a spec's accumulated lane (`AFK.md` step 3) writes five things into `--state`
for that lane. Four are additions to the eight above and the fifth is one of the eight, doing a
second job here. **`--state` gains no flag for any of them** — it is one field of prose, and the
additions are four more paragraphs inside it.

- **The lane's identity** — the address of the repository its items land in, its branch
  `spec/<m>-<slug>`, its worktree path, and its pull request's number once one exists. It is
  written when the lane OPENS (`AFK.md` step 3), not when the first item merges: the
  successor's first command, `git -C "<path>/spec-<m>" fetch --prune origin`, needs it before
  anything has merged. Only two of the four are recoverable
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
  fifth content above read at lane scope, so a review that never reported is resumed first and
  re-fired whole only as that content says, here too.
- **The claims** — the fourth of the eight above, written exactly as they are there and gaining
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
The lens is one agent and it fires once, so the line is one agent's window. Where the lens would
cost more window than the implementation did, the slice takes the mandatory review alone.

**The slope decides whether the next review fits, and the height alone cannot say.**
`../../bin/tk-context --curve` prints the occupancy at intervals across the session, so a
seam can read 15k a step apart from 40k a step.

**Reviews serialize** — one at a time per orchestrating session. So review time is a **sum**
over the package's slices, not a maximum across them, and that serialized tail is the part of
a package the wall reaches first.

## After the reset, the package finishes and stops

A resumed package runs out the items it already claimed and ends there. The queue waits for
the next kickoff, which is the user's.

**A successor opened at a planning seam holds no claim, and its scope is the cut its predecessor
wrote into the handoff** — that package and no item beyond it. It claims that package itself, at
`AFK.md` step 3, which is the one thing this scope rule's ordinary reading does not cover.

The reason is the window it wakes into. A resumed package eats a window the user has not
opened yet, and holding it to the items already claimed puts a ceiling on that appetite that
needs no number.

## Auto-continue is a fail-safe, never a plan

Claude Code can resume a session at the usage limit's reset (`/config`, "Continue automatically
at usage limit"). It is **timer-driven**: the scheduled resumption carries a fire time of the
reset plus a jitter, polled every 30 seconds. It fired **87 seconds after the reset** with
nobody at the keyboard and no key pressed.

**Only a real rejection schedules it** — the window spent to 100% by work in flight, mid-turn.
So an orchestrator that reads `../../bin/tk-quota`, sees one of *The tick*'s floors and stops
clean schedules nothing at all, and the two disciplines do not compose: the floors keep a
package off the wall, and this fail-safe exists for the package that reached it anyway.

**Plan the package as though it will not fire.** Four limits switch it off, and from inside the
session nothing says which of them holds:

- a horizon of 24 hours, which leaves the WEEKLY window out entirely, so that window keeps the
  procedure the rest of this file gives;
- an exhausted cap, after repeated resumptions;
- a poll gap wide enough to leave the scheduled resumption stale, which asks for a keypress
  instead;
- cancellation by a background handoff, a relaunch, a process exit, `escape` or `ctrl-c`.

Whether the harness warns a session that it will NOT resume is unmeasured: plan without that
warning.

**Who meets the wall on the main thread is the tick.** A workflow in flight has a quota wait of
its own and re-runs its parked agents after the reset, so the wall does not come back to the
script as a `null`; it is the tick's own turn that takes the rejection. Ticks that queued while
the window was spent arrive together at the resumption, so a resumed turn opens holding several
tick prompts and runs ONE tick over them all.

**Under the Agent-tool fallback** (`AFK.md` step 3, *The vehicle*), **the tick resumes what the
wall killed**, which keeps its context and its uncommitted worktree edits. At each fire where
`tk-quota` reads the 5-hour window live and with room — not refused, not spent — send ONE
`SendMessage` to every dispatched agent that has neither handed back nor is running.
`ListAgents` rows name the agents this session spawned, by kind, with no run state; the task
notifications say which handed back. Re-dispatch whole only where no agent answers, or its
worktree shows no work.

**The marker a resumed session reads is structural, never the prose.** The resumption arrives
as a `user` line carrying `origin.kind: "auto-continuation"`, and the harness ships three
different continuation texts, so a rule matching a sentence is a rule the next release breaks.
*The wall*'s step 5 is what acts on it.

## The vehicle that opens the next generation

The orchestrator's skill carries `disable-model-invocation: true`, and that lock decides what
can open a successor. A subagent cannot invoke the command, so a subagent is not a generation
(`../dispatch/SKILL.md`, *Mechanism boundaries*). Two vehicles remain:

- **A scheduled fire** whose prompt points at this skill's files by path rather than by
  command name — the route that same section documents for a locked skill — naming the
  handoff to resume from. For the wall, `reset + 5 min`, **conditional on the predecessor being
  gone**: auto-continue may have woken that session 87 seconds earlier (*Auto-continue is a
  fail-safe, never a plan*), and generations are sequential, so the fire's own prompt reads the
  package ledger's last line and the handoff's hour first, and ends without opening anything
  where the predecessor has written since the reset.
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
tokens of a session, and a package cannot be orchestrated from inside it. So the package
stops depending on the parent being sharp — fine judgement goes to a fresh subagent at pinned
effort, state lives outside the session (the queue, the handoff, git), and the parent is
**replaced before it degrades** rather than nursed.

The rule, at every seam — **the cut, the `pack` confirm**, the dispatch of a workflow, an item
closed, the wall, the end of the package:

- **Refresh the handoff.** Always, whatever the context reads — from the first dispatch on. At
  the two planning seams nothing is dispatched yet and there is nothing to refresh: the handoff
  is written there only when the threshold is crossed, and it is what crossing it buys.
- **Read the context number on purpose**, at each of those seams: `../../bin/tk-context` prints it,
  from this session's own transcript. It is not in the statusline — that is rendered to the
  user's terminal and never enters an orchestrator's context. Between one API
  response and the next the reading lags the live one by about a turn, and lags it LOW, so a
  seam sitting on the threshold reads the lag as room it does not have. Across a compaction it
  does not lag: the command reads the boundary the compaction wrote, and says it did.
- **Where there is no number, the judgement says so.** `tk-context` exits 2 when it cannot
  read one. Deciding by judgement is allowed there; presenting that judgement as this rule is
  not, and the report names it as judgement.
- **Compare absolutes, never a fraction.** The threshold is the smart zone's edge — judgement
  degrading — and not the window running out, so it does not scale with the window's capacity.
  That is why `tk-context` prints tokens and no percentage: on a 1M-context model a measured
  293k renders as 29%, the same ceiling wearing the look of room.
- **Above the threshold**, open the next generation and end this one. It is ~130k at the two
  planning seams, for the reason the section below gives, and ~150–200k once the package has
  begun dispatching.
- **Below it**, carry on.

**That ~150–200k threshold is a simple slice's ceiling, not a slice's.** Why a slice costs what
it does is the cut's question and has one home, in `AFK.md` step 1: correction cycles are the
multiplier there, and the same rule sizes a generation here. So read the zone as the ceiling
of a slice the audit sends round once, and expect an item it sends round more to reach the
zone early.

**The dispatch of a workflow is a seam, and its handoff is written right AFTER the launch** —
the script's path, the run id and the args file do not exist before it. Between that launch and
the return the orchestrator holds no seam at all: none of the graph is its own turn. *The tick*
below is what
reads `../../bin/tk-quota` there; where no tick is armed, the orchestrator reads it at every
wakeup until the workflow returns.

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
seam on the list is out of its reach. `afk` has no step 2, so the cut is its only planning
seam; the enumeration above covers both modes with no special case. The confirm earns its place on the `pack` path by being the **last seam
before any claim**, and because the round of questions after the cut is not free: a checkpoint
at the cut alone is blind to it.

**The threshold here is ~130k** — the smart zone's edge plus the ~78k a kickoff is born
carrying. Like the cut's own sizes in `AFK.md` step 1, it is an **opening bid**: step
6 measures what planning cost this package, and the next cut reads that line.

**Over the threshold at a planning seam, the action is not the wall's.** Nothing is claimed yet,
so *The wall*'s fourth step — keep the claims — has nothing to keep, and claiming here would
leave an orphan claim every later package refuses. Under the threshold the seam costs one
`tk-context` and nothing else. Over it:

1. **Record the triage through `tk-queue`** — `add`, `edit`, `cancel` — so the verification
   against reality and the re-triage survive the session that paid for them.
2. **Write one `tk-queue handoff` on the item that closes last** (`AFK.md` step 5 names it), in
   the form `../verify/SKILL.md` prescribes, and run the `edit` it prints (same file, *The item
   points at the briefing*). Its `--state` carries the seam this session stopped at — which is
   what tells the successor where to enter (`RESUME.md`, through `AFK.md`'s section of that
   name) — the cut's order, the context number just read, and whichever of *The wall*'s eight
   contents a package that dispatched nothing still has to say.
3. **Leave the remote as it stands.** The lane's branch opens at `AFK.md` step 3; a branch
   pushed early takes its spec out of the next package's election (`AFK.md` step 1).
4. **Hand back the line that resumes the package**, and stop. The successor opens on that
   handoff and reads no queue (`SKILL.md`, *A session opening on a package handoff*).

## The tick, and what one fire may dispatch

*The wall* above is an arrival to be ready for. This section is what keeps it from arriving.
The mechanism is a **tick**: a recurring scheduled fire, hourly (the package it was measured
on fired every ~47 minutes), that reads the quota, asks who is still alive, dispatches whatever
the budget below allows, checks the claims, and writes one line of the package ledger.

**The tick is periodic and never aimed at the reset.** The resets observed across that
package were 15:20, 20:30, 01:40 and 06:50 — five hours from the window's own first request,
not a fixed grid — and a cron written at 22:20 for a fixed hour missed every one of them.

**The tick is armed by work in flight, and deleted by its absence.** Every tick prompt opens
with the marker `tk-tick`, and a turn finds the tick by `CronList` and that marker.

- **Arm.** An unattended orchestrator running on the session's main thread — an afk package, a
  fleet — arms the tick before the turn that first puts background work in flight ends. Where
  `CronList` shows no marked job, run `CronCreate` with `cron: "7 * * * *"` (hourly, off the
  minute) and `recurring: true`; the tool takes nothing else. A recurring job auto-expires
  after some days, so a package that outlives it re-arms at its next seam. A successor
  generation re-arms on open when its handoff names work in flight. An attended session arms
  nothing.
- **A project run a fleet dispatched arms nothing.** A cron created inside a subagent fires only
  into it and is dropped when it ends. The fleet's tick resumes the project run by
  `SendMessage`; the resumed run resumes its own agents the same way (`ListAgents` lists only
  agents you spawned).
- **Its prompt is self-contained**, since a fire opens with no file in view. At arm time,
  resolve its paths to ABSOLUTE, as `../fleet/SKILL.md` §4 item 2 does: `tk-quota`,
  `tk-context`, and this file by section. After the marker it runs, in order: `tk-quota`; the
  resume rule (*Who meets the wall on the main thread is the tick*); the floors and the claims
  check (*The tick, and what one fire may dispatch*); `tk-context --window` (*The scheduled
  context refresh*); one ledger line.
- **Nothing in flight** is three empty answers: no dispatched agent running or awaiting
  resumption (`ListAgents`, the task notifications), no workflow running (its status, by the
  handoff's run id), and no claim held by a dispatched run (the claims check).
- **Delete the tick** when a fire or a turn finds nothing in flight — the package or the fleet
  closed, `ESPERANDO-HUMANO` below — and on a WEEKLY wall once the handoff is written: a reset
  days away is not waited on by firing. Run `CronList`, match the marker, and `CronDelete` that
  id. Then write one ledger line and end the turn.
- **Recurring, never a chain of one-shots.** A one-shot whose own turn the wall rejects never
  reaches its re-arm, while a recurring cron's fires queue through the wall and arrive together
  at the resumption.
- **Cost.** An idle fire costs about one turn (*An idle tick costs ONE turn*, below).

Four numbers bound what a fire may dispatch. Each is calibrable, and each carries what
measured it.

- **How many Opus agents run at once is the site's number, not this file's.** It is
  `max-local-opus` in `~/.claude/tk/env`, which `../../bin/tk-contract` reads into the block
  of every dispatched run as *Opus subagents*; a ceiling written into prose here is a fork of
  the policy (`../fleet/SKILL.md` §3). **The two ceilings are different axes and are not one
  number.** `max-local-subagents` is the RAM one — its site value was measured on five
  parallel Sonnet runs, and `tk-contract` emits it as *Local subagents* — while
  `max-local-opus` is the QUOTA one, and it counts Opus agents in EITHER venue, since a cloud
  run buys RAM and not quota. This budget is authorised by `max-local-opus` and by nothing
  else: a fire that would put one more Opus agent in flight than that key allows waits,
  whatever the RAM ceiling says, and where the site file carries no `max-local-opus` the
  block states no number, which is a decision to take and log rather than a ceiling to read
  off the other key. What the weekend measured is why: with five live Opus agents the 5-hour
  window went 20→41% in 25 minutes (~50 pp/h) and 56→70% in 14 minutes (~60 pp/h), which
  spends a whole window in a little over two hours. **T270 is the sibling measurement** that
  recalibrates `max-local-subagents` against the same ledger; this file names it and does not
  duplicate it.
  **The RAM axis is READ at each fire, and the site key is what it falls back to.**
  `../../bin/tk-ram` reads this container's own cgroup — `memory.max`, less a reserve, less
  `anon` and `memory.swap.current` — divides that by the 0.74 GiB an agent was measured to
  cost, and prints the fit, clamped to `[1, 3]`. A fire dispatches no more LOCAL runs than that
  line allows, whatever the site key holds: the key is one moment's occupancy written down,
  and the occupancy is what moves between packages. The running agents'
  memory is already in `anon`, so the fit bounds what this fire ADDS, never what may be
  alive at once. **A printed `1` may be the floor and not a fit.** The bin never prints 0 —
  dispatching nothing is the quota floor's verdict and the wall's — so where its stderr says
  the raw fit was at or below zero, the fire dispatches nothing local and the ledger line
  carries that stderr line beside the number. The line it printed goes in the package
  ledger's `<event>` field, so that a later reader can tell a reading from a default. Where the bin refuses — exit 2 — `max-local-subagents` is the
  number and the ledger line says the reading failed. **The harness's own low-memory warning
  does not cover this**: 2.1.274 reads `/proc/meminfo`, which inside a container is the
  HOST's, and is blind to the cgroup that actually kills the run.
- **Nothing at all is dispatched below 15% of the window remaining.** A run the wall kills
  before its first commit delivered nothing and refuted nothing, and the item pays for it
  anyway (*The wall*).
- **No review is dispatched below 35%.** Measured twice in one package: a wall killed a
  review with BOTH axes already answered, and re-fired whole, the triage — the expensive half —
  was lost, ~150k tokens thrown away each time. A review resumed by `SendMessage` keeps its
  context (*Who meets the wall on the main thread is the tick*). Where a package refuses that
  floor, the alternative is a review that commits its raw findings to a file before it triages.
- **A review is 25 to 45 minutes**, measured over that same package, which is what makes it
  the thing that fits a short slot where a lane does not fit. The hour before a reset is a
  review's hour and not an idle one.

**The claims are checked by script at every fire, and never from memory.** The tick crosses
`tk-queue list --dir "<queue dir>"` with the five lists of `ROOT-CAUSE.md` for that run, and
names two divergences: an item dispatched with no claim, and a claim with nothing dispatched
against it. It writes the missing claim before its next dispatch, and it releases the idle
claim or re-dispatches its item — and either way the divergence is a ledger line before
it is repaired.

**The quota is read through `../../bin/tk-quota`, in three modes that are not
interchangeable.** A READING is a measurement. A FLOOR — `tk-quota --estimate --opus <n>` —
is a lower bound on what has been spent, so it may only ever FORBID a dispatch and never
authorise one: "at least 41% used" is as true at 95% as at 41%. The third mode is the reset.
The bin refuses a window whose reset has passed with nobody rendering since as a READING, and
`--estimate` does not stop there, because the window boundaries are fixed and known — the
crossed one is in the sidecar. It anchors a floor of 0% at the reset it has just crossed and
counts the dispatches forward from there at the same rate. That is a floor too, and the bin
prints it as a **RESET-ANCHORED FLOOR**, the shape the package ledger admits under that name,
in words of its own and never as a reading. Past one whole window the anchor is dropped
rather than stretched: the window that opened there may itself have reset, no floor spans
both, and the tick is back to judgement and says so.

None of the four floors displaces *The wall*. They decide what is dispatched while the
window still has room; the wall's five steps are what happens when it has none, and a tick
whose own turn survives the rejection runs them unchanged. Where that turn ends first, the two
shapes *The wall* opens with say what covers it.

## The scheduled context refresh

The same tick keeps the orchestrator's own window fresh. The harness compacts on its own at
a ceiling this file does not set; what the tick owes is to have written the handoff BEFORE
that happens, so that the compacted session wakes holding a briefing rather than a summary.

**The trigger is the tick, and not a schedule of its own.** A `/compact` armed for the night
of 2026-09-06 never ran and nothing said so — a scheduled fire is exactly the mechanism that
failed.

**The ceiling is absolute, in the tokens `../../bin/tk-context` prints, and never a fraction
of the window.** That is the rule *Generations, and `--budget N`* already states for the
generation threshold, borrowed here rather than restated: on a 1M window a measured 293k
renders as 29%, the same ceiling wearing the look of room.

**Handoff or compact is decided by the site, and not by how long the package is.** Where
`~/.claude/tk/kickoff.md` names a vehicle, *The vehicle that opens the next generation*
holds and the answer is the one this file already gives: write the handoff and open the next
generation. Where it names none, the compact is what keeps ONE generation alive, and the
tick lets the harness compact rather than ending the package.

**The compact belongs to the harness, through the key `autoCompactWindow`** — settings user,
project or local; a number of tokens, or `auto` — with the environment variable
`CLAUDE_CODE_AUTO_COMPACT_WINDOW` winning over the key. Written by hand the key takes effect in
the NEXT session, because it is an option read when a session opens, and only the user's own
`/autocompact` applies it live; `auto` resolves to the model's own context, 1M on Fable,
which is nowhere near the smart zone. So this file prescribes the KEY and never a number in
prose, and an orchestrator, whose session is always new, needs only the key in its project's
own settings.

Three pieces, and the tick is the first:

1. **Before, with margin.** The tick runs `../../bin/tk-context --window`, which prints this
   session's tokens on stdout and, on a channel of its own, the window and the threshold the
   harness compacts at. Above (threshold − ~40k of margin) it runs `/tk:wrap-up afk` and
   writes the handoff, and the harness compacts afterwards by itself. The channel is
   separate so that the bare reading every other seam here does is unchanged; and an
   unconfigured key is not an unreadable session — the flag prints the harness's own
   fallback MARKED as a default and exits 0. Exit 2 still means one thing, no token number
   in the transcript, which is what *Generations* spends as its licence to judge.
   **The project settings come from the SESSION's directory**, the first `cwd` its
   transcript records. So the tick reads the same window from a worktree as from the
   project root, and the flag names that directory beside the number.
2. **At the compact**: the `PreCompact` hook, matcher `auto`, running
   `../../bin/tk-compact-mark`. It blocks nothing, decides nothing and runs no skill: it
   appends one ledger line, with the hour read and the quota field the bin printed. A
   trace. **The line is the orchestrator's own compaction and no one else's**: the hook
   fires inside every subagent too, and a subagent reports the orchestrator's `session_id`
   and `cwd`, so the bin reads `agent_id` — present only from within a subagent — and
   writes nothing when it is there. **What the guard costs**: a subagent that fills its own
   window is then traced only in its own transcript, under `<session>/subagents/`. The package's ledger
   carries no line of its own for that event: the user decided so on 22/09.
3. **After**: the `SessionStart` hook, matcher `compact`, running
   `../../bin/tk-compact-pointer`. It prints one JSON envelope, and the
   `hookSpecificOutput.additionalContext` in it is INJECTED into the new context — the only
   channel that reaches a compacted orchestrator. A paragraph printed bare outside that
   envelope reaches nobody: the harness logs the hook as having produced no payload, and the
   session starts as empty as before. What the paragraph says is: read the handoff at this
   path, then resume by `RESUME.md`. It reads `agent_id` as the bin above does: a compacted
   implementer told to read the orchestrator's handoff drops its own item.

Both hooks read the package's addresses from `~/.claude/state/tk-package.json`, which the
orchestrator writes when the package opens:

```sh
mkdir -p ~/.claude/state && printf '%s\n' \
  '{"package": "<package>", "ledger": "<ledger file>", "handoff": "<handoff file>"}' \
  > ~/.claude/state/tk-package.json
```

With no such file both hooks do nothing at all, which is what lets the wiring sit in the
settings permanently: most sessions on this machine are not packages. The wiring itself is
the site's and the human's — `~/.claude/settings.json` is written by Claude Code and
versioned by snapshot — so a package that finds the hooks unwired says so in the ledger and
goes on. The refresh depends on the tick's own reading; the hooks are the trace and the
pointer around it.

**The ceiling is high enough that the wrap-up does not retrigger the compact.** The margin
above exists for that: a threshold set just under the window makes the summary itself cross
it, which is the warning the cookbook page below gives. **Runs that sample server-side — web
search, server-side extended thinking — are left OUT of the budget** rather than estimated
into it: their cache tokens accumulate across the sampling loop, so what they add is not
this session's conversation growing, and they are measured after the fact instead.

**What does not exist here.** `compaction_control` and `context_token_threshold` are
parameters of the Messages API's tool runner, not of this harness; nothing in Claude Code
reads either, and no rule above may be implemented with them. What crosses over from
https://platform.claude.com/cookbook/tool-use-automatic-context-compaction is the pattern —
threshold, summarise, discard the history — and those two warnings.

## `ESPERANDO-HUMANO`: the state in which the tick turns itself off

When everything left in the package depends on the human, the tick has nothing to dispatch
and every fire still costs a turn. The state is declared in the package ledger by that name, with
the list of what only the human does:

- the OK to merge a pull request;
- a command that has to run on the host, outside this container;
- an edit to live configuration — `~/.claude/settings.json`, the site file, a system cron
  entry, never the tick.

**Entering the state deletes the tick** (*The tick*): nothing is left in flight, so the
orchestrator deletes it (`CronDelete`) and writes the line with the hour read from `date`, as
every ledger line is. Re-arming is a `CronCreate` the session makes itself when it revives on
the human's message.

**A goal-check hook does not live with a goal that reserves the merge to the human.** Such a
goal is unsatisfiable by construction, and the hook rejects the end of every turn. Two exits,
and a package takes one of them before switching on such a hook: the goal declared to it
EXCLUDES what is the human's ("until the pull requests are reviewed and open"), or the hook is
switched off when the ledger enters this state. **The same rejection three times running is the
signal to stop, not to insist.**

**An idle tick costs ONE turn.** Anything above that in a session with nothing to do is a
defect of the harness and not a budget, and `../../bin/tk-context` and `../../bin/tk-quota`
are what make it visible — turns per hour with no change of state.

What it costs where nobody writes this down was measured on the night of 06-07/09: **247 model
turns and 95.1M tokens of cache read in eight hours, with no useful work**, the 5-hour window
going 0→10% and the weekly 86→87%. That burn came mostly from the goal-check Stop hook above
rejecting every turn end; an idle tick fire costs about one turn. One idle turn re-reads the
whole window as cache — ~385k there — so at that size doing nothing costs more than a whole
Sonnet lane every three turns.
