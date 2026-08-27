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

The wall announces itself twice — a dispatched run comes back a **terminal failure**, and the
error text names the moment the window resets. Both matter. A run the wall killed delivered
nothing and refuted nothing, so it is **not** one of the three attempts `../verify/SKILL.md`
counts: charge it to the item and the wall spends an item's whole budget on a fact about the
clock.

On the first quota failure, in this order:

1. **Stop dispatching.** The runs in flight are already dead; the ones not yet sent stay
   unsent.
2. **Refresh one handoff** — `tk-queue handoff "<id>" --objective "..." --state "..."
   --blockers "..."`, in the form `../verify/SKILL.md` prescribes. The id is the item in
   flight; with nothing in flight, it is the head of what the package has left. One handoff,
   not one per item: the package's remaining state has a single home, and a copy per item is a
   copy to go stale.
3. **Say what is left, in `--state`:** the items still to dispatch, in order; the item in
   flight and the branch its work is pushed to; the reset time the error named; and the claims
   this package holds.
4. **Keep the claims.** They are how the next generation knows which items are its own, and
   releasing them here invites a sibling session to take work that is half done. This is the
   one place the release rule of `AFK.md` step 3 does not apply.
5. **Stop.** Report the wall, the reset time and the handoff's path.

**Done when:** the tree is pushed, one handoff carries the four contents of step 3, the claims
are intact, and the report names the reset time.

## After the reset, the package finishes and stops

A resumed package runs out the items it already claimed and ends there. The queue waits for
the next kickoff, which is the user's.

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

The rule, at every seam — an item closed, the wall, the end of the package:

- **Refresh the handoff.** Always, whatever the context reads.
- **Above ~150–200k of context**, open the next generation and end this one. The number is
  visible in the statusline and is calibrated by what each package reports.
- **Below it**, carry on.

Generations are **sequential**: one orchestrator at a time, so the single-writer rule over the
queue survives, and the claims pass to the successor inside the handoff. One package, one live
orchestrator.

**Write the handoff rather than compacting.** An auto-compacted orchestrator carries a machine
summary of a long context; a fresh one carries a briefing its predecessor wrote on purpose,
against a contract, with the queue and git behind it. The second is strictly better, and
writing it is already step 2 of the wall.
