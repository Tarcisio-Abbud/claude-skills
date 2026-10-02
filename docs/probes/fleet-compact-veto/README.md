# Probe: the compact veto under a fleet

What this probe answers, for `tk/hooks/compact-veto.js` and its `exempt` list:

1. Is the `agentId` on a subagent's `session.compact` the same id the Agent tool returned
   when that subagent was dispatched?
2. Under a fleet's shape, does the veto keep every implementer whole while each project run
   still compacts? The shape is a main session, two background project runs, and one
   implementer inside each run.

`run.sh <work dir>` reproduces question 2, and its data also answers question 1. It spends
quota: one Sonnet main session and four Haiku subagents, each holding about 120k tokens at most.
`analyze.py` summarises a run from the logger's files and the session's transcripts.
`logger/` is a plugin that writes one JSON file per `session.compact`, `agent.spawn` and Agent
tool result.

## 2026-10-02, Claude Code 2.1.287

The compaction window was 100,000 tokens (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`), so the threshold
sat near 80k. The main session ran on Sonnet, and every subagent ran on Haiku 4.5, whose model
window is 200k.

**Identity.** A single foreground subagent was dispatched, read past the threshold, and
compacted. Its `session.compact` carried `agentId` `a76e545d8bcb29caa`. The Agent tool result
named the same id twice: in its structured `agentId` field, and in the text line the model
reads (`agentId: a76e545d8bcb29caa (use SendMessage ...)`). In the fleet run below, a background
dispatch returned `status: async_launched` with the `agentId` at once. Each of those two ids
later appeared on that run's own `session.compact`.

**Fleet of two runs.** The main session wrote the pointer with its own session and both runs'
ids under `exempt`. `$.session.id()` answered that main session's id in every event, nested
implementers included.

| Loop | Role | Compactions the veto skipped | Compactions that ran | `compact_boundary` in transcript | Peak context |
|---|---|---|---|---|---|
| `a5cb3b535d16a5e85` | implementer of run A | 6 | 0 | 0 | 118,322 |
| `a0d59e9f21cee605b` | implementer of run B | 6 | 0 | 0 | 118,367 |
| `a5193d89be250d11e` | project run A (exempt) | 0 | 1 | 1 | 63,417 |
| `a40e89e75327b5cbd` | project run B (exempt) | 0 | 1 | 1 | 63,473 |
| main | fleet orchestrator | none raised | none | 0 | 44,071 |

Peak context is the largest request a loop sent. A project run's peak stays below the threshold
because its compaction ran before the request that would have crossed it (inferred: the engine
decides before each request, on the context it is about to send).

**A first attempt at the same shape failed, and it shows the veto's assumption.** It used files
twice the size, so each implementer had to read about 175k tokens. Vetoed at every request, the
implementers grew past Haiku's 200k window and died with `Prompt is too long`. The project runs
re-dispatched them and thrashed. This is the documented limit in `WINDOW.md`, *Three pieces*:
a subagent kept whole has only the distance between the compaction window and its own model's
window to work in. A subagent on a model whose window is smaller than the parent's is the
case the mod cannot see.
