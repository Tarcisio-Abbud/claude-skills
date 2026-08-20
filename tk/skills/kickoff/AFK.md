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

An exclusion naming a class the filter does not recognise — one written in
another language, which queues older than the contract are full of — takes ONE
command: `tk-queue edit <id> --class AUTONOMOUS` reaches the field through the
variants the script already knows (`Classe`, `Esforço`, `Risco`, `Fonte`, …)
and rewrites it in the contract's own name, keeping the item's id, its place in
the order and every other field. What it replaces is the whole class VALUE, so
an annotation riding inside that value goes with it — read the line before
running it on an item whose class carries prose. Reach for `cancel` + `add` only where the field
chain itself cannot be read, and reach knowing the cost: a new id, the place in
the order lost, and any prose past the done-log's title cut gone with it. The
fold the `repairs:` block prints has a limit of its own — it is refused outright
when the item's text carries a field marker inside it.

**Then cut.** Take the eligible in the order printed — priority IS the order of
the file, and `tk-queue bump <id>` is what moves an item to the top — then add
items while the package still fits ONE session: the parent only orchestrates and
verifies, yet each item still costs context to dispatch, monitor and check. Each
candidate line carries its Effort, raw and unsummed. Guidance: stop around 3–6
items or ~2h of summed Effort; leaving an eligible item out beats a session too
long to verify its own work.

Those numbers are an opening bid: step 6 measures what this package actually did, and the
next cut reads that line. The shapes behind them were measured against one 5-hour quota
window (2026-08-18) — a survey ≈5% of the window, one implement + review + fix lane
≈15–20%, a full-method second pair of eyes ≈8%. The audit of step 4 is a fixed cost on the
package rather than a per-item one, and the round it has measured is in that step.
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
writes into ANOTHER project's memory dir whenever that cwd collides with one, and reports
success for it. (With no queue at that path it fails loud instead — the collision is the
dangerous half.) Runs return evidence; the writing happens here.

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

On a wave, the audit of step 4 stands between the claim and the first run: claim and write the
dispatches here, fire them after that step returns.

**Done when:** every package item was claimed — all of them, before the first dispatch — or
reported as held elsewhere, and every dispatched run carries a contract block generated for
that dispatch and a prompt self-sufficient without the tracker.

## 4. Audit the spec and the tickets

A package whose items came from a spec and a ticket set written in this flow — a **wave** — is
audited before any of it is implemented: three adversarial lenses read the two documents, one
verifier tries to refute each finding, and every survivor leaves by one of four outcomes.
There is no code yet, so this reviews none: `/mattpocock-skills:code-review` still runs per
slice, and the conditional second pair of eyes still runs over delivered code.

**It sits between the claim and the first run.** Step 3 claims the whole package and writes
each dispatch; the first run is fired once this step returns, because a REGRILL halts the
package outright and an item whose ticket the audit rewrote has to be dispatched from the
rewritten one.

It runs by **default** on a wave. The orchestrator may skip it for a wave of at most two
tickets that are both Effort S and fully specified — the same test the `implementer` row of
`../../reference/subagent-policy.md` uses to allow a sonnet downgrade — and the skip costs the
block step 6 is owed either way; a wave born
of a REGRILL never skips, however small it is. A package assembled from an aged queue rather
than from a wave has no spec to read and the audit does not apply — which is the line step 6
gets in that case.

### The workflow

Fire the site's **dynamic workflow** from this session — the palette row is in
`../dispatch/SKILL.md` and the site names the concrete mechanism in `~/.claude/tk/dispatch.md`.
That row hands the workflow to the user; the audit is the one package step that fires one
itself, and this instruction is the opt-in that allows it. Running it here rather than inside
a subagent is what keeps the findings where the orchestrator can read them. Where the session
has no such mechanism, run the same graph as Agent-tool dispatches in series. Either way the
prompt carries the ceiling in words — "use at most N agents" — with N no larger than the local
ceiling in the contract block.

Each run takes its row from `../../reference/subagent-policy.md`: `audit-finder` for the
lenses, then `verifier-1`, `verifier-2` and `tiebreak`. The graph, in order:

