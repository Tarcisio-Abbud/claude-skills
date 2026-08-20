---
name: dispatch
description: "Dispatch a task to the right execution mechanism — /goal, /loop, Monitor, /schedule, a ticket flow or a subagent — delivering the ready-to-paste line. Use when the user wants to delegate, schedule, or automate something and the mechanism is in doubt, or when another skill needs the dispatch palette."
---

**Dispatching** is matching a task to the mechanism that executes it without the user — and
delivering the ready-to-paste line, never just the mechanism's name. Diagnose the task
against the palette, pick ONE line (when torn between two, the cheaper one) and write the
complete command/prompt.

**Site extensions:** read `~/.claude/tk/dispatch.md` and `.claude/tk/dispatch.md` (project
root) if they exist — they name the site's concrete commands for the palette rows marked
"(site extensions name it)".

## The palette

| Task situation | Dispatch | Who fires it |
|---|---|---|
| Needs conversation/context from this session | inline, now (plan mode if large) | the agent |
| Verifiable end state (tests green, queue empty, everything compiles) | `/goal` — ready line per the recipe below | the user |
| Agent-ready ticket on the tracker | the site's per-ticket implementation flow (site extensions name it) — one ticket per fresh session | the user |
| Queue of autonomous slices WITHOUT a single termination condition | plain `/loop` over the project's `loop.md` (contract below), one slice per iteration | the agent |
| Big, foggy effort — the way to the destination isn't visible, too big for one session | a charting flow that maps it into tickets (site extensions name it); then one map ticket per session | the user |
| Reading/investigation legwork against external sources (docs, APIs, knowledge bases) | a background research agent that leaves a cited markdown file in the repo (site extensions may name a command; fallback: a background subagent with that same contract) | the user |
| Waiting on external state (CI, third party) | Monitor — background script streaming the state (no polling); `/loop` with an interval only if there is no observable command | the agent |
| Same operation over MANY items (sweep, mass migration) | dynamic workflow (site extensions name it) — pilot on a small slice before the full sweep | the user |
| Recurring (routine, not a one-off item) | `/schedule` (cloud) or local cron — draft the COMPLETE routine: it runs without a human and without permission prompts, so the prompt is self-contained, with the done criterion embedded and a recommended model (mechanical routine → smaller model) | the agent |
| Context-independent and parallelizable | background subagent (isolated worktree) | the agent |

"The user" dispatches are native commands the agent doesn't invoke: deliver the
ready-to-paste line, with the `/goal` condition or the workflow prompt already written. If a
mechanism doesn't exist in the session, use the nearest neighbour.

## The `/goal` recipe

The evaluator only reads the conversation, it doesn't run commands; the ready condition
carries: a measurable end state, the command that proves it ("`npm test` exits 0"), the
constraints ("without touching other tests") and a cap ("or stop after 20 turns").

## Mechanism boundaries

`/loop` dies with the session and expires in 7 days — a queue that must survive goes to
`/schedule`. Scheduled fires only execute model-invocable skills: to schedule work from a
`disable-model-invocation: true` skill (kickoff, wrap-up), point the prompt at the skill's
file in the plugin's install folder ("follow `skills/wrap-up/SKILL.md` of the `tk`
plugin"). The same lock rules out dispatching such a skill to a subagent: a prompt reading
"run `/implement`" reaches an agent that cannot invoke it, and the run dies there. When a
locked skill must open the work, the user types it as the session's first line, and the
dispatch delivers that line rather than a subagent.

The `next-steps.md` queue (contract: `../kickoff/SKILL.md`, relative to this file) has
three dispatchers, by presence and scope:

- **interactive kickoff menu** — the user is present and chooses;
- **`/tk:kickoff afk` / `pack`** — one-shot package run by an orchestrator + background
  subagents, context-isolated (`../kickoff/AFK.md`);
- **`/loop` over `loop.md`** — same-session slices, context accumulates across iterations.

Tickets published on the issue tracker are dispatched by the site's per-ticket flow, one
ticket per fresh session — the tracker is their source of truth.

## The `loop.md` contract

`.claude/loop.md` at the project root replaces plain `/loop`'s default prompt — it turns
`/loop` (5 keystrokes) into the dispatcher of the `next-steps.md` queue. When dispatching a
queue of slices for the first time in a project, create the file; on later runs, check it
still matches the contract:

```markdown
Read the queue at ~/.claude/projects/<cwd-slug>/memory/next-steps.md. Execute ONLY the
top AUTONOMOUS item — one slice per iteration — and verify the result. Resolve it via
`tk-queue done <id> --how "<pointer>"` (the script is the queue's only writer; contract
in the tk kickoff skill). No AUTONOMOUS item left: end the loop and summarize what remains.
```

Edits to `loop.md` take effect on the next iteration; the file belongs to the project
(versionable), the queue stays in auto-memory.

**Done when:** the user received ONE mechanism (with the why in 1 sentence) and the complete
ready-to-fire line/prompt — or the task turned out to be inline and that was said.
