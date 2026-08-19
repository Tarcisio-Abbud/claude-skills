---
name: verify
description: "Runs the item's own acceptance criterion as the ruler of the delivery — north star after each slice, hard gate at the end, and the evidence block the next reader re-runs. Use when a session declares an item done, when an implementer or an orchestrator closes an unattended slice, or when another skill needs the acceptance ruler."
---

**Verifying** is running the item's **criterion** — the acceptance line the item was born
with (`A:` a deterministic check, `B:` the user's verdict; contract in
`../kickoff/SKILL.md`) — against the tree actually delivered, and emitting **evidence**
someone else can re-run. The criterion is read-only here: it is the ruler, and a ruler bent
to fit the delivery measures nothing. A criterion that has to change belongs to the user.

## Two positions

| Position | What runs | What it produces |
|---|---|---|
| **North star** — after each slice | criterion A of the ITEM, whole | observational: it is expected to fail until the last slice, and the result is logged, not acted on. One exception: a slice that makes it **regress** — stopped executing, or stopped passing what already passed — is redone on the spot |
| **Hard gate** — last slice delivered | criterion A of the item, on the final tree | exactly one outcome below |

One run yields one of three results: **passes** · **fails** · **does not execute**. At the
hard gate those results resolve into outcomes; before it, they are only logged.

## The proof fits the promise

A criterion A proves what the item promised, in the promise's own currency. A behaviour
promise → the behaviour exercised. An **equivalence** promise (a refactor, a port, a
rewrite) → an equivalence artefact: output byte-compared against real data, a differential
fuzz across the two implementations, dumps compared on a copy of the real database. A green
suite there proves the suite still runs, which is not what the item promised.

## Outcomes of the hard gate

Exactly one holds. Type A and type B split the items; within A, the three cases partition
every run. Fewer than three failed attempts is not an outcome — it is a retry.

| Outcome | Holds when | What it emits |
|---|---|---|
| **Approved** | a type-A criterion executed and passed on the final tree, re-run by the caller | the evidence block; the item can close and the PR can be merged |
| **Proof ready** | type B: the artefact plus a one-line claim ("this proves X") is assembled | the evidence block with the artefact attached. The verdict is the user's, so a **type-B item never merges inside an unattended package** — the package ends at an open PR carrying the proof |
| **Failed 3×** | a type-A criterion executed and failed on three attempts | the item becomes a DECISION carrying its attempt history, and leaves the package |
| **Rotten criterion** | the criterion cannot execute, or executes and proves something other than what the item promised | a DECISION naming the contradiction and proposing the criterion that carries the same guarantee; the delivered code is left as it stands |

## A rotten criterion has two shapes

- **Unsatisfiable by construction** — no delivery could pass it. Say so **in writing before
  doing the work**, not after: name the contradiction and the criterion that would carry the
  same guarantee. Work done against a broken premise is work to throw away.
- **Satisfiable but wrong** — it passes while measuring something else (the AST where the
  promise was behaviour; the suite where the promise was equivalence). Same outcome, same
  remedy.

Both are honest outcomes and count as a finished run. The one thing that reaches the user is
what was **measured**, which is why the criterion travels intact: an implementer that
rewrites the ruler to make it pass returns a self-attestation, and the gate stops meaning
anything from that item on.

## Three attempts, then the queue

The ceiling of three applies at the hard gate. Attempt 1 fails → fix the delivery and rerun;
same for attempt 2. On the third failure, in this order:

1. `tk-queue edit <id> --class DECISION --deferred "<why the decision could not be asked>"`
   (an unattended session passes `--deferred afk`), plus `tk-queue release <id>` when the
   item was claimed, so the dead package's ownership does not outlive it.
2. Write the handoff beside the queue files (`handoff-<id>.md`, same directory the
   `tk-queue` resolves for `next-steps.md`) and point the item at `[[handoff-<id>]]`. It
   carries the destination, the state, and the **attempt history**: per attempt, what
   changed, the command, the exit code and the tail of the output. The history lives there
   rather than in the item because the item is capped at 700 chars.
3. The branch and the PR stay exactly as they are. The next session starts from the handoff.

## The caller re-runs it

The evidence that carries a merge verdict is the criterion re-run **by the caller** — the
orchestrator of a package, or the session accepting the work — once, on the final tree,
after the last slice and before the wrap-up. The implementer's report is an input to that
run, never a substitute for it. A subagent that returns with no evidence block did not pass:
an empty return is a failure that reads as success.

## The evidence block

Lives in the **body of the PR**; a session with no PR puts it in `tk-queue done <id>
--note "..."`. The wrap-up's digest reads it and displays it — it is written once, here.

```
### Verify — <item id>
Criterion: <the criterion as written on the item>
Command:   <the literal command run>
Exit code: <n>
Output:    <last lines, enough to recognise the run>
Attempts:  <n> of 3
When:      <ISO timestamp>
```

Type B adds the artefact and its one-line claim in the same block.

## Promoting the criterion to a test

A criterion A already in the shape of the target repo's suite is **promoted**: commit it as
an acceptance test named `acceptance_*`, and add one line to that repo's
`CODING_STANDARDS.md` — "every delivered item carries its acceptance test; `acceptance_*`
tests only get stronger". From then on the Standards axis of any code review watches it for
free. A criterion that is not in suite shape stays ephemeral, living in the evidence block.

On the first promotion of a criterion, prove once that it **can fail**: put the defect back
and watch the test fall. A test that passes with the defect back protects nothing.

**Done when:** exactly one outcome above is named for the item, its evidence block sits in
the PR body (or the item's `--note`), and — for a 3× failure or a rotten criterion — the
DECISION is already in the queue with its handoff.