1. **Three finders in parallel**, one per lens, each reading spec and tickets whole:
   **adversarial** — break what the spec promises, with the tickets as they stand;
   **blast radius** — which ticket touches a path that deletes or corrupts with no copy;
   **contract** — a promise in the spec that no ticket delivers.
   The lenses are fixed by measurement: on 2026-08-14 the grave findings came from lenses
   aimed at breaking a promise, and generic "review this" reading returned none. Two lines are
   fixed in every finder's prompt — **check each acceptance criterion against the decision it
   cites**, which is where the strongest findings of the round measured below came from, and
   **an empty return is a failure, never an approval: finding nothing, list the attacks you
   ran**, which is what makes a lens that found nothing usable as evidence.
2. **Dedup here**, by comparing the three lists; no agent for it. Two lenses arriving at one
   finding by different routes is corroboration, not duplication — record it once and keep
   both routes in its text.
3. **One verifier per finding**, carrying three fixed lines: its mandate is to **refute**, its
   default verdict is *refuted*, and it reads the **real sources** rather than the quotations
   the finding carries. That prompt broke 22% of the finders' findings on that same round.
   It also declares its own **confidence** — `high`, `medium` or `low`, those three words —
   and confidence is the escalation trigger, not severity: a `low` verdict goes to
   `verifier-2`, as does any confirmed finding whose
   correction would edit the spec or a ticket, and the two disagreeing goes to `tiebreak`. There,
   the four low-confidence verdicts were exactly the four the tiebreak decided
   — two of them real, two refuted.
4. A verifier that **writes** — runs the suite, mutates a source — is dispatched with
   `isolation: 'worktree'`, since a shared tree was measured contaminating reviewers of one
   another (2026-08-14).

**One question stays with the orchestrator rather than becoming a fourth lens: can the first
implement session START?** The three lenses read the two documents against each other, and
none of them asks whether the work can begin at all — on that round a code repo holding no
tracker configuration got past all three, and was caught outside the audit. Ask it once of the
wave, by naming what the first ticket's session needs before its first edit: the repo, the
tracker configuration in it, the credentials, the fixture its criterion runs against. A "no"
is a finding like any other and takes one of the four outcomes below — usually **resolve
here**, and **REGRILL** where the spec assumed the missing thing was there.

