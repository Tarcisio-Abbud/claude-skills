# Subagent policy — model, effort, venue, PR, checkpoint

The default for every subagent an orchestrator dispatches: which model runs it, at which
reasoning effort, in which **venue** (local × cloud), whether the role authors a pull request
of its own, and whether its work lands in a repository and therefore owes the **checkpoint
invariant**. One role, one row.

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

**Schema** (`schema=3`, declared in the opening marker):

- The rows live between the literal lines `<!-- tk:roles schema=3 -->` and `<!-- /tk:roles -->`.
  A parser reads only what sits between them.
- Inside, every line beginning with `|` is a row, in fixed positions: the first is the
  **header**, the second is the Markdown alignment row (one `---` cell per column) and is
  skipped, and every row after those two is a **data row**, one per role.
- A row is split on `|`; the leading and trailing empty fields from the outer pipes are
  dropped, and each cell is stripped of surrounding whitespace. Cells never contain `|`.
- Columns, in this order: **role**, **model**, **effort**, **venue**, **pr**, **checkpoint**,
  **note**.
  - `role` — the lookup key. Lowercase kebab, stable: renaming one is a breaking change.
  - `model` — `sonnet`, `haiku`, `opus`, or `parent` (the orchestrator's own model; no row uses
    it today — a role that must follow the session's model says so here first).
  - `effort` — `session` (inherits the session's effort) or `high` (pinned, overrides it).
  - `venue` — `local` or `cloud`.
  - `pr` — `opens` when the role's own work lands as a pull request it authors, `none` when
    it does not. It is what decides whether a generated contract block carries the closing
    line below; a role that opens no PR must not be told to write one.
  - `checkpoint` — `required` when the role's work lands in a repository, `none` when it does
    not. It is what decides whether a generated contract block carries the checkpoint
    invariant below. It is deliberately NOT the same question as `pr`: a role can commit into
    a branch another role opens the pull request on, and reading `pr` for this would drop the
    invariant from exactly that role, silently.
  - `note` — prose for the human and the agent; a consumer emits it verbatim, never parses it.
    A role with nothing to add carries `—`.
- A role absent from the table has no default. Choose deliberately and log the choice as a
  deviation.

<!-- tk:roles schema=3 -->
| role | model | effort | venue | pr | checkpoint | note |
|---|---|---|---|---|---|---|
| audit-finder | sonnet | session | local | none | none | Adversarial lens over the work; dispatch one agent per lens. |
| verifier-1 | sonnet | session | local | none | none | Refutes a finding. A finding that would edit a spec or a ticket goes on to verifier-2. |
| verifier-2 | opus | high | local | none | none | Second verdict, for a finding that edits a spec or a ticket. Effort is pinned. |
| tiebreak | opus | high | local | none | none | Settles a split verdict. Effort is pinned. |
| implementer | opus | session | local | opens | required | Downgradable to sonnet on a mechanical, fully specified ticket. Log the downgrade. |
| implementer-spec | opus | session | local | none | required | A package item on a spec's accumulated lane. The orchestrator owns that branch's pull request and writes its body, so this role opens none and hands back its pushed branch. Same downgrade as implementer. |
| fixer | opus | session | local | none | required | Applies a correction cycle's confirmed findings, and resolves a conflict marker the tail's merge of `origin/main` left, with both sides as context. Commits into a branch someone else opened the pull request on; where the correction belongs to one item, `T<id>:` leads the commit title, so the user's revert of that item carries it. No mechanical downgrade: a marker is the one thing here that is never fully specified. |
| research | sonnet | session | cloud | none | none | Rises to opus when the question turns on fine judgement. Log the rise. |
| review | sonnet | session | cloud | none | none | Second pair of eyes; follows the audit-finder row, returning findings for someone else to judge rather than a verdict. Its return is text the orchestrator relays — a cloud agent reaches no tracker of its own. |
| explore | haiku | session | local | none | none | Pure search and file location, no verdict. |
| fleet-orchestrator | opus | session | local | opens | required | One project's whole package, dispatched by the fleet at `--budget 1`. Its wrap-up versioning gate opens that package's pull requests, so the closing line rides with it wherever the item names a tracker ticket. Local by construction: its queue is auto-memory, which no pushed repo carries. |
<!-- /tk:roles -->

## The closing line

A role marked `pr = opens` writes, in the body of the pull request it opens, the literal line

```
Fixes <owner>/<repo>#<n>
```

naming the tracker the ticket lives in and the ticket's own number. Whoever dispatches the
role composes that line with `../bin/tk-ticket-ref <id> --closing-line` and hands it over
finished — the owner half comes from the tracker config of the clone the item's **Repo:**
field names (`--repo <clone>` when it names none), through a shape gate, never from a config
read written into a prompt. `Fixes` is the forge's native keyword, so the merge
itself closes the ticket: the closure becomes a mechanism instead of prose somebody has to
read and act on. It works across repositories when the PR targets its
own repository's default branch and the author can write to the tracker.

**Why the merge is allowed to be the acceptance.** The verification gate runs BEFORE the merge
by construction, so a ticket closed this way was never closed ahead of its proof. The
asymmetry settles the rest: a ticket closed too early reopens with one click, while a ticket
left open too long gets its work done twice.

**The keyword has no undo, and two shapes make it fire at nothing.** A merge later reverted
leaves its ticket closed — reopening is by hand. A reference missing its owner half resolves
against the repository the PR sits on rather than the tracker, and a PR targeting anything
other than its own repository's default branch fires the keyword at nothing at all. Both fail
silently, which is why the wrap-up gate checks the keyword, the number, the owner half, any
OTHER closing line and the base rather than the presence of a line — `../bin/tk-closure-check
<id> --pr <n>` asks the five.

**The tracker may be private, and the line names it anyway.** That is the deliberate cost of
the keyword — the repository's name and the ticket's number become public in the PR body.
Nothing else follows it across: company names, account names and internal content stay out, as
they always were.

## The checkpoint invariant

A role marked `checkpoint = required` commits and pushes at every **seam** of its work — a
north star reached, a suite green, a file finished — and hands nothing back with a dirty tree.
Its orchestrator owes the other half of the same rule: **no review wave is dispatched over
uncommitted work**, so what a lens or a verifier reads is what a later reader can also reach.

**The invariant is about rescue, not tidiness.** An orchestrator verifies by artefact — it
reads the tree and the diff, never the run's account of them — and a later generation of it
starts from git, the queue and a handoff, with the previous generation's context gone. Work
that was never pushed is therefore unreachable by everyone who could act on it, however
complete the return that described it.

**What collects on it is the quota wall.** On 2026-08-18 it landed mid-dispatch and killed
every run then in flight; what survived was exactly what had already been committed and
pushed. The wall arrives without warning, which is why the rule fires at each seam rather than
at the end of the work.

It is **not** enforced by a hook. A hook matches a tool call's arguments and reaches neither a
subagent nor a worktree, and the condition here is an intention about when to stop — so it
lives in the contract block this table generates and in the orchestrator's own normative text.

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
orchestrator assigns. Since 2026-09-02 no row resolves to `parent`, so a session opened on
Fable does not carry its model into a package: implementer, fixer and verdict roles are pinned
to `opus`. One exception, and it holds only with all three locks closed:

1. The question is a **high-level design decision within the agent's own authority** — a verdict
   or a spec decision reserved to the human stays with the human.
2. The consult is **one-shot**: one question, one answer, no tool loop.
3. It is **logged as a deviation**, in the same one-line format as any other.

A second exception is the human's own: `/tk:second-opinion` dispatches a Fable subagent because
the user typed the command — the session choice, made by the person who owns it. Its `consensus`
mode loops, so lock 2 does not hold there; the turn budget is the lock instead. The role has no
row, and the skill writes the deviation line, so the report reads the same either way.
