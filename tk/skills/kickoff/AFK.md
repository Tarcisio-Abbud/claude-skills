# The `afk` and `pack` arguments

Both arguments build the same **package** — the largest set of queue items this session can
run unattended. `afk` fires it with zero interaction: the user typed the command and left.
`pack` shows it once and waits for a single confirmation. Everything else is identical.

The session running a package is an **orchestrator**: it claims, dispatches, verifies and
closes, and implements nothing inline. Every run it dispatches takes its model, effort and
venue from the role table in `../../reference/subagent-policy.md` — which also fixes the
one-line format a departure from that table costs.

## 1. Build the package

`tk-queue pack` (`../../bin/tk-queue`) hands over the candidates: the eligible
items in the queue's own order, and every excluded item with the reason AND the
value that caused it. The filter is the script's — AUTONOMOUS, no Risk, **Env**
absent or naming THIS machine, unclaimed — and the shape it prints is documented
in `tk-queue pack --help`. What it deliberately does not decide is the cut.

**Re-triage before accepting an exclusion.** A Risk the triage finds OBSOLETE (it
names a branch since merged, a migration since run) is cleared on the spot with
`tk-queue edit <id> --risk none`, which is what keeps a stale line from excluding
the item forever; an Env that named a machine the item needed before it was
sliced goes the same way, with `--env none`. An item reported as claimed belongs
to another session — if that session is known to be gone, hand it back with
`tk-queue release <id>`, which prints whose claim it dropped. An item excluded
over a malformed field carries its repair in the `repairs:` block. Re-run
`tk-queue pack` after any of these.

**Then cut.** Take the eligible in the order printed — priority IS the order of
the file, and `tk-queue bump <id>` is what moves an item to the top — then add
items while the package still fits ONE session: the parent only orchestrates and
verifies, yet each item still costs context to dispatch, monitor and check. Each
candidate line carries its Effort, raw and unsummed. Guidance: stop around 3–6
items or ~2h of summed Effort; leaving an eligible item out beats a session too
long to verify its own work.

Those numbers are an opening bid: step 5 measures what this package actually did, and the
next cut reads that line. The shapes behind them were measured against one 5-hour quota
window (2026-08-18) — a survey ≈5% of the window, one implement + review + fix lane
≈15–20%, a full-method second pair of eyes ≈8%.
What multiplies a lane is the number of correction cycles, not the size of the diff —
budgeting a lane by its diff was measured underestimating by ~3× (2026-08-19).

**Done when:** the package lists its items with the summed Effort (e.g. "4 items, ~1h45"),
every exclusion carries either the command that cleared it or the one-line verdict that it
still holds, and every item left out is noted with the reason — the eligible ones dropped for
size AND the ones `tk-queue pack` excluded, which are not eligible at all and would otherwise
leave no trace anywhere.

## 2. `pack` only: confirm

One multiSelect `AskUserQuestion` listing the package items — the summed Effort in the
question, recommended composition stated — so the user unchecks what they don't want and
confirms once. The check IS the authorization. (`afk` skips this step: invoking it IS the
authorization.)
**Done when:** the confirmed package is fixed.

## 3. Claim, then dispatch

### The claim is the first line of the concurrent-session guard

Claim every item of the confirmed package before dispatching the first one:
`tk-queue claim <id> --as <session/host label>`, taken under the exclusive lock the queue
already holds. A second claim is REFUSED, naming the owner and the moment — and that refusal
IS the guard: the item leaves the package untouched and enters the report as held elsewhere.

It leads because the tree signals are blind exactly where the collision happens. A sibling
session working from the shared main tree appears in no `git worktree list` and carries no
`+` in `git branch -v`; on 2026-08-19 one such sibling ran `git pull --ff-only` and landed
the fast-forward on the branch another session had checked out. The tree is the second line
and it is a **defence**, not a check: dispatch every code-editing run into its own worktree,
so a sibling in the shared tree cannot move the ground under it.

A package that dies holding claims leaves them behind — `tk-queue release <id>` hands an item
back without closing it, and prints whose claim it dropped.

### The vehicle, and who writes the queue

The mechanisms are the palette's, in `../dispatch/SKILL.md`; the choice among them here is by
SIZE, and that rule is this step's own. Default: one background subagent per item, in its own
worktree, dispatched **in series**, since items from one queue usually share a repo.
Parallel only across disjoint repos or areas, and never past the local ceiling the contract
block states. An item whose work does not fit one subagent's context is not squeezed into
one: write its briefing with `tk-queue handoff <id>` and dispatch it as a session of its own
— and where this machine cannot open one unattended, the item leaves the package carrying
that briefing, and its ready-to-paste line goes in the report.

**Only the orchestrator writes the queue.** `tk-queue` resolves which queue it is writing
from the cwd, and a run in a worktree has a different one: a subagent calling `done` there
writes into another project's memory dir, or none, and reports success either way. Runs
return evidence; the writing happens here.

### The prompt each run receives

Two parts, both produced here and neither delegated back:

- **The contract block**, pasted verbatim from `../../bin/tk-contract --role <row>`: the
  ceilings, that role's model/effort/venue, and the return contract it owes. The row for a run
  executing a package item is `implementer`; any other run takes the row of the role it is
  dispatched as, and a role the table has no row for is a deliberate choice, logged like any
  other deviation. Generate it per dispatch rather than typing it from memory — a hand-written
  block is a fork of the policy. Pass `--fleet N` only when something else shares this
  machine's ceiling and told you N; alone, the whole ceiling is yours.
