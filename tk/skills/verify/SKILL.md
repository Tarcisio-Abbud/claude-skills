---
name: verify
description: "Verify a delivery against the item's acceptance criterion, emitting the evidence block. Use when a slice lands, an item is declared done, or a skill needs the acceptance ruler."
---

**Verifying** is running the item's **criterion** against the tree delivered, and emitting
**evidence** someone else can re-run. The criterion is the acceptance line the item was born
with: `A:` a deterministic check, `B:` the user's verdict (contract in `../../reference/queue.md`).
It is read-only here: a ruler bent to fit the delivery measures nothing, and one that has to
change belongs to the user.

**Site extensions:** read `~/.claude/tk/verify.md` and `.claude/tk/verify.md` if they exist
(README, "Site extensions").

## Two positions

| Position | What runs | What it produces |
|---|---|---|
| **North star** — after each slice | criterion A of the ITEM, whole | observational: expected to fail until the last slice, and logged rather than acted on. One exception: a slice that makes it **regress** — stopped executing, or stopped passing what already passed — is redone on the spot |
| **Hard gate** — last slice delivered | criterion A of the item, on the final tree | exactly one outcome below |

One run yields one of three results: **passes** · **fails** · **does not execute**.

## The proof fits the promise

A criterion A proves what the item promised, in the promise's own currency. A behaviour promise
→ the behaviour exercised. An **equivalence** promise (a refactor, a port, a rewrite) → an
equivalence artefact. That is output byte-compared against real data, or dumps compared on a
copy of the real database. A green suite there proves the suite still runs, which is not what
the item promised.

The fixture carries the same weight as the currency. Run the criterion against the shape the
data really has, not the smallest one the wording accepts. When the item's subject has a real
population — a queue with tagged items, a file with prior content — that population is the
fixture.

## The anchor outlives the tree

**A criterion anchors on content, never on a line number or an absolute count** — a reformat
moves the line, a sibling slice moves the count. Anchor by a grep of the sentence. Write an
unavoidable count paired with the sha of the tree it ran on, the shape
`../wrap-up/MERGE-GATE.md` gives a green suite. A criterion passed only because a reflow
refilled its line, and two lane tickets named a count their lane had already passed.

## Prove it can fail

The first time a criterion A is run at all, prove once that it **can** fail: put the defect back
and watch it fall.

## Outcomes of the hard gate

Exactly one holds, and the fit check in *The proof fits the promise* runs FIRST. A criterion
that fails it is **rotten** whatever its exit code. Fewer than three failed attempts is a retry
rather than an outcome.

| Outcome | Holds when | What it emits |
|---|---|---|
| **Approved** | a type-A criterion that fits the promise executed and passed on the final tree, re-run by the caller. | the evidence block; the item can close. Merging stays the caller's decision |
| **Proof ready** | type B, criterion fitting the promise: the artefact plus a one-line claim ("this proves X"). | the evidence block with the artefact attached. The verdict is the user's, so a **type-B item never merges inside an unattended package**. That package ends at an open PR carrying the proof, and waits |
| **Failed 3×** | the criterion fits the promise and executes, and three attempts fail to satisfy it — for type B, the artefact could not be produced. | the item becomes a DECISION carrying its attempt history, and leaves the package |
| **Rotten criterion** | the criterion cannot execute, or executes and proves something other than what the item promised. | a DECISION naming the contradiction and proposing the criterion that carries the same guarantee; the delivered code is left as it stands |

## A rotten criterion has two shapes

- **Unsatisfiable by construction** — no delivery could pass it. Say so **in writing before
  doing the work**: name the contradiction and the criterion that would carry the same
  guarantee.
- **Satisfiable but wrong** — it passes while measuring something else (the AST where the
  promise was behaviour; the suite where the promise was equivalence). Same outcome, same
  remedy.

Both are honest outcomes and count as a finished run.

## Three attempts, then the queue

The ceiling of three applies at the hard gate. Attempt 1 fails → fix the delivery and rerun;
same for attempt 2. On the third failure the item leaves the package as a DECISION, by the
three-step `tk-queue` sequence in `HANDOFF.md`.

## The item points at the briefing

Every caller of `tk-queue handoff` owes this step, whatever brought it there. The script warns
on stderr, **at exit 0**, that the item carries no `[[handoff-T00N]]`. It prints the `tk-queue
edit` that repairs the link, quoted for the shell. **Run the `edit` it
prints.** That pointer is the briefing's only discovery path.

## The caller re-runs it

The evidence that carries a merge verdict is the criterion re-run **by the caller** — the
orchestrator of a package, or the session accepting the work. It runs once, on the final tree,
after the last slice and before the wrap-up. The implementer's report is an input to that run,
never a substitute for it.

## The evidence block

Lives in the **body of the PR**. A session with no PR puts it on the item as it closes:
`tk-queue done <id> --how "<pointer>" --note "<the block>" --force`. That `--force` raises the
field ceiling without removing it. Either way the block is written once, here: a wrap-up digest,
a reviewer or the next session reads and displays it rather than re-deriving it.

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

A criterion A already in the shape of the target repo's suite is **promoted**: commit it as an
acceptance test named `acceptance_*`. Add one line to that repo's `CODING_STANDARDS.md`, or
wherever it documents its standards — "every delivered item carries its acceptance test;
`acceptance_*` tests only get stronger". A criterion outside suite shape stays ephemeral,
living in the evidence block.

**Done when:** exactly one outcome above is named for the item, and its evidence block sits in
the PR body or the item's `--note`. A 3× failure or a rotten criterion also has its DECISION in
the queue, with its handoff.