One round is measured (2026-08-19, run over this package's own spec and tickets): three Sonnet
finders, ≈280k tokens and 10.5 minutes, returned 11 findings with one of them reached by two
lenses; the verifier plus one effort-high tiebreak, ≈152k tokens and 10.6 minutes, confirmed 7
and refuted 2. It found one real REGRILL — a gap that the spec, its quiz and a human approval
had all let through. That is one round and not a distribution, which is why step 6 adds this
package's.

### The four outcomes

Exactly one holds per surviving finding.

| Outcome | Holds when | What it emits |
|---|---|---|
| **Resolve here** | the correction fits inside the spec or the tickets and is unambiguous | the orchestrator edits them directly — editing the spec included, the delta being accepted practice — and records file, field, and what the text said before |
| **Backlog** | the finding is real and correcting it is work of its own | `tk-queue add` at the moment of the verdict, the gate named in the item's own text, exactly as *A session finding, unattended* prescribes below; one only the user can judge is a `DECISION` carrying `--deferred afk` |
| **Refuted** | the verifier broke the finding | one line naming the verifier and how it broke — the finding is gone, and the line is the whole record |
| **REGRILL** | the spec's own premise is what the finding hit | the package halts with no run fired, and the queue takes the decision instead of the work (below) |

Every record in that last column goes into the **audit's block**, which is what this step
hands to step 6: one line per finding under its outcome — what was edited, what was queued,
what was refuted. That block is the only address they have, and a record kept in this step's
own reasoning reaches nobody.

*Refuted* is a verifier's verdict that the finding was never real, which is what separates it
from the **discarding** of the session-finding ladder below: that one is a human judgement an
unattended package does not have, and there a real finding nobody can weigh goes to
**backlog** instead.

### A rotten criterion is routed, not chosen

A ticket whose acceptance criterion measures something other than what the ticket promises
carries a **rotten criterion** — the term and its two shapes, *unsatisfiable by construction*
and *satisfiable but wrong*, belong to `../verify/SKILL.md`. Caught here it is the cheapest
finding of the round: the alternative is an implementer spending three attempts against a
broken ruler and the item ending at a DECISION anyway. It is a distinct object from that
file's **failed 3×** — a rotten criterion never executed against a real delivery at all.

Those two shapes say how the criterion is broken. What routes it here is a different
question — which of the two documents is wrong — and the answer is not a choice among the
four outcomes:

- the spec states the promise plainly and only the criterion misses it → **resolve here**,
  rewriting the criterion to measure the promise, recording both the old text and the new.
  It edits a ticket, so `verifier-2` sees it first;
- the criterion and the spec agree, and together they miss what the work is for → **REGRILL**.
  Nothing ratified is left to measure against, so no rewrite here can be the right one.

A rotten criterion the verifier does not break stays out of **backlog**: a broken ruler left
standing in a ticket is what the next implementer measures itself against.

### REGRILL enters the queue through its gate

```sh
tk-queue add "REGRILL: <the promise the audit could not close> — package halted before the first implement" \
  --class DECISION --deferred afk --effort "M (~40min)" \
  --criterion "B: the user re-grills the promise, and the wave is re-sliced from the spec that grill leaves"
tk-queue handoff <id> --objective "<what the re-grill has to settle>" \
  --state "<the finding, its verifier's verdict, and where the spec and the tickets stand>" \
  --blockers "<what the package stopped holding, and every claim it released>"
```

`--deferred` is the gate: `--class DECISION` is refused without it, so a REGRILL that reached
the queue reached it carrying the record of why nobody could be asked. `../../tests/test_afk_audit.py`
extracts those two commands from this file, runs them against a throwaway queue, and runs the
first again with `--deferred` removed to watch the refusal — it proves the commands and the
gate, and nothing about whether this step ran, which is what the line owed to step 6 is for.

Then release what the package was holding, per step 3, and hand it to step 6: a halted package
still owes its measurement and its close.

**Done when:** the audit ran and every finding it kept carries exactly one of the four
outcomes with the verifier's verdict beside it — or it was skipped, and the judgement that
skipped it is written for step 6.

## 5. Verify every delivery

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
in the PR body or on the item, every claim this package took has either left with its item or
been released, and `tk-queue list` shows exactly the items the run left open — every item it
closed gone from that list, every claim it did not close released — or the queue file itself is
gone, and the report says so instead of a criterion nobody could meet.

## 6. Measure, and hand the package to the close

Three numbers on one line, emitted here, where the package hands back: **planned × completed
× wall clock** — items claimed, items that reached an approved outcome, and the time from
first dispatch to last verdict. They are what stops the cut in step 1 from staying a guess:
this package's line is the next package's evidence. The deviation lines are emitted beside
them, one per departure from the role table, in that file's format — a deviation with no line
is indistinguishable from a slip. The audit hands over its **block** here, whichever way it
went: having run, one line per finding under its outcome plus what the round cost in agents
and wall clock; skipped,
with the judgement that skipped it. Those lines belong to the package and precede the close,
whose own report follows a template this file does not extend.

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
  nobody made. Where that value names a defect in the ITEM rather than a decision about it —
  a field the script cannot read — the reason says so, since "carried" alone reads as a
  deliberate hold and not as a repair waiting;
- an item left out for size is **carried** under the effort gate — cut in step 1, or too big
  to dispatch from here in step 3 — and it carries the ready-to-paste line that runs it:
  another `/tk:kickoff afk` for the cut, and for the one that needed a session of its own,
  the line step 3 already put in the report beside its briefing.

An item verify ended at **proof ready**, and one it turned into a **DECISION**, are carried on
what verify already wrote into them and owe nothing further here: the close is where a
proof-ready item becomes the DECISION that carries its digest reference.

The ladder covers what the package handled. The queue items it never visited are handed over
too, by class — and the classes are not a list to keep by hand: they are every class the step-1
filter refuses, which today is all four that are not AUTONOMOUS. No step of this run looked at
them, and a close shaped only around what the package touched is where they go silent.

**Done when:** the measurement line, the audit's line and the deviation lines are written, and every item the
package did not close carries the first rung that applies to it, and the items it never
visited are handed over by class.

## 7. Chain the afk wrap-up

The package ends by running `../wrap-up/SKILL.md` with its `afk` argument, executed **from
that file**: both skills carry `disable-model-invocation: true`, so an agent cannot fire
`/tk:wrap-up afk` as a command. Reading the file is how the chaining honours that lock
instead of routing around it.

What the close owns from there, and this file therefore does not restate: committing and
pushing before any review is dispatched, the four verdicts of safe-to-merge in their strict
unattended form, which items may merge unattended and which end at an open PR carrying their
proof, and the closing template that step 6's unclosed items enter by their reason.

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

**Done when:** the close carries one line per session finding, each matching an item this run
added to the queue with its gate named — none discarded, none resolved on the spot.