- **The item's distilled contract**: the interface the work must honour, its invariants, what
  the neighbouring slices consume from it. You hold the map hot and distilling costs once,
  where re-reading costs per dispatch — a prompt that says "read #X, #Y and #Z" bills that
  price on every run, and was measured starting an implementer at ~150k of context — the edge
  of the smart zone — before its first line of code (2026-08-19). Retransmit the item, the
  memory file behind its `[[slug]]` at ONE hop and its handoff; context in none of the three is a
  **missing handoff**, and the prompt says exactly that in its own line, because a gap named
  is cheap and a gap papered over with plausible synthesis sends the run onto invented ground.

**Count each run by the venue signature it returns, never by the flag you passed** — a
signature that came back local counts against the local ceiling. The measurement behind that
rule is the *Venue* section of that same policy file.

**Done when:** every package item is claimed or reported as held elsewhere, and every
dispatched run carries its generated contract block and a prompt self-sufficient without the
tracker.

## 4. Verify every delivery

The ruler is the item's own criterion and the rite belongs to `../verify/SKILL.md` — read it
before the first item closes. What this step owes that file:

- **The caller re-runs the proof**, here, once, on the final tree — the one measurement, which
  the close then displays rather than repeating. The run's own account of its work is an input
  to it and never a substitute: verify by artifact, not by summary.
- **An empty return is a failed attempt.** A run that comes back with no evidence block did
  not deliver, however confident its prose, and the attempt counts toward the three.
- The three attempts, the four outcomes and the DECISION-plus-handoff a failure writes are
  verify's own; this step supplies the caller they are written for.

An approved item then leaves the queue here — `tk-queue done <id> --how "<pointer>"`, in the
form verify prescribes for carrying the evidence block — and an item verify turned into a
DECISION stays, carrying its handoff.

**Done when:** every package item carries exactly one verify outcome with its evidence block
in the PR body or on the item, and every claim this package took has either left with its
item or been released.

## 5. Measure, and hand the package to the close

Three numbers on one line, emitted here, where the package hands back: **planned × completed
× wall clock** — items claimed, items that reached an approved outcome, and the time from
first dispatch to last verdict. They are what stops the cut in step 1 from staying a guess:
this package's line is the next package's evidence. The deviation lines are emitted beside
them, one per departure from the role table, in that file's format — a deviation with no line
is indistinguishable from a slip. Both belong to the package and precede the close, whose own
report follows a template this file does not extend.

What the items the package did NOT close owe that template is their **reason**, since it
groups by outcome and by nothing else. Read them in order and the first that applies is the
reason — the convention `tk-queue pack` already uses for its own exclusions:

- an item bound to ANOTHER environment is **blocked**, marked "runs on: X": nothing here can
  execute it, and the user is the only path to the machine that can;
- an item another session holds is **carried** under the dependency gate — whose shape here is
  a sibling session holding it — and its reason is the owner and the moment, printed either by
  `tk-queue pack`'s exclusion or by the claim this package was refused;
- an item `tk-queue pack` excluded for anything else is **carried** too, recording the value
  the filter printed: it was never eligible at all, and "left out" alone reads as a size call
  nobody made;
- an item left out for size is **carried** under the effort gate — cut in step 1, or too big
  to dispatch from here in step 3 — and it carries the ready-to-paste line that runs it:
  another `/tk:kickoff afk` for the cut, and for the one that needed a session of its own,
  the line step 3 already put in the report beside its briefing.

An item verify ended at **proof ready**, and one it turned into a **DECISION**, are carried on
what verify already wrote into them and owe nothing further here: the close is where a
proof-ready item becomes the DECISION that carries its digest reference.

**Done when:** the measurement line and the deviation lines are written, and every item the
package did not close carries the reason that lands it in one of the close's groups.

## 6. Chain the afk wrap-up

The package ends by running `../wrap-up/SKILL.md` with its `afk` argument, executed **from
that file**: both skills carry `disable-model-invocation: true`, so an agent cannot fire
`/tk:wrap-up afk` as a command. Reading the file is how the chaining honours that lock
instead of routing around it.

What the close owns from there, and this file therefore does not restate: committing and
pushing before any review is dispatched, the four verdicts of safe-to-merge in their strict
unattended form, which items may merge unattended and which end at an open PR carrying their
proof, and the closing template that step 5's unclosed items enter by their reason.

**Done when:** the wrap-up reached its own "Done when" — or it did not run, and the report
names the step that stopped the package and the state the tree was left in.

## A session finding, unattended

A **session finding** is work this session discovered and did not come for; what separates it
from a pendency is the criterion of the item in hand, and the ladder that triages it lives in
`SKILL.md` beside this file. Unattended, that ladder has exactly one rung left: **queue it
with a gate.** `tk-queue add` at the moment of discovery, the gate named in the item's own
text — human decision · effort · external dependency — and a finding only the user can judge
arrives as a DECISION carrying `--deferred afk`.

The two rungs an unattended session does not have are the two that need a human. **Discarding**
is a judgement ("this will never happen") nobody here can make, so an unattended package
reports no discards. **Resolving on the spot** is the hydra's own fuel: three heads die and
six items are born, which is how a quick job became three weeks. So every finding this package
queued is listed in the close under the gate that kept it, for the user's **veto** on their
return — `tk-queue cancel <id> --why "..."` is that veto, and it is one command against a
finding that would otherwise have been lost to nobody's judgement.
