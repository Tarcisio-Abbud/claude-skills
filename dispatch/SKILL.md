---
name: dispatch
description: "Dispatch a task to the right execution mechanism — /goal, /loop, /implement, Monitor, dynamic workflow, /schedule, /wayfinder, /research or a subagent — delivering the ready-to-paste line. Use when the user wants to delegate, schedule, or automate something and the mechanism is in doubt, or when another skill needs the dispatch palette."
---

**Dispatching** is matching a task to the mechanism that executes it without the user — and
delivering the ready-to-paste line, never just the mechanism's name. Diagnose the task
against the palette, pick ONE line (when torn between two, the cheaper one) and write the
complete command/prompt.

## The palette

| Task situation | Dispatch | Who fires it |
|---|---|---|
| Needs conversation/context from this session | inline, now (plan mode if large) | the agent |
| Verifiable end state (tests green, queue empty, everything compiles) | `/goal` — ready line per the recipe below | the user |
| Agent-ready ticket on the tracker (from `/to-tickets`, `/triage`, or a wayfinder frontier) | `/implement` — one ticket per session, `/clear` between tickets | the user |
| Queue of autonomous slices WITHOUT a single termination condition | plain `/loop` over the project's `loop.md` (contract below), one slice per iteration | the agent |
| Big, foggy effort — the way to the destination isn't visible, too big for one session | `/wayfinder` — chart the map; then one map ticket per session | the user |
| Reading/investigation legwork against external sources (docs, APIs, knowledge bases) | `/research` — background agent leaves a cited markdown file in the repo | the user |
| Waiting on external state (CI, third party) | Monitor — background script streaming the state (no polling); `/loop` with an interval only if there is no observable command | the agent |
| Same operation over MANY items (sweep, mass migration) | dynamic workflow (`ultracode` / "use a workflow") — pilot on a small slice before the full sweep | the user |
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
`disable-model-invocation: true` skill (kickoff, wrap-up), point the prompt at its file
("follow `/root/.claude/skills/wrap-up/SKILL.md`").

Two queues, two dispatchers: the `next-steps.md` queue is dispatched by `/loop` over
`loop.md`; tickets published on the issue tracker are dispatched by `/implement`, one ticket
per fresh session.

## The `loop.md` contract

`.claude/loop.md` at the project root replaces plain `/loop`'s default prompt — it turns
`/loop` (5 keystrokes) into the dispatcher of the `next-steps.md` queue (queue contract in
`/root/.claude/skills/kickoff/SKILL.md`). When dispatching a queue of slices for the first
time in a project, create the file; on later runs, check it still matches the contract:

```markdown
Read the queue at /root/.claude/projects/<cwd-slug>/memory/next-steps.md. Execute ONLY the
top AUTONOMOUS item — one slice per iteration — and verify the result. Update the queue
(resolved items leave). No AUTONOMOUS item left: end the loop and summarize what remains.
```

Edits to `loop.md` take effect on the next iteration; the file belongs to the project
(versionable), the queue stays in auto-memory.

**Done when:** the user received ONE mechanism (with the why in 1 sentence) and the complete
ready-to-fire line/prompt — or the task turned out to be inline and that was said.
