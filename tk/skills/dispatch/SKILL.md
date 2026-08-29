---
name: dispatch
description: "Dispatch a task to the mechanism that runs it unattended — `/loop`, `/schedule` — delivering the ready-to-paste line. Use when delegating, scheduling or automating work, or when a skill needs the palette."
---

**Dispatching** is matching a task to the mechanism that executes it without the user, and
delivering the ready-to-paste line rather than the mechanism's name. Diagnose the task against
the palette, pick ONE row — the cheaper one when torn — and write the complete command.

**Site extensions:** read `~/.claude/tk/dispatch.md` and `.claude/tk/dispatch.md` if they exist
(README, "Site extensions").

## The palette

| Task situation | Dispatch | Who fires it |
|---|---|---|
| Needs conversation/context from this session | inline, now (plan mode if large) | the agent |
| Verifiable end state (tests green, queue empty, everything compiles) | `/goal`, per the recipe below | the user |
| Agent-ready ticket on the tracker | the site's per-ticket flow (site extensions name it), one ticket per fresh session | the user |
| Queue of autonomous slices with no single termination condition | plain `/loop` over the project's `loop.md` (`LOOP.md` beside this file), one slice per iteration | the agent |
| Big, foggy effort, too big for one session | a charting flow into tickets (site extensions name it), then one map ticket per session | the user |
| Reading legwork against external sources (docs, APIs) | a background research agent leaving a cited markdown file (site extensions may name it) | the user |
| Waiting on external state (CI, third party) | Monitor — a script streaming state, not polling; `/loop` on an interval where no command observes it | the agent |
| Same operation over MANY items (sweep, mass migration) | a dynamic workflow (site extensions name it), piloted on a small slice first | the user |
| Recurring routine rather than a one-off item | `/schedule` (cloud) or local cron, per the recipe below | the agent |
| Context-independent and parallelizable | a background subagent in an isolated worktree | the agent |

"The user" rows are native commands the agent cannot invoke: deliver the ready-to-paste line
with the `/goal` condition or the workflow prompt already written. Where a mechanism is absent
from the session, use its nearest neighbour.

## The two recipes

The `/goal` evaluator reads the conversation and runs no command. Its ready condition carries a
measurable end state, the command proving it ("`npm test` exits 0"), the constraints, and a cap
("stop after 20 turns"). A `/schedule` routine runs with no human and no permission prompt. Write
it self-contained, with the done criterion embedded and a model recommended — the smaller one for
mechanical work.

## Mechanism boundaries

`/loop` dies with the session and expires in 7 days, so a queue that must survive goes to
`/schedule`. A `disable-model-invocation: true` skill (kickoff, wrap-up) is reachable by FILE
only, because the lock holds the command and lets the reading through. Point the scheduled
prompt or the subagent at `skills/wrap-up/SKILL.md` of the `tk` plugin. Take the same route for
every project of a fleet dispatch (`../fleet/SKILL.md`). What no subagent can open is a
**generation** (`../kickoff/WINDOW.md`): a scheduled fire or the user's own first line opens
one. There the dispatch delivers the line the user types, rather than a subagent.

The `next-steps.md` queue (contract: `../kickoff/SKILL.md`) has four dispatchers:

- **interactive kickoff menu** — the user is present and chooses;
- **`/tk:kickoff afk` / `pack`** — one orchestrator plus background subagents, each
  context-isolated (`../kickoff/AFK.md`);
- **`/loop` over `loop.md`** — same-session slices, context accumulating (contract: `LOOP.md`);
- **`/tk:fleet`** — every project's queue on this machine at once, one orchestrator per project
  (`../fleet/SKILL.md`).

**Done when:** the user received ONE mechanism, its why in one sentence, and the complete
ready-to-fire line — or heard the task was inline.
