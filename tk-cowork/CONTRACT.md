# Contract — `next-steps.md`

One queue per project, at the project folder's root, holding **open items only**.

```markdown
# Próximos passos — <projeto>

- **T003** · DECISION · Effort M — Enviar a proposta revisada ao cliente
  - **Critério:** e-mail enviado com o PDF final anexado
  - **Contexto:** 04-Regras e Documentação/proposta-v3.md

## Concluídos
- 2026-08-04 · T002 — Planilha de conciliação entregue (04-Financeiro/conciliacao.xlsx)
```

**ID** — `T001…`, sequential per project. An ID stays with its item forever, so read the
Concluídos section before assigning the next one.

**Class** — exactly one per item:

| Class | Criterion |
|---|---|
| `AUTONOMOUS` | well specified; an agent executes it alone |
| `DECISION` | missing a user choice; once decided, becomes AUTONOMOUS |
| `BLOCKED` | needs data, access or an action only the user has |
| `EXTERNAL` | waiting on a third party; at most chase or remind |
| `RECURRING` | not a one-off — should become a routine |

**Effort** — `P` (minutes) · `M` (a session) · `G` (more than one session).

**Critério** — required: the observable fact that closes the item. "Pronto" describes a
feeling; "e-mail enviado com o PDF anexado" describes a fact.

**Size** — an item is a pending action in two lines. Durable context lives in a project
document, reached from the Contexto line.

**Leaving the queue** — a resolved item moves to `## Concluídos` with the date and what
resolved it, in the same edit that resolves it.

**One writer** — this file and the project's shared state documents have exactly one writer
per batch of work: the session holding the conversation. Subagents execute their item and
**report back what changed**; they never edit the queue or a shared document. Two
read-modify-write cycles on the same file lose the first one silently — the second agent
starts from a copy taken before the first wrote, and its save restores that copy. A
subagent may own a whole document only when it is the sole writer of that file in the batch.

**Confirming a write** — a tool returning success proves a write happened, not which base
version it used, and a subagent reporting success proves even less. Confirm by reading the
file back through a path that does not pass through the session's staging cache — where a
device shell exists, that is reading the mount directly — and match a string that could
only exist if this edit landed: an exact figure, an ID, a phrase just written. A grep for a
generic word finds it elsewhere in the file and confirms nothing.

**Legacy queue** — a project may carry an older file (`PROXIMOS-PASSOS.md`, or one buried
in a subfolder). Adopt it once: merge into `next-steps.md` at the root, delete the old
file, and say so.
