# Subagent policy — model, effort, venue

The default for every subagent an orchestrator dispatches: which model runs it, at which
reasoning effort, and in which **venue** (local × cloud). One role, one row.

The policy is **hybrid**. The table below is the default, and the orchestrator may deviate in
any direction — it is the one holding the case in front of it. Every deviation costs one
line, written where the orchestrator hands the run back to the human, so the reader sees the
choice next to its reason:

```
role: default→used — reason
```

A deviation with no line is the failure this format exists to prevent: the reader cannot tell
a judgement from a slip.

## Role table

The table is the single source for these values: the agent reads the rows as they stand, and a
generator that injects them into a subagent's contract block parses these same cells verbatim.
A consumer that copies the values into itself has forked the policy — read them from here.

**Schema** (`schema=1`, declared in the opening marker):

- The rows live between the literal lines `<!-- tk:roles schema=1 -->` and `<!-- /tk:roles -->`.
  A parser reads only what sits between them.
- Inside, every line beginning with `|` is a row, in fixed positions: the first is the
  **header**, the second is the Markdown alignment row (one `---` cell per column) and is
  skipped, and every row after those two is a **data row**, one per role.
- A row is split on `|`; the leading and trailing empty fields from the outer pipes are
  dropped, and each cell is stripped of surrounding whitespace. Cells never contain `|`.
- Columns, in this order: **role**, **model**, **effort**, **venue**, **note**.
  - `role` — the lookup key. Lowercase kebab, stable: renaming one is a breaking change.
  - `model` — `sonnet`, `haiku`, or `parent` (the orchestrator's own model).
  - `effort` — `session` (inherits the session's effort) or `high` (pinned, overrides it).
  - `venue` — `local` or `cloud`.
  - `note` — prose for the human and the agent; a consumer emits it verbatim, never parses it.
    A role with nothing to add carries `—`.
- A role absent from the table has no default. Choose deliberately and log the choice as a
  deviation.

<!-- tk:roles schema=1 -->
| role | model | effort | venue | note |
|---|---|---|---|---|
| audit-finder | sonnet | session | local | Adversarial lens over the work; dispatch one agent per lens. |
| verifier-1 | sonnet | session | local | Refutes a finding. A finding that would edit a spec or a ticket goes on to verifier-2. |
| verifier-2 | parent | high | local | Second verdict, for a finding that edits a spec or a ticket. Effort is pinned. |
| tiebreak | parent | high | local | Settles a split verdict. Effort is pinned. |
| implementer | parent | session | local | Downgradable to sonnet on a mechanical, fully specified ticket. Log the downgrade. |
| research | sonnet | session | cloud | Rises to parent when the question turns on fine judgement. Log the rise. |
| review | sonnet | session | cloud | Second pair of eyes; follows the audit-finder row, returning findings for someone else to judge rather than a verdict. Its return is text the orchestrator relays — a cloud agent reaches no tracker of its own. |
| explore | haiku | session | local | Pure search and file location, no verdict. |
<!-- /tk:roles -->

## Effort inherits the session

An omitted `effort` inherits the **session's** effort — not the model's own default, and never a
floor of the harness's choosing. A session opened at low effort therefore runs every `session`
row at low effort, which is why the two verdict roles pin `high`: a verdict is the one place
where the session's setting must not decide the depth.

## Venue

**Venue restricts the role**, orthogonally to whatever restricts the item.

The mechanism is a subagent dispatched with `isolation: remote`: the orchestrator keeps the
thread and receives the return with no polling. An independent cloud session is a different
object and sits outside this contract — it cannot answer back.

**Eligibility, the hard test:** a role runs in cloud only when its **proof fits in the pushed
repo** — no gitignored data, no local state, no interactively authenticated integration. The
rows marked `cloud` above are the ones measured to pass it; every other role stays local until a
measurement moves it, and moving one is a change to this file, not a judgement call at dispatch
time.

**Cloud buys RAM, not quota.** A cloud run relieves the local memory ceiling and burns the same
rolling usage window as a local one. Treat the two ceilings as separate numbers — concurrent
local subagents, concurrent remotes — and quota as one accounting across both.

**Every return carries a venue signature.** `isolation: remote` has been measured degrading
**silently** to local execution: the run reported success while the filesystem and the memory it
touched were the local ones. So each subagent reports the signature of where it actually ran
(the working directory it resolved, plus a marker the remote sandbox would not share), the
orchestrator reads that signature rather than the flag it passed, and **a degraded run counts
against the local ceiling**. Counting it anywhere else lets the local ceiling leak through
remotes that never left the machine.

## Fable is a session choice

Fable stays out of the table: it is the model a human picks for their own session, not a tier an
orchestrator assigns. One exception, and it holds only with all three locks closed:

1. The question is a **high-level design decision within the agent's own authority** — a verdict
   or a spec decision reserved to the human stays with the human.
2. The consult is **one-shot**: one question, one answer, no tool loop.
3. It is **logged as a deviation**, in the same one-line format as any other.
